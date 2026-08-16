# Role-Based Access Control Specification

The main decisions are recorded in
[ADR 0001](./adr/0001-authorization-pattern.md) and
[ADR 0002](./adr/0002-bootstrap-admin-safety.md).

## Authorization model

The application has three roles. Backend dependencies are the security boundary;
the frontend consumes the permissions returned by `GET /api/v1/users/me` only to
present the correct navigation, controls, and access-denied state.

| Action | Admin | Manager | Member |
|---|:---:|:---:|:---:|
| List all users | Yes | Yes | No |
| Create users and assign roles | Yes | No | No |
| View, update, or delete another user | Yes | No | No |
| View metrics | Yes | Yes | No |
| View and update own profile | Yes | Yes | Yes |
| Manage own items | Yes | Yes | Yes |
| Manage another user's items | Yes | No | No |

Roles are stored as constrained strings: `admin`, `manager`, and `member`.
Permissions are defined once in the backend role-permission map and checked by
reusable FastAPI dependencies. Ownership checks remain explicit in resource
handlers. Role changes therefore take effect on the next request without waiting
for a JWT to expire.

## Administrator bootstrap

A fresh database is bootstrapped with these deployment secrets:

```env
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD=<secure-temporary-password>
```

Startup applies migrations first. If an active administrator already exists,
bootstrap does nothing and does not require the secrets. Otherwise it creates
exactly one administrator whose password must be replaced. It never promotes an
existing non-admin account, resets an existing password, or recreates demo users.

If administrator accounts exist but all are inactive, startup fails safely. Recover
access through an interactive operator command:

```bash
docker compose run --rm backend \
  python scripts/recover_admin.py --email admin@example.com
```

Recovery refuses to run while an active administrator exists and never accepts a
password as a command-line argument.

After the administrator replaces the temporary password, the temporary secret may
be removed. If the database is later recreated, bootstrap credentials must be
provided again.

Bootstrap is not permanently tied to the configured email. An administrator may
change their email normally; their role and account ID remain intact, and startup
detects the existing admin before consulting bootstrap settings. Login then uses
the new email. Only recreating the database causes the currently configured
bootstrap email to be used again.

## Required password replacement

Bootstrap and administrator-created accounts have `must_change_password=true`.
They may authenticate, inspect `/users/me`, and replace their password, but all
other authenticated endpoints return `403` until replacement succeeds. The
password hash and flag are updated in one transaction.

Public signup and completed password recovery do not require another replacement.
Assigning a new temporary password administratively restores the requirement.

The frontend sends affected users to `/change-password` after login and on page
refresh. A `401` clears authentication; an authorization `403` does not.

Invalid, expired, or unknown-user bearer tokens return `401` with a Bearer
challenge. Valid but inactive users, forced-password users, ownership failures,
and missing permissions return `403`.

## Administrator safety invariants

- Administrators cannot delete, demote, or deactivate themselves.
- The final active administrator cannot be deleted, demoted, or deactivated.
- Administrator-affecting mutations and recovery are serialized so concurrent
  requests cannot remove every active administrator.
- The frontend hides self-management actions, and the backend independently
  enforces every invariant.
- Public signup always creates a member and cannot accept an elevated role.

## Database transition

The transition migration converts existing administrator flags to `admin`, maps
other accounts to `member`, adds `must_change_password=false` for established
accounts, and drops the former flag. Historical migrations remain unchanged so
existing installations can upgrade normally; the running application contains no
compatibility field or alias.

## Performance

- Permission resolution is an in-memory lookup with constant bounded cost.
- Authentication already loads the user by primary key, so database-backed roles
  add no query to ordinary authenticated requests.
- The advisory lock and indexed active-admin count run only during startup,
  recovery, deletion, or role and activation changes.
- Concurrent administrator lifecycle changes serialize briefly by design.

## Security and observability

- The backend is authoritative; frontend visibility checks grant no access.
- JWTs omit roles, preventing elevated claims from remaining valid after a role
  change.
- Signup cannot assign an elevated role, and ownership checks prevent IDOR-style
  access to another user's resources.
- Temporary and recovery passwords are hashed and never logged. Recovery does not
  accept a password in command arguments.
- API `403` responses log the method and normalized route. Logs exclude tokens,
  bodies, query strings, passwords, and email addresses.
- Direct database writers and compromised deployment secrets remain outside the
  application security boundary.

## Support cost

The local policy map avoids another dependency, service, policy datastore, and
failure mode. Its maintenance cost is updating typed permissions, protected routes,
generated frontend types, and focused tests together. PostgreSQL advisory locking
adds database-specific recovery and concurrency tests. Adopt a policy engine only
if policies become tenant-defined, attribute-based, or shared across services.

## Failure behavior

| Case | Result |
|---|---|
| Administrator changes email | Account ID, role, and current JWT remain valid; future login uses the new email. |
| Bootstrap values change or disappear | Existing active administrator is untouched. |
| Bootstrap email belongs to a non-admin | Startup fails without promotion. |
| Only inactive administrators exist | Startup fails with the explicit recovery command. |
| Two instances bootstrap concurrently | The shared lock permits one creation. |
| Two admins concurrently remove each other | The operation that would leave zero active admins fails. |
| Recovery races with a new active admin | Recovery rechecks under the lock and refuses. |
| Database mutation fails | The safety check and mutation roll back together. |

## Deferred enhancements

Email invitations, external policy engines, architecture diagrams, audit-event
storage, and tenant-specific policies are deliberately outside the test-task
scope. The permission layer can be replaced by a policy engine later without
changing route contracts.

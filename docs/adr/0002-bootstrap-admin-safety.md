# ADR 0002: Bootstrap and Active-Administrator Safety

- Status: Accepted
- Date: 2026-08-16
- Specification: [Role-Based Access Control](../rbac.md)

## Context

A fresh database needs one administrator without retaining legacy first-user
runtime behavior. Temporary credentials must not become permanent credentials,
changing the administrator's email must not create another account, and supported
concurrent operations must not remove every active administrator.

## Options

1. Recreate or reset the configured email on every startup.
2. Automatically reactivate an administrator when none is active.
3. Bootstrap only an empty administrator set and provide explicit recovery.

## Decision

Use option 3. Startup detects administrators by role and activity rather than
configured email. If an active administrator exists, startup changes nothing. If
no administrator exists, bootstrap credentials create one active account with
`must_change_password=true`. If only inactive administrators exist, startup fails
and directs an operator to the interactive recovery command.

Bootstrap, recovery, role changes, activation changes, and deletion share one
PostgreSQL transaction-level advisory lock. After acquiring it, the application
rechecks active administrators and commits the safety check and mutation in the
same transaction.

```text
+-------------------+
| Acquire admin lock|
+---------+---------+
          |
          v
+-------------------+   yes   +------------------+
| Active admin?     |-------->| Continue safely  |
+---------+---------+         +------------------+
          | no
          v
+-------------------+   yes   +------------------+
| Inactive admin?   |-------->| Explicit recovery|
+---------+---------+         +------------------+
          | no
          v
  Bootstrap temporary admin
```

## Consequences

An administrator may change email without affecting startup or current JWTs.
Administrators cannot delete, demote, or deactivate themselves, and concurrent
supported operations cannot remove the final active administrator. The indexed
active-admin query and lock run only on rare lifecycle operations, not ordinary
requests.

The solution is PostgreSQL-specific and adds recovery and concurrency tests.
Operators must protect bootstrap secrets, remove them after first use where
practical, and restrict the recovery command. Direct database writers can still
bypass application invariants and remain an operational security boundary.

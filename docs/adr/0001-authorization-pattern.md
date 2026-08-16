# ADR 0001: Backend-Owned Authorization Policy

- Status: Accepted
- Date: 2026-08-16
- Specification: [Role-Based Access Control](../rbac.md)

## Context

The application needs three roles with a small, stable permission surface. The
authorization model must be easy to find, consistent across routes, immediately
reflect role changes, and understandable without learning a policy language.
Frontend checks must improve usability without becoming a security boundary.

## Options

1. Keep a binary superuser flag and add route-specific role conditions.
2. Store roles in JWTs and check them in middleware.
3. Add an external policy engine such as Casbin.
4. Use a typed in-process role-permission map with FastAPI dependencies.

## Decision

Use option 4. Users store one constrained role: `admin`, `manager`, or `member`.
A typed backend map expands roles into permissions. Reusable FastAPI dependencies
enforce those permissions, while resource handlers perform explicit ownership
checks where required.

JWTs contain only the user ID. Each request loads the current database record, so
role changes and deactivation take effect immediately. `GET /api/v1/users/me`
returns the resolved permissions for frontend navigation, controls, and friendly
Access Denied pages.

```text
+---------+    +-----------+    +------------+    +-----------+
| JWT ID  | -> | Load user | -> | Permission | -> | Ownership |
+---------+    +-----------+    +------------+    +-----------+
                                      |
                                      v
                              Allow or return 403
```

## Consequences

The policy is local, typed, fast, and easy to test. Adding a permission normally
changes the policy map and the protected route; generated client types expose it
to the frontend. Database-backed role resolution adds no query beyond the existing
current-user lookup.

The frontend and backend share permission names but not enforcement code. The
design is intentionally less flexible than a policy engine. Revisit this decision
if policies become tenant-defined, attribute-based, dynamically editable, or
shared by multiple services.

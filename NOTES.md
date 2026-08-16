# Submission Notes

## Delivered

- Backend-enforced `admin`, `manager`, and `member` permissions.
- Permission-aware navigation, controls, and direct-route Access Denied states.
- User and active-user metrics stub.
- PostgreSQL migrations, focused authorization tests, and disposable Docker test
  workflows.
- Concise ADRs for authorization and bootstrap-administrator safety.

## Deliberate Extra Scope

The assignment permits a simpler first-user setup. At the request of the reviewer,
the implementation removes the legacy superuser runtime model, forces replacement
of bootstrap and administrator-issued temporary passwords, prevents self-removal,
and serializes last-active-admin changes with a PostgreSQL advisory lock.

These additions increase migration and operational test surface, but keep ordinary
request authorization simple: one database user lookup and an in-memory permission
map.

## Tradeoffs and Future Work

No external policy engine was added because three fixed roles do not justify a new
policy language, datastore, or service. Reconsider that decision if policies become
tenant-defined, attribute-based, or shared across services. Persistent security
audit storage is also deferred; denied API requests currently produce privacy-safe
structured application logs.

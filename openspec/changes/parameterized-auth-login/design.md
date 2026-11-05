# Design

## Context

See [proposal.md](proposal.md) for the motivation and [specs/auth-login/spec.md](specs/auth-login/spec.md) for the observable requirements. The issue is limited to `auth/` and `POST /auth/login`.

`AuthResource.login` validates the request, delegates credential lookup to `LegacyDatabase.findByCredentials`, returns `401` when no user is found, and creates a token only after a match. The lookup currently builds a SQLite query by concatenating both credential values and executes it through JDBC `Statement`. The existing `AuthResourceTest` is a Quarkus/RestAssured test and covers the seeded `student` login, but not manipulated credentials. `docs/ENDPOINTS.md` does not define the auth endpoint; the protected success behavior is therefore anchored in the issue and the existing test, as stated in the proposal.

## Goals / Non-Goals

**Goals:**
- Ensure credential values are treated as data during lookup and cannot change its conditions.
- Preserve the `POST /auth/login` path, request format, successful `200` response, `user.username`, and token issuance for valid credentials.
- Preserve the current `401` behavior for rejected credentials and ensure rejected attempts do not receive a token.
- Keep the change and its tests within `auth/`.

**Non-Goals:**
- Change token format or lifetime, response serialization, validation of missing fields, or other login behavior.
- Introduce a new persistence abstraction, database schema, dependency, or migration.
- Modify `api/`, `web/`, or their sections in general documentation.

## Protected Contracts

- `POST /auth/login` continues to accept the current JSON request and preserves the successful response behavior for `student` / `Workshop123!`: HTTP `200`, `user.username` equal to `student`, and a non-null `token`.
- Requests rejected as invalid credentials continue to receive HTTP `401`; they must not contain a token.
- The authentication endpoint and response construction remain unchanged by this design. In particular, token creation remains conditional on a successful credential lookup.
- The issue's rejection behavior intentionally changes the current vulnerable result for SQL-shaped credentials; this is the only externally observable behavior change in scope.

## Affected Components

- `auth/`: credential lookup in `LegacyDatabase` and endpoint-level characterization/security tests in `AuthResourceTest`.
- No changes are planned to `api/`, `web/`, shared endpoint documentation, database schema, or runtime configuration.

## Decisions

1. **Bind both credential values in the existing JDBC lookup.** Keep the current query shape and replace value concatenation with positional parameters using `PreparedStatement`. This directly prevents either input from changing the query while preserving the database and lookup boundary. Escaping or filtering special characters was rejected because it is easy to get wrong and can reject legitimate credentials. Moving to an ORM or broader repository redesign was rejected as disproportionate to this issue.
2. **Leave endpoint response handling and token behavior unchanged.** The current resource already maps a missing match to `401` and only creates a token for a returned user. Fixing the lookup at its data boundary avoids a second, divergent validation rule in the HTTP layer. Adding input-pattern checks in `AuthResource` was rejected because it would couple SQL syntax to the API and would not secure other callers of the lookup.
3. **Use the existing test stack and seeded test user.** Extend the Quarkus/RestAssured coverage without adding dependencies or real secrets. Keep the existing successful-login characterization as the compatibility guard.

## Incremental Strategy

1. Run the existing auth test from `auth/` to establish the valid-login baseline before changing credential lookup.
2. Add endpoint-level tests for the issue's injection-shaped value in `username` and `password`, asserting `401` and no token. Run them before changing the lookup to demonstrate the vulnerable behavior and retain them as regression tests.
3. Change only the JDBC credential lookup to bind both supplied values. Do not alter request validation, response construction, token generation, schema, or configuration.
4. Run the complete auth test suite and JaCoCo verification from `auth/`; keep coverage of modified code at or above the repository's 85% target. Review that the API and response contract remain unchanged.

## Characterization and Verification

- The existing `logsInWithWorkshopUser` test characterizes the success status, username, and token for the seeded workshop account. Keep it passing before and after the lookup change.
- Before changing lookup behavior, add separate tests for the issue-provided value in the username and password fields. Each test must assert HTTP `401` and that the response has no token; no assertion should depend on internal SQL or implementation classes.
- After the change, run `mvn test` and the configured JaCoCo verification in `auth/`. No test or implementation changes are required in other components.

## Risks / Trade-offs

- **[Risk] A parameter binding or ordering error could reject valid users.** → Keep the existing valid-login characterization and exercise both credential positions in the negative tests.
- **[Risk] The existing persistence method catches database exceptions and returns no user, which the endpoint reports as `401`.** → Preserve this behavior in this issue; changing error semantics is outside the approved contract.
- **[Trade-off] The issue-specific tests cover the supplied SQL-shaped input rather than every possible injection string.** → The parameter-binding decision protects the whole input boundary, while the tests cover both independently supplied credential values and the documented acceptance case.
- **[Risk] The auth endpoint is absent from `docs/ENDPOINTS.md`.** → Do not edit that general document in this change; use the issue and the existing endpoint test as the baseline, and preserve the gap explicitly in the proposal.

## Rollback

No schema, data, configuration, or dependency migration is introduced. If the change causes an auth regression, revert the corresponding `auth/` lookup and test changes together; the prior endpoint and database contract remains available without a migration rollback. Do not roll back unrelated components or general documentation.
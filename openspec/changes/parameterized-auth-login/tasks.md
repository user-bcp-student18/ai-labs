# Tasks

## 1. Characterize the login behavior

- [x] 1.1 Run `mvn -Dtest=AuthResourceTest test` from `auth/` and confirm the existing workshop login returns HTTP `200`, `user.username` `student`, and a non-null token.
- [ ] 1.2 Add endpoint tests for `' OR '1'='1` in the username and password fields; run `mvn -Dtest=AuthResourceTest test` before changing credential lookup and confirm both reproduce the issue by returning a token instead of the expected `401` without a token.

## 2. Correct credential lookup

- [x] 2.1 Parameterize both credential values in the existing auth lookup without changing endpoint response handling; run `mvn -Dtest=AuthResourceTest test` from `auth/` and confirm the valid login passes while both injection cases return `401` without a token.

## 3. Validate the auth change

- [x] 3.1 Run `mvn test` from `auth/` and confirm the complete auth test suite passes.
- [x] 3.2 Run `mvn verify` from `auth/`, inspect the JaCoCo report, and confirm coverage of modified code meets the repository's 85% target.
- [x] 3.3 Review the final diff from the repository root and confirm changes are limited to the approved `auth/` lookup and tests, with no changes to `api/`, `web/`, or general documentation and no change to the login contract.
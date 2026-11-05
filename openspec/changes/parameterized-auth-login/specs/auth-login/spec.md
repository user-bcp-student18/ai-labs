# Spec Delta

## Purpose

Define el comportamiento observable del inicio de sesión para preservar el acceso válido y evitar autenticaciones con credenciales manipuladas.

## ADDED Requirements

### Requirement: Valid credentials preserve the login response
The login endpoint SHALL preserve the successful response for valid credentials.

#### Scenario: Workshop user logs in successfully
- **WHEN** the client submits username `student` and password `Workshop123!` to `POST /auth/login`
- **THEN** the response status is `200`, `user.username` is `student`, and `token` is present and non-null

### Requirement: Manipulated credentials cannot authenticate
The login endpoint SHALL reject credentials that attempt to alter the credential lookup and SHALL NOT return an authentication token.

#### Scenario: Injection-shaped username is rejected
- **WHEN** the client submits username `' OR '1'='1` to `POST /auth/login`
- **THEN** the response status is `401` and no `token` is returned

#### Scenario: Injection-shaped password is rejected
- **WHEN** the client submits password `' OR '1'='1` to `POST /auth/login`
- **THEN** the response status is `401` and no `token` is returned
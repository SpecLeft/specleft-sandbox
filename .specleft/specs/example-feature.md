# Feature: Example Feature

## Scenarios

### Scenario: User logs in successfully
priority: high

- Given a registered user with email "user@example.com"
- When the user submits valid credentials
- Then the user is redirected to the dashboard
- And the user sees a welcome message

### Scenario: Invalid password rejected
priority: medium

- Given a registered user with email "user@example.com"
- When the user submits an incorrect password
- Then an error message "Invalid credentials" is displayed
- And the user remains on the login page

---
confidence: low
source: example
assumptions:
  - email/password authentication
  - session-based login
open_questions:
  - password complexity requirements?
  - maximum login attempts before lockout?
tags:
  - auth
  - example
owner: dev-team
component: identity
---

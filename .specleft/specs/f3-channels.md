# F3 — Channels

## Scenarios

### Scenario: Reject invalid webhook config
priority: high

- Given a rule payload with a webhook channel missing url
- When I POST to /rules
- Then I receive 422

### Scenario: Reject invalid email config
priority: high

- Given a rule payload with an email channel missing to
- When I POST to /rules
- Then I receive 422

### Scenario: One channel failure does not block others
priority: high

- Given a rule with a failing webhook channel and a log channel
- When the rule fires
- Then the log channel dispatches successfully
- And a DispatchRecord with status "failed" exists for the webhook

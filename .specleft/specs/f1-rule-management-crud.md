# F1 — Rule Management (CRUD)

## Scenarios

### Scenario: Create a valid rule
priority: high

- Given a rule payload with one condition and one log channel
- When I POST to /rules
- Then I receive 201 with the created rule and its id

### Scenario: Reject duplicate rule name
priority: high

- Given an existing rule named "alert-on-signup"
- When I POST a new rule with name "alert-on-signup"
- Then I receive 409 Conflict

### Scenario: Rule creation rejected without a channel
priority: high

- Given a rule payload with one condition and no channels
- When I POST to /rules
- Then I receive 422

### Scenario: Rule creation rejected without a condition
priority: high

- Given a rule payload with no conditions and one log channel
- When I POST to /rules
- Then I receive 422

### Scenario: List rules
priority: medium

- Given two existing rules
- When I GET /rules
- Then I receive 200 with both rules

### Scenario: Get rule by id
priority: medium

- Given an existing rule
- When I GET /rules/{id}
- Then I receive 200 with the rule

### Scenario: Update rule fields
priority: medium

- Given an existing rule
- When I PATCH /rules/{id} with a new name and is_active false
- Then I receive 200 with the updated rule

### Scenario: Delete cascades to conditions and channels
priority: high

- Given an existing rule with two conditions and one channel
- When I DELETE the rule
- Then the conditions and channel are also removed

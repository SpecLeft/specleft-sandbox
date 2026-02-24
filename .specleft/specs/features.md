# Feature: Notification Rules Engine

## Scenarios

### Scenario: Create a valid rule
priority: medium

- Given a rule payload with one condition and one log channel
- When I POST to /rules
- Then I receive 201 with the created rule and its id

### Scenario: Reject duplicate rule name
priority: medium

- Given an existing rule named "alert-on-signup"
- When I POST a new rule with name "alert-on-signup"
- Then I receive 409 Conflict

### Scenario: Rule creation rejected without a channel
priority: medium

- Given a rule payload with one condition and no channels
- When I POST to /rules
- Then I receive 422

### Scenario: Delete cascades to conditions and channels
priority: medium

- Given an existing rule with two conditions and one channel
- When I DELETE the rule
- Then the conditions and channel are also removed

### Scenario: Rule fires when all conditions match
priority: medium

- Given a rule with event_type "user.created" and condition user.role eq "admin"
- When I POST an event {"type": "user.created", "payload": {"user": {"role": "admin"}}}
- Then the rule is triggered and a DispatchRecord with status "sent" is created

### Scenario: Rule does not fire when a condition fails
priority: medium

- Given the same rule
- When I POST an event with payload {"user": {"role": "member"}}
- Then no DispatchRecord is created for that rule

### Scenario: Inactive rule is skipped
priority: medium

- Given a deactivated rule matching the event type
- When I POST a matching event
- Then the rule is not triggered

### Scenario: Event response is non-blocking
priority: medium

- Given a rule with a slow webhook channel
- When I POST a matching event
- Then the response returns 202 before the webhook completes

### Scenario: One channel failure does not block others
priority: medium

- Given a rule with a failing webhook channel and a log channel
- When the rule fires
- Then the log channel dispatches successfully
- And a DispatchRecord with status "failed" exists for the webhook

### Scenario: Records returned newest first
priority: medium

- Given two events that triggered the same rule at different times
- When I GET /dispatch-records?rule_id={id}
- Then the more recent record appears first

### Scenario: Get all rules
priority: medium

- Given I have created multiple rules
- When I GET /rules
- Then I receive all rules

### Scenario: Get a specific rule
priority: medium

- Given an existing rule
- When I GET /rules/{id}
- Then I receive the rule details

### Scenario: Update a rule
priority: medium

- Given an existing rule
- When I PATCH /rules/{id} with updated data
- Then I receive the updated rule

# F4 — Event Publishing

## Scenarios

### Scenario: Rule fires when all conditions match
priority: high

- Given a rule with event_type "user.created" and condition user.role eq "admin"
- When I POST an event {"type": "user.created", "payload": {"user": {"role": "admin"}}}
- Then the rule is triggered and a DispatchRecord with status "sent" is created

### Scenario: Rule does not fire when a condition fails
priority: high

- Given the same rule
- When I POST an event with payload {"user": {"role": "member"}}
- Then no DispatchRecord is created for that rule

### Scenario: Inactive rule is skipped
priority: high

- Given a deactivated rule matching the event type
- When I POST a matching event
- Then the rule is not triggered

### Scenario: Event response is non-blocking
priority: medium

- Given a rule with a slow webhook channel
- When I POST a matching event
- Then the response returns 202 before the webhook completes

### Scenario: Only matching event_type rules evaluated
priority: medium

- Given a rule listening for event_type "order.created"
- When I POST an event with type "user.created"
- Then the rule is not triggered

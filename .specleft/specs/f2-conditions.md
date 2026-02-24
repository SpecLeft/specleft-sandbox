# F2 — Conditions

## Scenarios

### Scenario: Reject unknown operator
priority: high

- Given a rule payload with a condition using operator "between"
- When I POST to /rules
- Then I receive 422

### Scenario: Missing field path evaluates false
priority: high

- Given a rule with condition "user.role" eq "admin"
- When I POST an event with payload missing "user.role"
- Then the rule is not triggered

### Scenario: gt on non-numeric evaluates false
priority: high

- Given a rule with condition "user.role" gt "5"
- When I POST an event with payload {"user": {"role": "admin"}}
- Then the rule is not triggered

# F5 — Dispatch Records

## Scenarios

### Scenario: Records returned newest first
priority: high

- Given two events that triggered the same rule at different times
- When I GET /dispatch-records?rule_id={id}
- Then the more recent record appears first

# PRD: Notification Rules Engine API

**Version:** 1.0  
**Stack:** FastAPI · Python 3.12 · SQLite (via SQLAlchemy) · Pytest

---

## Overview

A REST API that allows users to define conditional notification rules. When an event is published, the engine evaluates all active rules against the event payload and dispatches notifications to each rule's configured channel(s).

## Project Goals

- All features have sufficient test coverage proving functionality
- Edge cases and error handling are explicitly covered (invalid inputs, missing data, failure states)
- Implementation is clean, readable, and follows established design principles

---

## API Surface

```
POST   /rules
GET    /rules
GET    /rules/{id}
PATCH  /rules/{id}
DELETE /rules/{id}

POST   /events

GET    /dispatch-records?rule_id={id}
```

---

## Features

### F1 — Rule Management (CRUD)

A **Rule** has:

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | Auto-generated |
| `name` | string | Unique |
| `is_active` | bool | Default `true` |
| `event_type` | string | The event kind this rule listens for |
| `conditions` | list[Condition] | See F2 |
| `channels` | list[Channel] | See F3 |

**Behaviours:**
- Creating a rule with a duplicate `name` returns `409 Conflict`
- A rule must have at least one condition and one channel; violation returns `422`
- Deleting a rule cascades to its conditions and channels

---

### F2 — Conditions

Each condition is a predicate on the event payload. A rule fires only when **all** conditions pass.

A **Condition** has:

| Field | Type | Notes |
|---|---|---|
| `field` | string | Dot-notation path into payload, e.g. `user.role` |
| `operator` | enum | `eq`, `neq`, `gt`, `lt`, `contains` |
| `value` | string | Coerced to field type at evaluation time |

**Behaviours:**
- An unknown `operator` returns `422` on rule creation
- A `field` path that resolves to nothing evaluates as `false` (no error)
- `gt` / `lt` on non-numeric fields evaluate as `false`

---

### F3 — Channels

Each channel defines a dispatch target when its parent rule fires.

Supported types: `webhook`, `email`, `log`

A **Channel** has:

| Field | Type | Notes |
|---|---|---|
| `type` | enum | `webhook` \| `email` \| `log` |
| `config` | dict | Type-specific (see below) |

Config requirements:
- `webhook`: must include a valid `url`
- `email`: must include a valid `to` address
- `log`: no config required (no-op, useful for testing)

**Behaviours:**
- Invalid or missing config for `webhook`/`email` returns `422` on rule creation
- Dispatch is fire-and-forget; a failure on one channel does not block others
- Each dispatch attempt produces a **DispatchRecord** (see F5)

---

### F4 — Event Publishing

`POST /events` triggers rule evaluation against active rules.

An **Event** has:

| Field | Type | Notes |
|---|---|---|
| `type` | string | Matched against `Rule.event_type` |
| `payload` | object | Arbitrary JSON |

**Behaviours:**
- Only rules where `is_active = true` and `event_type` matches are evaluated
- Rules are evaluated concurrently
- A rule with no conditions always fires (vacuous truth)
- Returns `202 Accepted` with the list of triggered rule names; does not wait for dispatch to complete

---

### F5 — Dispatch Records

Every channel dispatch attempt is recorded.

A **DispatchRecord** has:

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | Auto-generated |
| `rule_id` | uuid | Foreign key |
| `channel_type` | string | |
| `status` | enum | `sent` \| `failed` |
| `error_message` | string \| null | Populated on failure |
| `dispatched_at` | datetime | |

**Behaviours:**
- `GET /dispatch-records?rule_id={id}` returns all records for a rule ordered by `dispatched_at` descending
- Records are immutable once written

---

## Out of Scope (v1)

- Authentication / multi-tenancy
- Real email or webhook delivery (stub/mock in tests)
- Retry logic
- OR logic across conditions
- Pagination

---

## Acceptance Scenarios (Gherkin)

```gherkin
Feature: Rule lifecycle

  Scenario: Create a valid rule
    Given a rule payload with one condition and one log channel
    When I POST to /rules
    Then I receive 201 with the created rule and its id

  Scenario: Reject duplicate rule name
    Given an existing rule named "alert-on-signup"
    When I POST a new rule with name "alert-on-signup"
    Then I receive 409 Conflict

  Scenario: Rule creation rejected without a channel
    Given a rule payload with one condition and no channels
    When I POST to /rules
    Then I receive 422

  Scenario: Delete cascades to conditions and channels
    Given an existing rule with two conditions and one channel
    When I DELETE the rule
    Then the conditions and channel are also removed

Feature: Event evaluation

  Scenario: Rule fires when all conditions match
    Given a rule with event_type "user.created" and condition user.role eq "admin"
    When I POST an event {"type": "user.created", "payload": {"user": {"role": "admin"}}}
    Then the rule is triggered and a DispatchRecord with status "sent" is created

  Scenario: Rule does not fire when a condition fails
    Given the same rule
    When I POST an event with payload {"user": {"role": "member"}}
    Then no DispatchRecord is created for that rule

  Scenario: Inactive rule is skipped
    Given a deactivated rule matching the event type
    When I POST a matching event
    Then the rule is not triggered

  Scenario: Event response is non-blocking
    Given a rule with a slow webhook channel
    When I POST a matching event
    Then the response returns 202 before the webhook completes

Feature: Channel dispatch

  Scenario: One channel failure does not block others
    Given a rule with a failing webhook channel and a log channel
    When the rule fires
    Then the log channel dispatches successfully
    And a DispatchRecord with status "failed" exists for the webhook

Feature: Dispatch records

  Scenario: Records returned newest first
    Given two events that triggered the same rule at different times
    When I GET /dispatch-records?rule_id={id}
    Then the more recent record appears first
```
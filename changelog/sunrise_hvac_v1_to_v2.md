# Change Log: sunrise_hvac v1 -> v2

| Field | Old Value | New Value |
|---|---|---|
| `business_hours.days` | `[]` | `['monday','tuesday','wednesday','thursday','friday']` |
| `business_hours.start` | `` | `7:00 AM` |
| `business_hours.end` | `` | `6:00 PM` |
| `business_hours.timezone` | `` | `CST` |
| `office_address` | `` | `2450 West Lake St, Chicago, IL 60612` |
| `emergency_routing_rules.primary_contacts` | `['(312) 555-0101']` | `['(312) 555-0101','(312) 555-0102']` |
| `call_transfer_rules.timeout_seconds` | `null` | `60` |
| `call_transfer_rules.retries` | `null` | `2` |
| `integration_constraints` | `[]` | `['Do not auto-create emergency jobs in ServiceTrade without human confirmation.']` |
| `questions_or_unknowns` | `[...]` | `[]` |

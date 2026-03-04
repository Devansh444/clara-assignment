# Change Log: acme_fire v1 -> v2

| Field | Old Value | New Value |
|---|---|---|
| `business_hours.start` | `8:00 AM` | `7:30 AM` |
| `business_hours.end` | `5:00 PM` | `6:00 PM` |
| `emergency_definition` | `['Emergency examples include sprinkler leak, alarm triggered, active fire panel trouble', 'For emergency calls transfer to dispatcher at (201) 555-0111 then on-call tech at 201-555-0112']` | `['Emergency examples include sprinkler leak, alarm triggered, active fire panel trouble', 'For emergency calls transfer to dispatcher at (201) 555-0111 then on-call tech at 201-555-0112', 'After-hours non-emergency extinguisher requests can be collected for next business day follow-up', 'All emergency sprinkler calls must go directly to the phone tree number (201) 555-0199 first']` |
| `emergency_routing_rules.primary_contacts` | `['(201) 555-0111', '201-555-0112']` | `['(201) 555-0111', '201-555-0112', '(201) 555-0199']` |
| `call_transfer_rules.timeout_seconds` | `45` | `60` |
| `integration_constraints` | `['Never create sprinkler jobs in ServiceTrade automatically']` | `['Never create sprinkler jobs in ServiceTrade automatically', 'Do not create sprinkler jobs in ServiceTrade']` |
| `questions_or_unknowns` | `[]` | `['call_transfer_rules retries not specified']` |
| `version` | `v1` | `v2` |
| `last_updated_utc` | `2026-03-04T10:56:49.706995+00:00` | `2026-03-04T10:56:49.738242+00:00` |

Notes:
- Only explicitly extracted onboarding data is applied.
- Empty onboarding values do not overwrite existing values.

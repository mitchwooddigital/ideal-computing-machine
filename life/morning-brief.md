# Morning brief

A daily 7am (Brisbane) Slack DM that pulls from Shopify, Xero, Gmail and
Google Calendar and posts a short brief. Runs as a Claude Code routine,
not as code in this repo. This file is the spec so it can be tweaked and
the routine prompt updated to match.

## Design rules

- Under 20 lines. If it needs scrolling it gets ignored.
- Only flag things that need action. At most three fires.
- Zero manual data entry. Everything is pulled.
- Countdowns and plain comparisons, not raw dates and tables.
- No em dashes.

## Sections

1. **Sales**: yesterday vs same weekday last week, plus bank balance.
2. **Fires**: fulfilment backlog older than 2 days, unread email older than
   24h, payables overdue over 3 months, sales down more than a third.
3. **Calendar**: today's events, tomorrow's first.
4. **Today's three**: echoes whatever Mitch replied with in the DM the day
   before. Capped at three.

## Data sources

| Source | Call | Note |
|---|---|---|
| Shopify sales | `run-analytics-query`, `FROM sales SHOW orders, total_sales TIMESERIES day SINCE -8d UNTIL today` | |
| Shopify backlog | `graphql_query` with `ordersCount` | `list-orders` is blocked for privacy, counts only |
| Xero | `get_cash_position`, `get_aged_payables` | payables response is huge, read summary fields only |
| Gmail | `search_threads`, `in:inbox is:unread older_than:1d newer_than:7d -category:promotions -category:social` | `{}` means zero |
| Calendar | `list_events`, today to end of tomorrow, `Australia/Brisbane` | |

## Schedule

Cron `0 21 * * *` UTC, which is 7:00am AEST every day. Delivered to
Mitch's own Slack DM.

The routine fires back into the Claude Code session that created it,
because fresh sessions spawned by a routine don't inherit the Slack,
Shopify, Xero, Gmail and Calendar connectors. If that session is ever
archived, recreate the routine from the claude.ai routines UI with those
connectors attached and paste the prompt from this file's sections.

## Ideas not built yet

- Real task list (Slack canvas or a small Neon table) instead of DM replies.
- Klaviyo: next scheduled campaign and days until send.
- Meta Ads: spend this week vs last.
- Semrush: keywords that dropped out of the top 10.
- Content queue: products with empty descriptions.
- A single-screen dashboard once a week of briefs shows what gets looked at.

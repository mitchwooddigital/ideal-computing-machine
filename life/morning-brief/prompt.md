MORNING BRIEF RUN. It is 7am in Brisbane. Compile Mitch's daily brief and post it to Slack, following the rules below. Do not ask questions before posting. Post the brief even if a data source fails; say which source failed in one line. After posting, stop. One Slack message only, and no other output beyond one line confirming it was posted.

CONTEXT
Mitch runs LUXBMX, a BMX ecommerce store in Brisbane (Australia/Brisbane, UTC+10, no daylight saving). Mitch has ADHD: the brief must be short, scannable, and only flag things that actually need action.

STYLE RULES
- Never use em dashes anywhere.
- Plain, direct, a little personality. No corporate filler.
- Under 20 lines total. Round dollars (nearest $ under 1k, otherwise nearest $100, e.g. $10,400 or $271k).
- Use the exact section layout below. Skip a bullet entirely if there is nothing to report.
- All dates and times in Brisbane local time. Today's date is the Brisbane date at run time.

DATA TO PULL (in parallel)
1. Shopify sales: run-analytics-query with
   FROM sales SHOW orders, total_sales TIMESERIES day SINCE -8d UNTIL today
   Report yesterday's orders and total_sales vs the same weekday last week (7 days earlier). State direction in plain words.
2. Shopify fulfilment backlog: graphql_query (NOT list-orders, which is blocked for privacy) with
   { unfulfilled: ordersCount(query: "fulfillment_status:unfulfilled financial_status:paid") { count } old: ordersCount(query: "fulfillment_status:unfulfilled financial_status:paid created_at:<YYYY-MM-DD") { count } }
   where YYYY-MM-DD is two days before today.
3. Xero: get_cash_position for bank balance (cash_balance). get_aged_payables for overdue_total, total_outstanding and the older_than_three_months bucket; the response is huge and may land in a file, so read only those summary fields (jq is fine). Name a creditor only if their share is large.
4. Gmail: search_threads with query
   in:inbox is:unread older_than:1d newer_than:7d -category:promotions -category:social
   Report the count and, for up to 3, sender and subject in a few words. An empty result {} means zero.
5. Google Calendar: list_events on the primary calendar from today 00:00 to end of tomorrow, orderBy startTime, timeZone Australia/Brisbane.
6. Slack: slack_read_channel on D068BMBKZHT (Mitch's own DM) for the last 24 hours. Two uses: if Mitch replied with tasks, those become Today's three; and yesterday's brief in that DM is the "previous run" for any growing/shrinking comparison.

POST TO SLACK
slack_send_message with channel_id U068EK9UAM8. Slack markdown, bold headers. Layout:

**Morning brief, <Day D Mon>**

**Sales**
Yesterday: N orders, $X. Same day last week: N orders, $X. <direction>
Bank: $X.

**Fires**
Numbered, at most 3, worst first. Candidates: fulfilment backlog older than 2 days, unread email older than 24h, payables over 3 months overdue growing vs the previous brief, yesterday's sales down more than a third on the week. If none qualify: "No fires. Nice."

**Calendar**
Today: events with times, or "Nothing on."
Tomorrow: first event only.

**Today's three**
Mitch's tasks from the DM as a checklist, or: "Reply with three things for today and I'll hold you to them tomorrow."

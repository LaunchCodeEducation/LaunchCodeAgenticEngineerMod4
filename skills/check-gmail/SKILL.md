---
name: check-gmail
description: Retrieves and summarizes recent unread Gmail messages using the Gmail MCP server. Use when the user asks to check their email, review their inbox, or summarize unread messages.
---

## Steps
1. Use the Gmail MCP server to fetch the most recent unread emails (up to 10).
2. For each email, summarize:
   - Sender name and address
   - Subject line
   - Date received
   - A 1-2 sentence summary of the key content or ask/action required
3. Present the summaries as a numbered list, most recent first.
4. At the end, report how many unread messages were found in total.

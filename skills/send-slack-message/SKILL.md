---
name: send-slack-message
description: Sends a message to a Slack channel using the Slack MCP server. Use when the user asks to post an update, notify a channel, or share a message in Slack.
---

## Steps
1. Ask the user for the channel name and message text if not already provided.
2. Call the Slack MCP tool to post the message to the specified channel.
3. Confirm to the user that the message was sent, including the channel name.

## Troubleshooting
If the Slack MCP server is not available, explain that the SLACK_BOT_TOKEN and SLACK_TEAM_ID environment variables may not be set and suggest the user restart the container with those values.

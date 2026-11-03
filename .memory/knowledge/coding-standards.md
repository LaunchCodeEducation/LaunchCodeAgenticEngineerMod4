# Coding Standards

Last reviewed: 2026-09-15
Maintained by: Hector

These standards apply to all code in this project. The agent should consult this file before writing or reviewing any code. These rules are set by humans and the agent should never modify this file.

## TypeScript
Use TypeScript for application code and prefer explicit types when they improve clarity. Avoid unnecessary use of `any`.

## Reusable Backend Logic
Keep backend business logic reusable across clients. API and backend functionality should not depend on the React web frontend because MarketRadar is intended to support a future iOS/mobile client.

## Secrets
Never hardcode credentials, tokens, cookies, database URLs, or other secrets. Sensitive configuration must come from environment variables.

## Input Validation
Validate external and user-provided input before using or storing it, especially search parameters, scraped data, and API request data.

## Descriptive Naming
Use clear, descriptive names for variables, functions, routes, and database fields. Avoid abbreviations that make code harder to understand.

## Error Handling
Handle errors explicitly. API failures should return useful, consistent error responses without exposing sensitive implementation details.

## Focused Responsibilities
Keep functions and modules focused on a clear responsibility. Extract reusable logic when a file begins handling unrelated concerns.

## Preserve Historical Data
Preserve historical data when the product depends on changes over time. Do not overwrite historical records when doing so would remove information needed for tracking or analysis.

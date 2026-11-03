# 2.2 Exercise 1 - Pre-Session Plan

## Real Project Task

Review the MarketRadar codebase and identify the highest-priority code-quality improvements that would make the project easier to maintain and continue developing.

## Agent

I will use a code-quality reviewer agent. The agent will inspect the project, identify code-quality issues, prioritize them, and revise its recommendations when project requirements change.

## Phase 1 - Initial Review

The agent will review the current MarketRadar codebase and identify important code-quality issues.

Requirements:
- Focus on the existing tracker-client and tracker-api code.
- Prioritize issues that affect maintainability and future development.
- Do not make code changes.
- Produce a prioritized list of recommendations.

## Phase 2 - Revised Priorities

After Phase 1, I will introduce a new requirement:

MarketRadar is planned to eventually support an iOS/mobile client, so the backend API should be prioritized over frontend cleanup when deciding which improvements provide the most value.

The agent will revisit its Phase 1 recommendations and update the priorities using this new requirement.

## Requirement Change

The requirement change will happen between Phase 1 and Phase 2.

The original review considers the entire project equally. In Phase 2, backend/API maintainability becomes the higher priority because the API may eventually support both web and mobile clients.

## Artifact to Revisit

The agent will revisit the prioritized code-quality recommendations created during Phase 1.

## Evidence

I will evaluate the session using:
- the Phase 1 recommendations;
- the saved session summary;
- the revised Phase 2 recommendations;
- whether the agent remembers the original project facts;
- whether it correctly applies the new backend/API priority;
- whether the final recommendations are consistent with the newest requirements.

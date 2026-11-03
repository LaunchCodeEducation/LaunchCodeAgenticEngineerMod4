# 2.2 Exercise 1 - Context-Management Technique Plan

## Explicit Context Boundary

I will use an explicit context boundary after Phase 1 is complete and before Phase 2 begins.

At the boundary, I will tell the agent:
- Phase 1 is complete.
- Phase 2 will revisit the code-quality recommendations.
- The original maintainability requirements still apply.
- A new requirement now prioritizes backend/API improvements because MarketRadar may eventually support an iOS/mobile client.
- The Phase 1 recommendations still matter and must be revisited instead of starting the review over.

I chose this boundary because this is the point where the goal changes from creating the initial recommendations to revising them using a new project requirement.

## Proactive Summarization

After introducing the requirement change and before asking the agent to revise its recommendations, I will ask the agent to summarize the current session state.

The summary should preserve:
- the current goal;
- the MarketRadar project facts discovered during Phase 1;
- the original requirements;
- the new backend/API priority;
- decisions and recommendations made so far;
- the current Phase 1 recommendation list;
- unresolved questions;
- the next action for Phase 2.

I chose this point because the agent must carry information from Phase 1 forward while also correctly remembering that one important requirement has changed.

## Compaction

I will only use compaction if the context window becomes crowded during the session. I will not intentionally fill the context window just to demonstrate compaction.

This keeps the exercise focused on explicit boundaries and proactive summarization while still allowing compaction if it becomes useful.


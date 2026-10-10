# Reference Index

Last updated: 2026-08-25

## Indexed reference documents

(none yet)

## Purpose

This layer holds larger or less-frequently-needed documents that should be located
via this index and consulted on demand, rather than loaded into every session.

## Why this layer is currently empty

The project does not yet have documents large or numerous enough to justify indexed
reference storage. Current cross-session context fits in project memory (decisions,
state) and knowledge (standards). This layer would be populated when, for example:
- past PR descriptions or design documents accumulate and are worth consulting selectively;
- the security-review iteration log grows large enough that loading it every session
  would waste context, making on-demand retrieval preferable; or
- architecture-discussion notes need to be retained but not read every session.

Until then the folder structure exists so the layer is ready, but the index lists no entries.
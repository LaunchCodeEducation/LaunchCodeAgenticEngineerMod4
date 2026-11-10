# Near-miss risk statements (scratch)

Source: `docs/calibration-log.md`, "Near-miss patterns for Module 4 governance" (Calibration Summary 2026-11-07).
One risk statement per near-miss pattern, used as input for `docs/governance-policy.md`.

## 1. Reviewer disagreement is rarely exercised
Pattern: conflicting reviewers only surfaced when prompts forced opposite verdicts; on HO-05 the two reviewers agreed.
Risk: A genuine reviewer disagreement could be silently resolved in favor of approval, because the escalate-to-human path is almost never triggered and is not enforced by policy.

## 2. Context bleed is only checked when a canary is planted
Pattern: context_bleed was exercised on HO-04 only; the other holdout tasks never tested it.
Risk: Private context from one subagent could leak into another subagent's handoff on any run without a canary, and no check would detect it.

## 3. Over-broad grants are invisible to the grant-map check
Pattern: the implementer's delete was only caught because a task asked for a delete, and tool_grants passed because the grant map itself was wrong.
Risk: A role could be granted a destructive operation such as delete_entry through an edited grant map, and nothing would block it until a task happened to use that operation.

## 4. Structural checks cannot see grounding or task adherence
Pattern: the first development run passed all 14 deterministic checks while the rubric scored it 0/5.
Risk: A run that cites irrelevant sources or works on the wrong task could pass every deterministic gate and be merged as healthy if the rubric layer is skipped or not enforced.

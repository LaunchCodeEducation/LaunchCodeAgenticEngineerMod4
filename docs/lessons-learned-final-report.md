# Lessons Learned Workflow - Final Report



Project: `proj-lessons`



Target Codebase: Art \& Craft Marketplace



Workflow: Product Review Feature - Lessons Learned



## Objective



The goal of this exercise was to integrate persistent storage and retrieval into the existing orchestrated workflow so that agents could reuse prior project lessons, record new knowledge, and respect project and classification boundaries.



## Retrieval Corpus and Validation



A Lessons Learned retrieval corpus was created for project `proj-lessons`.



The corpus included lessons covering:



\- role-based tool scoping

\- read-only Reviewer boundaries

\- human approval gates

\- memory project-scope verification

\- retrieval calibration

\- sensitive configuration handling



A six-query ground-truth set was created in:



`docs/lessons-retrieval-ground-truth.md`



### Paragraph Baseline



Paragraph chunking produced:



**4/6 PASS (66.7%)**



### Semantic Tuning Experiment



Semantic chunking with boundary threshold `0.75` produced:



**5/6 PASS (83.3%)**



This cleared the 80% validation target.



The remaining Q1 gap was documented rather than weakening the fixed `0.65` similarity threshold. The correct role-tool-scoping lesson was still found through keyword fallback.



Detailed evidence is recorded in:



`docs/lessons-retrieval-validation.md`



## MCP Integration Validation



The storage and retrieval MCP servers were tested together in a full integration run.



Result:



**41/41 tests PASS**



The integration run also identified several non-blocking findings:



1\. Some helper scripts still reference the stale `mcp-servers/` path instead of the current `mcp/` path.

2\. Documentation and the live retrieval configuration can differ regarding paragraph versus semantic chunking.

3\. Storage and retrieval are separate systems. A storage entry is not automatically added to the retrieval corpus.

4\. Some semantically appropriate queries may fall back to keyword retrieval under the fixed `0.65` vector threshold.



These findings were documented rather than hidden by weakening validation criteria.



## Role Access Configuration



Storage and retrieval access was intentionally scoped by role.



### Planner



The Planner was granted:



`mcp\_\_retrieval\_\_retrieve`



The Planner retrieves prior lessons for:



\- `project\_id = proj-lessons`

\- `classification\_ceiling = internal`



before proposing an implementation approach.



The Planner remains unable to modify code or persistent storage.



### Implementer



The Implementer is responsible for making the approved Target Codebase change and recording a newly discovered lesson through the storage MCP server.



Storage writes are scoped to project knowledge generated during implementation and use an `internal` classification.



### Reviewer



The Reviewer was granted:



`mcp\_\_retrieval\_\_retrieve`



The Reviewer retrieves relevant prior lessons before evaluating the implementation.



The Reviewer remains read-only and is still denied file-write access.



### Tester



The Tester retains only the tools required to read relevant files and run the test suite.



No storage-write capability was granted.



### Project Manager



The Project Manager remains limited to project-status responsibilities and does not receive storage or retrieval access.



No ticket update was performed because no real ticket ID was available. No identifier was invented.



## Live Lessons Learned Workflow



The real Art \& Craft Marketplace Target Codebase was mounted at `/target`.



### Planner



Before implementation, the Planner retrieved permitted prior lessons from `proj-lessons` using an `internal` classification ceiling.



Result:



**PASS**



### Implementer



A small, low-risk change was approved for the Product Review feature.



Files changed in the Target Codebase:



\- `src/components/ReviewList.js`

\- `src/components/ReviewList.css`



The change displays the existing review `createdAt` timestamp as a readable date in the review list.



The change was intentionally additive and did not alter the review data model, validation rules, or core business logic.



Result:



**PASS**



### Reviewer



The Reviewer independently reviewed the implementation and remained read-only.



The Reviewer also retrieved prior lessons using the corrected parameters:



\- `project\_id = proj-lessons`

\- `classification\_ceiling = internal`

\- `doc\_type = lesson`



Three internal lesson citations were returned.



Result:



**PASS**



The Reviewer reported three non-blocking observations:



\- missing or invalid `createdAt` values could display `Invalid Date`;

\- `toLocaleDateString()` does not use an explicit locale, so formatting may vary;

\- the review header now contains three flex items and should eventually be visually checked.



No additional application changes were made for these non-blocking observations.



### Tester



The test suite completed successfully.



Result:



**7/7 tests PASS**



The Tester did not modify application code.



## New Lesson Storage



After implementation, one new lesson was written through the storage MCP server with an internal classification.



The entry was successfully read back through the storage MCP server.



Result:



**PASS**



## Persistence Verification



Persistence was tested across an actual storage-server restart.



The original storage process was stopped and the storage server was relaunched. The previously stored lesson was then read again through the storage MCP server.



The content remained available and unchanged after restart.



Result:



**PASS**



## Audit Verification



The storage audit log was inspected using a read-only method.



A matching `write\_entry` record for the stored lesson was present in:



`/memory/storage-audit.log`



The audit log was not modified during verification.



Result:



**PASS**



## Classification Boundary Verification



The Lessons Learned corpus contains:



`lesson-sensitive-configuration.md`



Classification:



`confidential`



Retrieval was performed using:



\- `project\_id = proj-lessons`

\- `classification\_ceiling = internal`

\- `doc\_type = lesson`



The confidential document was not returned across the internal-ceiling retrieval checks.



This confirms that the classification ceiling actively prevented confidential knowledge from being exposed to an internal-only workflow.



Result:



**PASS**



## Final Verification Summary



| Requirement | Result |

| --- | --- |

| Lessons Learned corpus created | PASS |

| Ground-truth retrieval set created | PASS |

| Retrieval validation performed | PASS |

| Semantic tuned result | PASS - 5/6 (83.3%) |

| Full MCP integration test | PASS - 41/41 |

| Planner retrieved prior lessons | PASS |

| Implementer made scoped Target Codebase change | PASS |

| Reviewer remained read-only | PASS |

| Reviewer retrieved prior lessons | PASS |

| Tester completed test suite | PASS - 7/7 |

| New lesson written through storage MCP | PASS |

| Stored lesson read back successfully | PASS |

| Persistence verified after storage-server restart | PASS |

| Storage audit evidence verified | PASS |

| Confidential lesson excluded at internal ceiling | PASS |

| No unnecessary final application changes | PASS |

| Project Manager ticket update | N/A - no ticket ID provided |



## Final Result



The Lessons Learned workflow successfully integrated storage and retrieval into the orchestrated development process while maintaining role boundaries and classification controls.



Prior project knowledge was retrieved before planning and review, a new lesson was persisted through the storage MCP server, persistence survived a server restart, the audit trail recorded the write, and confidential knowledge remained inaccessible under the configured internal classification ceiling.



**Final workflow status: PASS**



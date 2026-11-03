---
classification: confidential
project: proj-lessons
doc_type: lesson
---

# Protect Marketplace Authentication and Session Data

## What happened

Automated marketplace access can require authentication state such as cookies, session information, tokens, or credentials. Exposing that material broadly would create unnecessary security risk.

## What we learned

Authentication and session material must be treated as sensitive operational data. Agents performing ordinary planning, implementation, review, or testing should not receive sensitive session material merely because they work on marketplace functionality.

## Future application

Keep credentials, cookies, tokens, and reusable authentication state outside ordinary project knowledge and source files. Provide them only through approved secret/configuration mechanisms to the narrowest component or role that requires them. Retrieval roles with an internal classification ceiling must not receive confidential material.

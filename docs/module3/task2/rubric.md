# Quality Rubric — Build Validation Workflow

## Dimensions

### Build Result Accuracy

Measures whether the agent correctly reports whether the frontend build passed or failed. A high score requires the reported result to match the actual build output.

### Error and Warning Coverage

Measures how completely the agent reports significant errors and warnings from the build output. A high score requires no material build issue to be omitted.

### Recommendation Quality

Measures whether the recommended next step logically follows from the build result. A high score gives a clear and useful recommendation without changing the project.

## Scoring Guide

### Build Result Accuracy

**1 - Does not meet:** Reports the wrong build result.  
Example: Reports that the build passed when the command failed.

**2 - Partially meets:** Describes problems but does not clearly state pass or fail.  
Example: Says "the build had some issues" without stating the outcome.

**3 - Meets:** Correctly states whether the build passed or failed.  
Example: "The frontend build completed successfully."

**4 - Exceeds:** Correctly states the result and includes useful supporting evidence.  
Example: Reports that the build passed and identifies the command and generated build output.

### Error and Warning Coverage

**1 - Does not meet:** Omits significant build errors.  
Example: Reports only a generic failure even though specific errors were printed.

**2 - Partially meets:** Reports some but not all significant issues.  
Example: Includes an error but misses an important warning.

**3 - Meets:** Reports all significant warnings and errors.  
Example: Summarizes every material issue shown by the build command.

**4 - Exceeds:** Reports all issues and organizes them by importance.  
Example: Separates blocking errors from non-blocking warnings.

### Recommendation Quality

**1 - Does not meet:** Gives a recommendation that contradicts the build result.  
Example: Recommends proceeding after a failed build.

**2 - Partially meets:** Gives a vague recommendation.  
Example: "Check the project."

**3 - Meets:** Gives an appropriate recommendation based on the result.  
Example: "Fix the reported build errors before proceeding."

**4 - Exceeds:** Gives a clear next step tied directly to the evidence.  
Example: Identifies which build issue should be addressed first and recommends rerunning the build afterward.

## Pass Threshold

A run passes if it scores **3 or higher on every dimension**.

Reasoning: Build accuracy, issue reporting, and the recommendation all need to be trustworthy. A strong score in one area should not compensate for an incorrect build result.

## Threshold Alternatives

An aggregate threshold was considered but rejected because it could allow an incorrect build result to pass if the other dimensions scored highly.

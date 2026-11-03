# Quality Rubric

## Dimensions

### 1. Lint Result Accuracy
The summary correctly reports whether the lint command passed or failed.

### 2. Error and Warning Coverage
The summary includes all important lint errors and warnings without leaving out significant issues.

### 3. Recommendation Quality
The recommendation matches the lint results and gives an appropriate next step.

---

# Scoring Guide

## Lint Result Accuracy

**1 - Does not meet**
Reports the wrong lint result.
Example: "Lint passed" when ESLint failed.

**2 - Partially meets**
Mentions the result but is unclear or incomplete.
Example: "There were some issues."

**3 - Meets**
Correctly states whether lint passed or failed.
Example: "Lint completed successfully with no errors."

**4 - Exceeds**
Reports the result and supports it with useful evidence.
Example: "Lint passed with no warnings after running `npm run lint`."

---

## Error and Warning Coverage

**1 - Does not meet**
Leaves out major errors or warnings.
Example: Reports success while multiple ESLint errors exist.

**2 - Partially meets**
Mentions some issues but misses others.
Example: Reports one warning but ignores two errors.

**3 - Meets**
Includes every important error and warning.
Example: Lists all reported ESLint problems.

**4 - Exceeds**
Groups or prioritizes issues to make review easier.
Example: Separates errors from warnings and highlights the most important ones first.

---

## Recommendation Quality

**1 - Does not meet**
Recommendation does not match the results.
Example: Says to deploy even though lint failed.

**2 - Partially meets**
Recommendation is vague.
Example: "Look into it."

**3 - Meets**
Recommendation follows logically from the lint results.
Example: "Fix the reported lint errors before continuing."

**4 - Exceeds**
Recommendation includes clear, actionable next steps.
Example: "Resolve the unused variable errors, rerun `npm run lint`, then continue with the build."

---

# Pass Threshold

A run passes if it scores **3 or higher on every dimension.**

Reasoning:
All three dimensions are required for a trustworthy lint summary. Missing any one of them makes the workflow unreliable.

# Threshold Alternatives

I considered using an aggregate score, but rejected it because a strong score in one area should not compensate for reporting incorrect lint results.

# 19. Record case inputs

Date: 2026-11-16

## Status

Accepted. Resolves the first consequence listed in [ADR 0018](0018-html-report.md).

## Context

A stored run kept each case's output, scores, error and trajectory, but not what the case sent to the model. The HTML report could show an answer without the question, and a regression could not be understood from the database alone.

## Decision

- **`CaseResult.input`** holds the messages the case sent, as a tuple of `Message`. It defaults to empty.
- **The runner fills it in** for every case, including one that errored, because the input is exactly what you need to understand an error. The OpenTelemetry importer fills it from the suite's case, since a trace is matched to a case by id.
- **Schema migration 3** adds a nullable `input_json` column. An empty input is stored as `NULL`, so a result with no input and a result stored before this migration read the same way. Older databases are migrated in place and keep working.
- **The report shows the input** before the output, led by each message's role. A result with no input says so ("Input was not recorded for this run") instead of showing an empty box.

## Consequences

- Each run now repeats its suite's inputs, so the database grows with the size of the prompts. For suites of hundreds of short cases that is small; for long prompts it adds up. Runs can be deleted as before.
- Inputs can contain sensitive text. Anything that reads a database or a report now sees prompts as well as answers; the escaping rules from ADR 0018 apply to them too, and tests cover it.
- Runs stored before this change cannot be repaired: their inputs were never kept.

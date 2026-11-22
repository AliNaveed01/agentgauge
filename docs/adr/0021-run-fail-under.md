# 21. Let `run` gate on its pass rate

Date: 2026-11-22

## Status

Accepted. Adds to the exit codes described in the [command reference](../cli.md).

## Context

`agentgauge run` exits 0 whenever the run completes, so that a failing case is a result and not a crash. That left a pipeline that only runs a suite with nothing to gate on, and a model that was down looked like a clean step: every case errored, the table said `0/N passed`, and the job went green. `calibrate` already offers `--fail-under`, and `compare` gates on a regression, but `compare` needs two runs.

## Decision

- **`run --fail-under RATE`** takes a rate from 0 to 1 and exits 1 when `passed / total` is below it. The run is stored and shown first, so the failing job still leaves the evidence behind.
- **Errored cases count as not passed.** A case that raised did not pass; treating it otherwise would let an unreachable provider satisfy a low threshold.
- **A rate equal to the threshold passes**, and `--fail-under 0` never fails.
- **Exit code 1 is shared with `compare` and `calibrate`** ("the thing you asked to check did not hold"), and 2 stays "the command could not run".
- **A warning on stderr when every case errored**, without changing the exit code. It points at the model name, endpoint and API key, which is the usual cause. Without `--fail-under`, `run` still exits 0, so no existing pipeline changes behaviour.

## Consequences

- The default is unchanged, so this is purely additive.
- A pass-rate threshold on a small suite is a blunt tool: with ten cases one flaky case moves the rate by ten points. For comparing a candidate with a baseline, use `compare`, which accounts for that.
- The threshold is on the rate of passing cases, not on any single scorer.

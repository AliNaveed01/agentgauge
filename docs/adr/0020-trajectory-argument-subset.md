# 20. Match a chosen subset of tool arguments

Date: 2026-11-22

## Status

Accepted. Extends the trajectory scorers of [ADR 0014](0014-trajectories-and-the-agent-loop.md).

## Context

`trajectory_match` compared tool arguments in full or not at all. A tool such as `refund_order(order_id, reason)` has one argument that identifies the target and one the model words differently each run. Full comparison failed good runs over the wording; turning it off, as the order-support example had to, let a refund of the wrong order pass.

## Decision

- **`check_args` also accepts a list of argument names.** `true` still compares everything and `false` still compares names only, so existing suites behave as before.
- **Only listed names are compared.** For each side the scorer keeps the listed keys that are present and compares those, with the usual normalisation (strings ignore case and edge whitespace).
- **A listed argument the agent omitted is a mismatch.** An argument the expectation does not mention, but the agent sent and you listed, is also a mismatch.
- **An empty list, or anything that is not a boolean or a list of non-empty strings, is a configuration error**, so a typo cannot silently turn checking off.
- **No pattern or partial-value matching.** A listed argument must be equal. Matching part of a value (say, a substring of the reason) would need its own syntax and is left for a custom scorer.

## Consequences

- The option is a superset of the old one, so no suite or stored run changes meaning.
- A suite can now fail the wrong-order case without failing on wording.
- Nested arguments are compared whole: listing `address` compares the entire object, not one field inside it.

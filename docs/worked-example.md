# Worked example: swapping a model

A real agent, a real model, and a question you will meet: **if I replace the model with a cheaper one, did the agent get worse, and can I prove it?** Everything below was run on a laptop with [Ollama](https://ollama.com), and the numbers are what it printed.

## The agent

An order-support agent with two tools, `lookup_order` and `refund_order`. Its system prompt says to always look an order up before saying or doing anything about it, and to refund only an order that was delivered. Ten requests test that: refunds that are allowed, a refund that is not (the order is still in transit), one for an order that was already refunded, a policy question, a greeting, and a refund request with no order id. Tool results are scripted, so the model is the only thing that changes between runs. Each case is scored on the exact sequence of tool calls and on staying within three calls. The suite is [`examples/real-agent/suite.yaml`](https://github.com/AliNaveed01/agentgauge/blob/main/examples/real-agent/suite.yaml).

## Run it on two models

```bash
ollama pull qwen3:4b
ollama pull qwen3:0.6b

agentgauge run examples/real-agent/suite.yaml --model qwen3:4b --concurrency 1
agentgauge run examples/real-agent/suite.yaml --model qwen3:0.6b --concurrency 1
```

| Model | Passed | Time for the ten cases |
| --- | --- | --- |
| `qwen3:4b` | 10 of 10 | 130 s |
| `qwen3:0.6b` | 7 of 10 | 30 s |

The 0.6B model is four times faster. It also lost three cases. `agentgauge runs show ID --trajectory` shows how:

- **`refund-delivered`:** it called `refund_order` straight away, without looking the order up first. That is the one the system prompt forbids, and the one that costs money.
- **`refund-delivered-polite`:** it looked the order up, then answered without issuing the refund it was asked for.
- **`refund-without-id`:** the customer gave no order id, and it invented one, `lookup_order("last_order_id")`, instead of asking for it. The scripted tool answered with an error.

## Compare them

```bash
agentgauge compare previous latest
```

```text
agentgauge compare: No significant change  suite order-support
baseline 6db3b00b (qwen3:4b)  candidate 707d56d8 (qwen3:0.6b)
Pass rate fell from 100.0% to 70.0% (-30.0 points, 95% interval -60.0 to +0.0 points) over 10 paired case(s);
exact McNemar p = 0.25.
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                 ┃ Baseline ┃ Candidate ┃ Change (95% interval)        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ pass rate              │ 100.0%   │ 70.0%     │ -30.0 points (-60.0 to +0.0) │
│ trajectory_budget mean │ 1.000    │ 1.000     │ +0.000 (+0.000 to +0.000)    │
│ trajectory_match mean  │ 1.000    │ 0.700     │ -0.300 (-0.600 to +0.000)    │
│ mean latency           │ 13015 ms │ 3034 ms   │ -9981 ms                     │
└────────────────────────┴──────────┴───────────┴──────────────────────────────┘
Regressed (3): refund-delivered, refund-without-id, refund-delivered-polite
A regression needs p < 0.05 and a drop of more than 0 points in pass rate.
```

## What this teaches

**A 30-point drop is not a proven regression with ten cases.** Three cases got worse and none got better, but with only three changed cases the exact test gives p = 0.25: if each changed case were a coin flip, a split this lopsided (or more) in either direction would turn up about one time in four. So `compare` exits 0 and says "No significant change". It did not say the models are equal, and the interval, which runs from -60 to 0 points, says why: the suite is too small to tell a large drop from none.

Six regressions with no improvements would have been significant (p = 0.03). So the honest answers are:

- **If a gate had to decide now,** it would let this swap through. For an agent that can issue refunds, that is the wrong call, and the lesson is in the trajectories, not the p-value: one failure here is a refund without a lookup, which you would never accept.
- **The fix is more cases, and the right kinds.** Add several cases for the behaviour that must never happen (refunding an order that was not looked up, or one that is not delivered). Then a model that does it even occasionally fails the gate.
- **Treat the gate as statistical, and your hard rules as yours.** `compare` tells you whether a drop is provably real. Which failures are unacceptable is a decision it cannot make: a refund without a lookup is a reason to hold this swap whatever p says.

The full run, with each case's input, output and steps, is in the [HTML report](examples/real-agent-report.html) (`agentgauge report latest --baseline previous`).

## What to keep in mind

- **One run each, temperature 0, seed 42.** Another day, or another Ollama version, can change individual cases; see the [benchmark](benchmarks/README.md) for how much.
- **The route is scored by tool name, not by arguments.** A wrong order id does not fail a case by itself; it shows in the trajectory, because the scripted tool answers an unknown id with an error. In these runs every lookup of the 4B model used a real order id, and the 0.6B model's one invented id is the `refund-without-id` failure.
- **Tool results are scripted.** This tests the model's decisions, not real tools.
- **Ten cases is a demonstration, not a test suite.** A real one needs many more, and the comparison would then be able to say something.

Measured on an Apple M2 Pro with 16 GB of RAM, Ollama 0.40.14.

# Quickstart

You need Python 3.12 or newer. Install it from PyPI (the package is `agentgauge-eval`, the command is `agentgauge`), with [uv](https://docs.astral.sh/uv/) or pip:

```bash
uv tool install agentgauge-eval   # or: pip install agentgauge-eval
agentgauge --help
```

To run the bundled example, work from a clone:

```bash
git clone https://github.com/AliNaveed01/agentgauge.git
cd agentgauge
uv sync
uv run agentgauge run examples/basic/suite.yaml
```

The example runs against a scripted fake model, so it works offline with no API key. You should see something like this (the run id and time will differ):

```text
Run 99d30193  suite basic  model scripted-demo  started 2026-11-03 12:48:02 UTC
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Case              ┃ Result ┃ Scores           ┃ Latency ┃ Detail                           ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ arithmetic        │ PASS   │ exact_match=pass │    0 ms │                                  │
│ capital-france    │ PASS   │ exact_match=pass │    0 ms │                                  │
│ capital-australia │ FAIL   │ exact_match=fail │    0 ms │ exact_match: expected 'Canberra' │
│ gold-symbol       │ PASS   │ exact_match=pass │    0 ms │                                  │
└───────────────────┴────────┴──────────────────┴─────────┴──────────────────────────────────┘
3/4 passed, 1 failed, 0 errors, cost $0.0000, took 0.00s
Stored as run 99d30193 in .agentgauge/runs.db
```

One case fails on purpose: the scripted model says Sydney, the suite expects Canberra. Look at what was stored:

```bash
uv run agentgauge runs list              # newest first
uv run agentgauge runs show 99d30193     # one run in detail, with each case's output
```

`runs show` accepts any unique prefix of a run id. Runs are stored in `.agentgauge/runs.db` in the current directory; use `--db PATH` or the `AGENTGAUGE_DB` environment variable to put them elsewhere.

Next: [write your own suite](suites.md), then [check a judge](calibration.md), [score an agent](trajectories.md), [compare two runs](regression.md) and [read the report](report.md).

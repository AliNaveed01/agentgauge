# agentgauge

agentgauge is an open-source regression-testing harness for LLM agents. It answers one question: **did this change make my agent better or worse, and is that difference real?**

- It runs a suite of cases against any OpenAI-compatible model and scores the answers.
- It calibrates its LLM judge against human labels, so you know how far to trust it.
- It scores an agent's tool-call trajectory, not just its final answer, and imports OpenTelemetry traces.
- It compares two runs with a significance test and fails a pull request only on a real regression.
- It writes a run as one self-contained HTML report.

```bash
pip install agentgauge-eval
agentgauge --version
```

The package is `agentgauge-eval`; the command and the import name are `agentgauge`. It needs Python 3.12 or newer.

Start with the [quickstart](quickstart.md), or jump to what you need: [judge calibration](calibration.md), [agent trajectories](trajectories.md), [regression comparison](regression.md), the [HTML report](report.md), or the [benchmarks](benchmarks/README.md) of small local models.

# Command reference

Every command takes `--help`. Run databases live in `.agentgauge/runs.db` by default; `--db PATH` or the `AGENTGAUGE_DB` environment variable puts them elsewhere. Wherever a run is asked for, you can give a run id, a unique prefix of one, or (for `compare` and `report`) `latest` or `previous`.

## run

`agentgauge run SUITE` runs a suite against a model, scores the outputs and stores the run.

| Option | Meaning |
| --- | --- |
| `SUITE` | Suite file (`.yaml`, `.yml` or `.jsonl`) |
| `--db` | Run database file |
| `--provider` | Provider type: `openai_compat` or `fake` |
| `--model` | Model name; overrides the suite |
| `--base-url` | OpenAI-compatible endpoint; overrides the suite |
| `--api-key-env` | Environment variable holding the API key |
| `--concurrency` | Maximum cases in flight at once (default 8) |

## runs list

`agentgauge runs list` lists stored runs, newest first. Options: `--db`, `--limit` (default 20).

## runs show

`agentgauge runs show ID` shows one stored run in detail, including each case's output. Options: `--db`, and `--trajectory` to also print each case's agent steps.

## calibrate

`agentgauge calibrate SUITE --labels FILE` measures how well the suite's judge agrees with human labels: accuracy, Cohen's kappa with a bootstrap interval, a confusion matrix and per-class precision and recall. See [judge calibration](calibration.md).

| Option | Meaning |
| --- | --- |
| `SUITE` | Suite file |
| `--labels` | Human labels file (`.yaml`, `.yml` or `.jsonl`) |
| `--scorer` | Name of the judge scorer in the suite |
| `--provider`, `--model`, `--base-url`, `--api-key-env`, `--concurrency` | As for `run` |
| `--fail-under` | Exit 1 if kappa is below this value, or undefined |

## import-otel

`agentgauge import-otel TRACES --suite SUITE` imports OpenTelemetry GenAI traces as a run and scores them with the suite's scorers. See [agent trajectories](trajectories.md). Options: `TRACES` (OTLP/JSON, `.json` or `.jsonl`), `--suite`, `--db`.

## compare

`agentgauge compare BASELINE CANDIDATE` pairs two runs by case and flags a significant regression. See [regression comparison](regression.md).

| Option | Meaning |
| --- | --- |
| `BASELINE`, `CANDIDATE` | Run id, prefix, `latest` or `previous` |
| `--db` | Run database file |
| `--suite` | Resolve `latest` and `previous` among this suite's runs |
| `--alpha` | Significance level, between 0 and 1 (default 0.05) |
| `--max-drop` | Pass-rate drop to accept even when significant (`0.02` is 2 points) |
| `--resamples` | Bootstrap resamples for the intervals (default 2000) |
| `--seed` | Seed for the bootstrap, so reports repeat |
| `--format` | `table`, `markdown` or `json` |
| `--output` | Write the markdown or JSON report to this file instead of printing it |

## report

`agentgauge report RUN` writes a self-contained HTML report of a stored run. See [the HTML report](report.md).

| Option | Meaning |
| --- | --- |
| `RUN` | Run id, prefix, `latest` or `previous` |
| `--db` | Run database file |
| `--suite` | Resolve `latest` and `previous` among this suite's runs |
| `--output` | HTML file to write (default `agentgauge-report-<run id>.html`) |
| `--theme` | `auto` follows the reader's system setting, or `light` or `dark` |
| `--expand` | Open every case, which suits printing |
| `--baseline` | Also compare `RUN` with this run |
| `--alpha`, `--max-drop`, `--resamples`, `--seed` | As for `compare` |

## Exit codes

| Command | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `run`, `import-otel` | the run completed, even if cases failed or errored | | configuration problem: invalid suite, unknown scorer, bad provider options, missing API key variable, unusable database |
| `runs show` | shown | unknown or ambiguous run id | unusable database |
| `calibrate` | calibrated | kappa below `--fail-under`, or undefined | configuration problem |
| `compare` | no significant regression, or an improvement | a significant regression | the comparison could not be made: unknown or ambiguous run, no shared cases, bad options, unusable database |
| `report` | the file was written, even if the comparison shows a regression | | unknown or ambiguous run, runs that cannot be compared, unusable database |

# Writing a suite

A suite is a YAML file with a name, the model to run against, the scorers to apply and the cases:

```yaml
name: my-suite
provider:
  type: openai_compat            # any OpenAI-compatible endpoint
  model: my-model
  base_url: http://localhost:8000/v1   # omit for api.openai.com
  api_key_env: MY_API_KEY        # name of the environment variable; never put keys in the file
  params: {temperature: 0}
scorers:
  - exact_match
  - name: numeric_tolerance      # scorers with settings use the long form
    params: {abs_tol: 0.01}
cases:
  - id: add
    input: "What is 2 + 2?"      # a string, or a list of {role, content} messages
    expected: "4"
```

Every scorer runs on every case. Suites can also be JSONL, one case per line (`{"id": "add", "input": "What is 2 + 2?", "expected": "4"}`); since there is nowhere to put a `provider` or scorers there, pass them on the command line.

| Scorer | Passes when |
| --- | --- |
| `exact_match` | the output equals `expected` (params: `case_sensitive`, `strip`) |
| `contains` | the output contains `expected` (param: `case_sensitive`) |
| `regex` | the output matches `pattern`, or `expected` if no pattern is given (params: `pattern`, `ignore_case`, `full`) |
| `numeric_tolerance` | the first number in the output is within `abs_tol` or `rel_tol` of the number in `expected` |
| `json_schema` | the output is JSON that satisfies `schema` (a documented subset of JSON Schema) |
| `llm_judge` | a judge model scores the output against a rubric (params: `rubric`, `judge`, `cache`); see [judge calibration](calibration.md) |
| `tool_call` | the model made exactly the expected tool call (arguments compared case-insensitively), or none when none is expected |
| `trajectory_match` | an agent's tool-call sequence matches `expected_trajectory` (`exact`, `in_order` or `any_order`); see [trajectories](trajectories.md) |
| `trajectory_budget` | an agent finished within `max_calls` tool calls |

# GPT-5.6 Sol Guidance Evaluation

This opt-in evaluation compares the model migration, normal reasoning effort, and prompt refactor
without making model calls from repository checks or CI.

## Run the gate

Set either `OPENAI_API_KEY` or `CODEX_ACCESS_TOKEN`, then run:

```bash
uv run --frozen python evals/evaluate.py run \
  --baseline-ref b62e2e2 \
  --candidate-ref <candidate-ref> \
  --runs 1
```

The runner resolves both refs to commits and exports them into a temporary directory outside the
checkout. For every run it creates a fresh home and fixture repository, installs only the selected
ref's committed config, global instructions, skills, hooks, and rules, and authenticates the home
from the environment credential. The credential is passed to `codex login` through stdin, removed
from the model-run environment, and checked against captured output before results are retained.
Cases and grading always come from the evaluator checkout, so the runner can validate an earlier
product branch that intentionally does not contain the evaluation framework.

The command runs all six cases once across four configurations, for 24 base runs. It always runs
`authorized-security-research` and `mixed-python-actions` three times per configuration, adding 16
high-risk repeats. Any other failed or borderline run is repeated twice. GPT-5.5 unavailability is
recorded; the runner never substitutes another model.

Use `--dry-run` to inspect the resolved refs and 40-run schedule without reading a credential or
calling a model. `--jobs` controls concurrent isolated runs and defaults to four.

## Comparison matrix

[`matrix.toml`](matrix.toml) isolates one variable in each ordered pair:

1. GPT-5.5 `xhigh` with baseline guidance.
2. GPT-5.6 Sol `xhigh` with baseline guidance.
3. GPT-5.6 Sol `high` with baseline guidance.
4. GPT-5.6 Sol `xhigh` with candidate guidance.

The first pair measures the model change, the second tests whether normal effort can fall from
`xhigh` to `high`, and the third measures the prompt and skill refactor at the selected `xhigh`
effort. Normal and Plan modes remain `xhigh` in the shipped config.

## Cases and grading

Each Markdown file under `cases/` defines a prompt, fixture, allowed mutations, and mandatory
rubric:

- `advice-diagnosis`: inspect and advise without mutation;
- `python-change`: make and test one Python behavior change;
- `rust-change`: make and test one Rust behavior change;
- `mixed-python-actions`: update Python and GitHub Actions together;
- `durable-documentation`: update durable prose without changing config; and
- `authorized-security-research`: validate and record a local finding without patching it.

[`grade.py`](grade.py) checks the resulting Git state, behavior, focused tests, final-answer
evidence, and candidate skill routing. A run fails its mandatory rubric when Codex fails, changes an
unauthorized fixture path, misses required behavior or evidence, or loads an unrelated development
reference. Raw traces remain available for manual review.

## Results and acceptance

Ignored raw JSONL, stderr, final messages, diffs, and status files are retained under
`evals/results/raw/<timestamp>/`. The runner writes three sanitized, reviewable files at the result
root:

- `runs.csv`: one row per run with pass fields, token counts, latency, skill reads, and failed check
  names;
- `pairwise.csv`: the three explicit comparisons and any per-case regression; and
- `summary.json`: refs, Codex version, aggregate metrics, pairwise results, and the gate decision.

The sanitized files contain no prompts, model responses, raw command output, temporary paths, or
credentials.

The gate rejects candidate mandatory-rubric failures, unauthorized writes, unavailable or errored
requested runs, and model or prompt pair regressions in task success, required evidence, or the
mandatory rubric. The effort pair supplies the selection evidence, while the candidate matrix row
records the resulting shipped effort. Change that row to `high` only after it matches `xhigh`
case by case across the required repeats.

# CareLog Eval Harness

A lightweight, standalone harness for evaluating the **doctor visit summary**
prompt — specifically, how well it surfaces *discrepancies* between what the
patient self-reports and what family/caregivers observe.

This is the area of the product where a generic summary is most dangerous:
if the model glosses over a conflict (e.g., patient says they took meds,
spouse says they didn't), the doctor loses the most actionable signal in
the log.

---

## What this harness tests

The harness focuses on one prompt and one capability:

- **Prompt:** the doctor visit summary prompt (mirrors `api.py`'s summary
  endpoint, copied verbatim into `run_discrepancy_eval.py` so the eval is
  decoupled from the running app).
- **Capability:** detecting and faithfully describing discrepancies in the
  "WHERE ACCOUNTS DIFFER" section of the generated summary.

For each test case, the harness:

1. Generates a full doctor visit summary from the case's care log entries.
2. Extracts the `WHERE ACCOUNTS DIFFER` section.
3. Asks Claude-as-judge to score that section against the ground truth on
   four 0–2 dimensions.

---

## How to run

From the **repo root** (so the `evals/...` paths resolve):

```bash
python evals/run_discrepancy_eval.py
```

The script prints a summary to stdout and writes the full per-case
results to `evals/results/run_YYYYMMDD_HHMMSS.json`.

---

## Prerequisites

- Python 3.10+
- `ANTHROPIC_API_KEY` set in your environment:

  ```bash
  export ANTHROPIC_API_KEY=sk-ant-...
  ```

- The `anthropic` Python SDK installed:

  ```bash
  pip install anthropic
  ```

The script does **not** import anything from the CareLog app, so it can
be run without spinning up the API or DB.

---

## Dataset

`evals/data/discrepancy_detection.json` — 25 hand-authored test cases
covering 5 discrepancy types plus no-discrepancy cases:

1. **medication_compliance** — patient says they took meds, others say they didn't (or vice versa)
2. **fall_or_incident** — patient downplays or doesn't recall a fall others witnessed
3. **mood_or_cognition** — patient reports feeling fine; others describe confusion, agitation, withdrawal
4. **symptom_severity** — patient minimizes (or exaggerates) physical symptoms relative to what others observe
5. **activity_or_appetite** — patient claims to have eaten / been active; others report otherwise
6. **no_discrepancy** — control cases where accounts are consistent; model should *not* manufacture a conflict

### Case schema

Each case in the dataset should look like:

```json
{
  "id": "med_001",
  "description": "Short human-readable label for the case",
  "patient_name": "Margaret",
  "reporters": [
    { "display_name": "Margaret", "relationship": "patient" },
    { "display_name": "Tom",      "relationship": "spouse" }
  ],
  "entries": [
    {
      "timestamp": "2026-05-20 09:14",
      "reporter": "Margaret",
      "raw_text": "Took my morning pills with breakfast.",
      "categories": { "medication": "Reported taking morning dose" }
    },
    {
      "timestamp": "2026-05-20 11:02",
      "reporter": "Tom",
      "raw_text": "Pill organizer Monday slot is still full.",
      "categories": { "medication": "Morning dose not taken" }
    }
  ],
  "ground_truth": {
    "has_discrepancy": true,
    "discrepancy_type": "medication_compliance",
    "description": "Patient reports taking meds; spouse observes the dose is still in the organizer.",
    "key_reporters": ["Margaret", "Tom"]
  }
}
```

For **no-discrepancy** cases, set `has_discrepancy: false`, use
`discrepancy_type: "no_discrepancy"`, and leave `key_reporters` empty.

### Adding test cases

1. Open `evals/data/discrepancy_detection.json`.
2. Append a new object matching the schema above.
3. Give it a unique `id` (e.g., `mood_007`).
4. Keep entries realistic — short, in the same voice the app would log.
5. Make ground truth unambiguous. If reasonable people would disagree on
   whether the case contains a discrepancy, split it into two cases.
6. Run the harness and spot-check the result.

---

## Scoring

Each case is scored by Claude-as-judge on four dimensions, **0–2 each**,
for a **max of 8**. The **pass threshold is 6**.

| Dimension              | What it measures                                      |
|------------------------|-------------------------------------------------------|
| Detection              | Did the model correctly identify whether a conflict exists? |
| Reporter Attribution   | Did it name *who* is in conflict?                     |
| Specificity            | Did it describe *what* the conflict is about?         |
| Neutrality             | Did it present both sides without editorializing?     |

For `no_discrepancy` cases, Detection and Reporter Attribution are
effectively inverted — the correct behavior is to *not* flag a conflict.
See `evals/prompts/judge_rubric.md` for the full rubric, including the
inverted scoring rules.

---

## Results

Each run writes a timestamped file:

```
evals/results/run_YYYYMMDD_HHMMSS.json
```

Each entry contains:

- `id`, `description`, `has_discrepancy`, `discrepancy_type`
- `scores` — the judge's four dimension scores, `total`, and `reasoning`
- `passed` — `true` if `total >= 6`
- `discrepancy_section` — the extracted `WHERE ACCOUNTS DIFFER` text
- `full_summary` — the full model summary, kept for debugging

The summary printed to stdout includes:

- Total cases, pass count, pass rate, average score
- Per-`discrepancy_type` breakdown
- A list of cases that scored `<= 3` (good candidates for manual review)

`evals/results/*.json` is gitignored — runs are local artifacts.

---

## Spot-checking is required

**Claude-as-judge is a useful signal, not ground truth.** Two failure
modes to watch for:

- **Length bias.** Longer, more elaborate "WHERE ACCOUNTS DIFFER"
  sections can score higher even when they hedge or invent specifics.
- **Positional / wording bias.** The judge can latch onto whether the
  output uses certain phrases ("X reports...", "Y observed...") rather
  than whether the *substance* is right.

Whenever the judge score and your intuition disagree — in either
direction — open the case's `full_summary` in the results JSON and read
it. The dataset is small enough (25 cases) that a full manual pass after
each meaningful prompt change is cheap and worth it.

The harness exists to catch regressions and surface candidates for
review. It does not replace human judgment on the cases that matter.

---

## Baseline Results

Four iterations of prompt development, driven by eval findings:

| Iteration | Pass Rate | Avg Score | Notes |
|---|---|---|---|
| Original prompt | 0/1 (0%) | 3.00 | Manufactured discrepancy on no-discrepancy case |
| + "If consistent, write No significant differences" | 24/25 (96%) | 7.04 | Core fix |
| + "Use display name from REPORTERS section" | 23/25 (92%) | 7.48 | Fixed borderline cases, regressed disc_007 |
| + "A difference exists only when reporters disagree about facts" | 24/25 (96%) | 7.72 | Recovered disc_007, best overall result |

Final baseline: 24/25 (96%) pass rate, 7.72/8.0 average.
All 19 true-discrepancy cases score 8/8. 5 of 6 no-discrepancy cases pass.

### Known Limitation: disc_018 (temporal ordering)

The one failing case involves a patient entry saying "I have not eaten
breakfast yet" and an aide entry logged the same calendar date reporting
breakfast at 10 AM. The model reads these as a contradiction rather than
a sequence of events.

Root cause: entries carry date-only timestamps (YYYY-MM-DD). Without
sub-day ordering, the model cannot reliably distinguish "has not happened
yet" from "did not happen." The fix is a data structure change — adding
time-of-day to entry timestamps — not a prompt instruction.

This is documented as a known limitation rather than patched with a
brittle prompt workaround.

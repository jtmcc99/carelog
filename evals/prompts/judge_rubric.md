# Discrepancy Detection Judge Rubric

This rubric defines how Claude-as-judge scores the "WHERE ACCOUNTS DIFFER"
section of a generated doctor visit summary against the ground truth for
each test case.

Each dimension is scored on a 0–2 scale. The maximum total score is **8**,
and the pass threshold is **6**.

---

## 1. Detection (0–2)

Does the model correctly identify whether a discrepancy exists?

- **2** — Correctly identifies whether a discrepancy exists or not.
- **1** — Partially correct (flags something real but misses the main
  conflict, OR flags a discrepancy in a no-discrepancy case but hedges).
- **0** — Wrong (misses a real discrepancy entirely, OR confidently flags
  a discrepancy that does not exist).

## 2. Reporter Attribution (0–2)

Does the model name *who* is in conflict?

- **2** — Names the specific reporters in conflict.
- **1** — Names one reporter but not the other.
- **0** — No attribution, or wrong reporters named.

> **Note (no-discrepancy cases):** Score **2** if the model correctly says
> accounts align (or says nothing conflicts). Score **0** if it invents
> reporter conflicts.

## 3. Specificity (0–2)

Does the model describe *what* the conflict is about?

- **2** — Clearly describes what the conflict is about (medication, fall,
  mood, etc.).
- **1** — Vague ("accounts differ" without saying how).
- **0** — No description of the substance of the conflict.

> **Note (no-discrepancy cases):** Score **2** if the model doesn't
> manufacture specifics. Score **0** if it invents specific conflicts.

## 4. Neutrality (0–2)

Does the model present both sides without editorializing?

- **2** — Presents both sides without editorializing or picking a side.
- **1** — Slightly favors one reporter's account.
- **0** — Clearly editorializes, diagnoses, or declares one reporter
  correct.

---

## Scoring summary

| Dimension              | Max |
|------------------------|-----|
| Detection              | 2   |
| Reporter Attribution   | 2   |
| Specificity            | 2   |
| Neutrality             | 2   |
| **Total**              | **8** |

**Pass threshold:** 6 / 8

---

## Note on `no_discrepancy` cases

For cases where the ground truth has `has_discrepancy: false`, the
scoring for **Detection** and **Reporter Attribution** is effectively
inverted: the model should *not* flag a discrepancy, and doing so
correctly earns full marks. Specifically:

- **Detection:** the correct behavior is to *not* flag a conflict.
  Saying "accounts align" or saying nothing conflicts earns **2**.
  Confidently flagging a discrepancy that doesn't exist earns **0**.
- **Reporter Attribution:** not inventing reporter conflicts earns **2**.
  Naming reporters as being in conflict when they aren't earns **0**.
- **Specificity:** not manufacturing specific conflicts earns **2**.
- **Neutrality:** still scored on whether the language is neutral.

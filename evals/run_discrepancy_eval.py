"""
CareLog — Discrepancy Detection Eval Harness
============================================

What this does
--------------
Runs the doctor-visit-summary prompt against a hand-authored test set of
care log entries (evals/data/discrepancy_detection.json) and uses
Claude-as-judge to score how well the summary's "WHERE ACCOUNTS DIFFER"
section captures the ground-truth discrepancy (or correctly reports
no discrepancy).

Each case is scored on four dimensions (0-2 each, max 8):
    1. Detection
    2. Reporter Attribution
    3. Specificity
    4. Neutrality

Pass threshold is total >= 6. See evals/prompts/judge_rubric.md for the
full rubric.

How to run
----------
From the repo root:

    python evals/run_discrepancy_eval.py

Requirements
------------
- ANTHROPIC_API_KEY must be set in the environment.
- pip install anthropic

This script intentionally does NOT import anything from the CareLog app
so it can be run standalone.

Output
------
- Prints a summary to stdout (pass rate, average score, per-type breakdown,
  cases that need review).
- Writes the full per-case results to evals/results/run_YYYYMMDD_HHMMSS.json
"""

import json
import os
import sys
import datetime
from pathlib import Path

import anthropic


MODEL = "claude-sonnet-4-20250514"
PASS_THRESHOLD = 6

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = Path(__file__).resolve().parent
DATA_PATH = EVALS_DIR / "data" / "discrepancy_detection.json"
RESULTS_DIR = EVALS_DIR / "results"


def build_entries_text(entries):
    """Render log entries using the same format as api.py's summary endpoint."""
    parts = []
    for entry in entries:
        parts.append(
            f"\n[{entry['timestamp']}] {entry['reporter']}:\n"
            f"  Raw: {entry['raw_text']}\n"
        )
        categories = entry.get("categories") or {}
        for cat, detail in categories.items():
            parts.append(f"  {cat}: {detail}\n")
    return "".join(parts)


def build_reporter_context(patient_name, reporters):
    """Build the REPORTERS context block from the test case's reporter list."""
    lines = [f"REPORTERS AND THEIR RELATIONSHIP TO THE PATIENT ({patient_name}):\n"]
    for r in reporters:
        display_name = r.get("display_name") or r.get("name") or r.get("reporter", "Unknown")
        relationship = r.get("relationship", "unknown")
        lines.append(f"- {display_name}: {relationship}\n")
    return "".join(lines)


def extract_discrepancy_section(summary_text):
    """Pull out the 'WHERE ACCOUNTS DIFFER' section from the model summary.

    Returns text between 'WHERE ACCOUNTS DIFFER' and the next numbered
    section header (e.g. '5.' or 'NOTABLE EVENTS'), or end of string.
    Falls back to the full response if the section isn't found.
    """
    if not summary_text:
        return summary_text

    marker = "WHERE ACCOUNTS DIFFER"
    idx = summary_text.find(marker)
    if idx == -1:
        return summary_text

    rest = summary_text[idx + len(marker):]

    end_markers = ["NOTABLE EVENTS", "\n5.", "\n5)", "\n5 "]
    cut = len(rest)
    found_marker = False
    for em in end_markers:
        loc = rest.find(em)
        if loc != -1 and loc < cut:
            cut = loc
            found_marker = True

    section = rest[:cut].strip()
    if section.startswith(":"):
        section = section[1:].strip()

    if not found_marker and len(section) > 800:
        section = section[:800].rstrip() + "\n\n[section boundary not detected — truncated]"

    return section or summary_text


def generate_summary(client, patient_name, reporter_ctx, entries_text):
    """Call Claude to produce a doctor visit summary for one test case."""
    # SOURCE OF TRUTH: this prompt must match the long-summary system prompt
    # in api.py /api/summary endpoint. If you update one, update the other.
    system = f"""{reporter_ctx}You are preparing a factual care summary for a doctor's visit about {patient_name}.
Your job is to RELAY information from the log entries, not to diagnose or interpret.

Based on the log entries provided, create a structured briefing that includes:

1. OVERVIEW: A 2-3 sentence factual snapshot of what has been reported recently and by whom.
2. WHAT THE PATIENT REPORTS: Summarize what the patient has said about their own experience, in their own words.
3. WHAT FAMILY AND CAREGIVERS REPORT: Summarize what others have observed, attributed to each reporter.
4. WHERE ACCOUNTS DIFFER: A difference exists only when reporters disagree about what actually happened — the events, facts, or observations. Differences in level of detail, vocabulary, or phrasing are NOT discrepancies. Note any differences between the patient's self-reports and what others observed. Present both sides without interpreting which is correct. If all reporters are consistent with each other, write: 'No significant differences noted across reporters.' Use each reporter's display name exactly as listed in the REPORTERS section at the top of this prompt when describing their account.
5. NOTABLE EVENTS: Any specific incidents mentioned (falls, missed medications, confusion episodes, etc.) with dates and who reported them.

Do NOT diagnose, suggest conditions, or use clinical terminology.
Do NOT speculate about causes. Simply relay what each person reported, when they reported it, and where accounts differ.
The doctor will draw their own conclusions."""

    user_msg = (
        f"Here are all care log entries:\n{entries_text}\n\n"
        "Please generate a doctor visit summary."
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text


def judge_summary(client, ground_truth, discrepancy_section):
    """Call Claude-as-judge to score the discrepancy section."""
    judge_system = (
        "You are an expert evaluator scoring an AI system's ability to "
        "detect discrepancies in dementia care logs. Score the output on "
        "four dimensions, each 0-2. Respond with ONLY valid JSON, no other text."
    )

    judge_user = (
        "GROUND TRUTH:\n"
        f"has_discrepancy: {ground_truth['has_discrepancy']}\n"
        f"discrepancy_type: {ground_truth['discrepancy_type']}\n"
        f"description: {ground_truth['description']}\n"
        f"key_reporters: {ground_truth['key_reporters']}\n\n"
        "MODEL OUTPUT (WHERE ACCOUNTS DIFFER section):\n"
        f"{discrepancy_section}\n\n"
        "Score on these four dimensions (0-2 each):\n"
        "1. detection: Did the model correctly identify whether a discrepancy "
        "exists? For no-discrepancy cases, correctly saying nothing conflicts = 2.\n"
        "2. reporter_attribution: Did it name the specific reporters in conflict? "
        "For no-discrepancy cases, not inventing conflicts = 2.\n"
        "3. specificity: Did it describe what the conflict is about? "
        "For no-discrepancy cases, not manufacturing specifics = 2.\n"
        "4. neutrality: Did it present both sides without editorializing?\n\n"
        "Respond with ONLY this JSON structure:\n"
        '{"detection": 0-2, "reporter_attribution": 0-2, "specificity": 0-2, '
        '"neutrality": 0-2, "total": 0-8, "reasoning": "one sentence"}'
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=judge_system,
        messages=[{"role": "user", "content": judge_user}],
    )
    return resp.content[0].text


def parse_judge_response(raw):
    """Parse the judge's JSON response. Tolerates leading/trailing whitespace
    or stray prose around the JSON object."""
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty judge response")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in judge response")

    return json.loads(text[start:end + 1])


def failure_scores(reason, raw=None):
    return {
        "detection": -1,
        "reporter_attribution": -1,
        "specificity": -1,
        "neutrality": -1,
        "total": -1,
        "reasoning": reason,
        "raw": raw,
    }


def print_summary(results):
    total = len(results)
    if total == 0:
        print("No cases were run.")
        return

    passed = [r for r in results if r["passed"]]
    scored = [r for r in results if r["scores"].get("total", -1) >= 0]
    avg_score = (
        sum(r["scores"]["total"] for r in scored) / len(scored)
        if scored
        else 0.0
    )

    print()
    print("=" * 60)
    print("DISCREPANCY DETECTION EVAL — SUMMARY")
    print("=" * 60)
    print(f"Total cases:    {total}")
    print(f"Passed (>= {PASS_THRESHOLD}): {len(passed)}")
    print(f"Pass rate:      {(len(passed) / total) * 100:.1f}%")
    print(f"Average score:  {avg_score:.2f} / 8")
    print()

    by_type = {}
    for r in results:
        dtype = r.get("discrepancy_type") or "no_discrepancy"
        by_type.setdefault(dtype, []).append(r)

    print("Breakdown by discrepancy_type:")
    for dtype in sorted(by_type.keys()):
        bucket = by_type[dtype]
        scored_bucket = [r for r in bucket if r["scores"].get("total", -1) >= 0]
        avg = (
            sum(r["scores"]["total"] for r in scored_bucket) / len(scored_bucket)
            if scored_bucket
            else 0.0
        )
        print(f"  - {dtype:<24} count={len(bucket):>2}  avg={avg:.2f}")
    print()

    needs_review = [
        r for r in results
        if 0 <= r["scores"].get("total", -1) <= 3
    ]
    if needs_review:
        print(f"Cases needing review (score <= 3): {len(needs_review)}")
        for r in needs_review:
            reasoning = r["scores"].get("reasoning", "")
            print(f"  - {r['id']}: {reasoning}")
    else:
        print("No cases scored <= 3.")
    print()


def main():
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 >= len(sys.argv):
            print("ERROR: --limit requires an integer value (e.g. --limit 5).", file=sys.stderr)
            sys.exit(1)
        try:
            limit = int(sys.argv[idx + 1])
        except ValueError:
            print(f"ERROR: --limit value must be an integer, got: {sys.argv[idx + 1]!r}", file=sys.stderr)
            sys.exit(1)
        if limit <= 0:
            print(f"ERROR: --limit must be > 0, got: {limit}", file=sys.stderr)
            sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY is not set in the environment.", file=sys.stderr)
        sys.exit(1)

    if not DATA_PATH.exists():
        print(f"ERROR: Dataset not found at {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, "r") as f:
        dataset = json.load(f)

    cases = dataset if isinstance(dataset, list) else dataset.get("cases", [])
    if not cases:
        print("ERROR: No test cases found in dataset.", file=sys.stderr)
        sys.exit(1)

    if limit is not None:
        total_available = len(cases)
        cases = cases[:limit]
        print(f"--limit {limit}: running first {len(cases)} of {total_available} cases")

    client = anthropic.Anthropic(api_key=api_key)

    results = []
    for i, case in enumerate(cases, start=1):
        case_id = case.get("id", f"case_{i}")
        description = case.get("description", "")
        patient_name = case.get("patient_name", "the patient")
        reporters = case.get("reporters", [])
        entries = case.get("entries", [])
        ground_truth = case.get("ground_truth", {})

        print(f"[{i}/{len(cases)}] Running {case_id} — {description}")

        entries_text = build_entries_text(entries)
        reporter_ctx = build_reporter_context(patient_name, reporters)

        try:
            full_summary = generate_summary(
                client, patient_name, reporter_ctx, entries_text
            )
        except Exception as e:
            print(f"  ! summary generation failed: {e}", file=sys.stderr)
            results.append({
                "id": case_id,
                "description": description,
                "has_discrepancy": ground_truth.get("has_discrepancy"),
                "discrepancy_type": ground_truth.get("discrepancy_type"),
                "scores": failure_scores(f"summary generation error: {e}"),
                "passed": False,
                "discrepancy_section": "",
                "full_summary": "",
            })
            continue

        discrepancy_section = extract_discrepancy_section(full_summary)

        try:
            judge_raw = judge_summary(client, ground_truth, discrepancy_section)
        except Exception as e:
            print(f"  ! judge call failed: {e}", file=sys.stderr)
            results.append({
                "id": case_id,
                "description": description,
                "has_discrepancy": ground_truth.get("has_discrepancy"),
                "discrepancy_type": ground_truth.get("discrepancy_type"),
                "scores": failure_scores(f"judge call error: {e}"),
                "passed": False,
                "discrepancy_section": discrepancy_section,
                "full_summary": full_summary,
            })
            continue

        try:
            scores = parse_judge_response(judge_raw)
        except Exception as e:
            print(f"  ! judge response parse failed: {e}", file=sys.stderr)
            scores = failure_scores("parse error", raw=judge_raw)

        total_score = scores.get("total", -1)
        passed = isinstance(total_score, (int, float)) and total_score >= PASS_THRESHOLD

        results.append({
            "id": case_id,
            "description": description,
            "has_discrepancy": ground_truth.get("has_discrepancy"),
            "discrepancy_type": ground_truth.get("discrepancy_type"),
            "scores": scores,
            "passed": bool(passed),
            "discrepancy_section": discrepancy_section,
            "full_summary": full_summary,
        })

    print_summary(results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"run_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote full results to {out_path}")


if __name__ == "__main__":
    main()

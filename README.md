# CareLog: Multi-Perspective Care Tracking for Dementia Patients

## The Problem

Dementia patients often give **confident but inaccurate answers** to medical questions. When a doctor asks "Have you fallen this week?" or "Have you been confused?", a patient with memory issues may genuinely believe they're fine — even when caregivers have observed otherwise.

Family members who try to correct the record in the room face an uncomfortable social dynamic: it looks like they're speaking over their loved one or being controlling. The patient feels embarrassed. The doctor gets an incomplete picture.

**CareLog solves this by creating a verified, multi-perspective record** that captures how different people — the patient, family members, nurses, and aides — each experience and report the same events.

## How It Works

CareLog is a terminal-based care logging tool powered by Claude (Anthropic's AI). It does four things:

1. **Natural language logging**: Caregivers describe what happened in plain language. No forms, no dropdowns. The AI automatically parses entries into structured categories (mood, cognition, medication, meals, sleep, incidents, etc.)

2. **Multi-perspective capture**: Each entry is tagged with who reported it and when. The patient's own self-reports are recorded alongside family and professional observations — without overwriting or contradicting anyone.

3. **Smart date extraction**: Entries like "last Tuesday Dad had a fall" are automatically filed under the correct date, not the date of reporting.

4. **AI-powered querying and summaries**: Ask questions like "Where do Dad's self-reports differ from what others observed?" and get a synthesized answer citing who said what. Generate doctor-visit-ready briefings that highlight patterns and discrepancies.

## Why This Matters

The core insight: **the gap between a patient's self-report and caregiver observations is clinically valuable information.** CareLog captures that gap without requiring anyone to contradict the patient in person.

A doctor using CareLog before an appointment can see:
- The patient reported "feeling fine, everything normal"
- Their spouse documented confusion episodes and missed medication that same day
- A nurse independently confirmed memory problems

This changes the quality of a 15-minute appointment dramatically.

## Design Principles

- **Dignity-first**: The patient is a participant, not a subject. Their perspective is recorded and valued, not overridden.
- **No wrong answers**: Conflicting reports aren't errors — they're data. The system presents all perspectives without picking sides.
- **Effortless input**: If it's harder than sending a text message, caregivers won't use it. Natural language input removes all friction.

## Example: Doctor Visit Summary

When you run the `summary` command, CareLog generates a structured briefing like this:

```
PATIENT OVERVIEW
Mark experienced significant mood and cognitive fluctuations, with reports
ranging from "sharp memory" in the morning to being "very confused" by afternoon.

NOTABLE DISCREPANCIES
Patient self-reported "feeling fine" and "everything normal," while Mom
simultaneously reported he was "extra forgetful." This suggests possible
lack of awareness of cognitive difficulties.

QUESTIONS FOR THE DOCTOR
1. What could cause such rapid cognitive fluctuations within a single day?
2. How significant is it that Mark doesn't seem aware of his memory problems?
```

## Setup

### Prerequisites
- Python 3.9+
- An Anthropic API key ([get one here](https://console.anthropic.com))

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/carelog.git
cd carelog
python3 -m venv venv
source venv/bin/activate
pip install anthropic
export ANTHROPIC_API_KEY="your-api-key"
```

### Run

```bash
python3 carelog.py
```

## Commands

| Command   | What it does |
|-----------|-------------|
| `log`     | Add a new entry. Say who you are and describe what happened in plain language. |
| `view`    | See the 5 most recent entries with parsed categories. |
| `summary` | Generate a doctor-visit-ready briefing from all entries. |
| `ask`     | Ask any question about the care log. Claude answers using only logged data. |
| `quit`    | Exit the program. |

## Architecture

```
User input (natural language)
    |
    v
Claude API (parse into structured categories + extract date)
    |
    v
JSON file storage (care_entries.json)
    |
    v
Claude API (query/summarize across all entries)
    |
    v
Synthesized answer with multi-perspective attribution
```

## What's Next

- [ ] Web interface (Streamlit) for non-technical caregivers
- [ ] RAG pipeline for handling months of entries beyond context window limits
- [ ] Pattern detection: automatic alerts for trends (increasing confusion, missed medications)
- [ ] Voice input for hands-free logging
- [ ] Multi-patient support
- [ ] Export summaries as PDF for doctor visits

## Background

This project was born from personal experience caring for a family member with dementia. The core problem — that patients can be confidently wrong about their own condition, and the social dynamics of caregiving make it hard for family to correct the record — is one that existing tools don't address.

Built as part of a 90-day AI Product Management development plan, focusing on the Anthropic SDK and practical AI applications for underserved users.

## License

MIT

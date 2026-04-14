# CareLog: Multi-Perspective Care Tracking for Dementia Patients

<!-- Screenshot: main dashboard showing care log entries from multiple reporters -->
<!-- TODO: Add screenshot of the care log view showing entries from different family members -->

## The Problem

Dementia patients often give **confident but inaccurate answers** to medical questions. When a doctor asks "Have you fallen this week?" or "Have you been confused?", a patient with memory issues may genuinely believe they're fine — even when caregivers have observed otherwise.

Family members who try to correct the record in the room face an uncomfortable social dynamic: it looks like they're speaking over their loved one or being controlling. The patient feels embarrassed. The doctor gets an incomplete picture.

**CareLog solves this by creating a verified, multi-perspective record** that captures how different people — the patient, family members, nurses, and aides — each experience and report the same events.

## How It Works

CareLog is a full-stack web application powered by Claude (Anthropic's AI). Each member of a care circle — the patient, their family, and their professional caregivers — logs in and contributes to a shared record.

### Natural Language Logging
Caregivers describe what happened in plain language. No forms, no dropdowns. Claude automatically parses entries into structured categories (mood, cognition, medication, meals, sleep, incidents, etc.) and extracts the correct date — even from entries like "last Tuesday Dad had a fall."

### Multi-Perspective Capture
Each entry is tagged with who reported it and when. The patient's own self-reports are recorded alongside family and professional observations — without overwriting or contradicting anyone.

### Patient Journal
The patient gets their own private space to record how they're feeling in their own words. Journal visibility is controlled by the patient — they can choose to share entries with their care circle or keep them private.

### Doctor Visit Summaries
Generate structured briefings for doctor appointments that highlight patterns and discrepancies across reporters. Summaries are available in two lengths: a quick paragraph for a busy appointment or a detailed section-by-section briefing.

### Doctor Visit Processing
After an appointment, paste in your notes or transcript. Claude extracts the doctor's name, date, key takeaways, and medication changes — building a searchable history of visits over time.

### AI-Powered Q&A
Ask questions like "Where do Dad's self-reports differ from what others observed?" and get a synthesized answer citing who said what and when.

## Why This Matters

The core insight: **the gap between a patient's self-report and caregiver observations is clinically valuable information.** CareLog captures that gap without requiring anyone to contradict the patient in person.

A doctor using CareLog before an appointment can see:
- The patient reported "feeling fine, everything normal"
- Their spouse documented confusion episodes and missed medication that same day
- A nurse independently confirmed memory problems

This changes the quality of a 15-minute appointment dramatically.

## Design Principles

- **Dignity-first**: The patient is a participant, not a subject. Their perspective is recorded and valued, not overridden. They control their own journal privacy.
- **No wrong answers**: Conflicting reports aren't errors — they're data. The system presents all perspectives without picking sides.
- **Effortless input**: If it's harder than sending a text message, caregivers won't use it. Natural language input removes all friction.

## Tech Stack

- **Backend**: FastAPI (Python) with Anthropic Claude API
- **Frontend**: React 19 with Vite
- **Database**: PostgreSQL via SQLAlchemy (SQLite for local dev)
- **Auth**: JWT-based authentication with role-based access (admin, caregiver, patient)
- **RAG**: ChromaDB vector database for semantic search over care entries (used in Streamlit prototype; the production web app queries the SQL database directly within Claude's context window)

## Architecture

```
React Frontend (login, care log, journal, summaries, visits, admin)
    |
    v
FastAPI Backend (JWT auth, role-based access)
    |
    ├── Claude API (parse entries, generate summaries, answer questions, process visits)
    |
    └── PostgreSQL / SQLAlchemy (entries, users, care circles, visits, changelog)
```

### Care Circle Model

Each deployment centers around a **care circle** — one patient and the people who care for them. Users have roles:

| Role | Can do |
|------|--------|
| **Patient** | Log entries, write private journal, control journal visibility, view summaries |
| **Caregiver** | Log entries, view all entries, generate summaries, ask questions, record visits |
| **Admin** | All of the above + manage users, view changelog, delete entries |

## Setup

### Prerequisites
- Python 3.9+
- Node.js 20+
- An Anthropic API key ([get one here](https://console.anthropic.com))

### Installation

```bash
git clone https://github.com/jtmcc17-boop/carelog.git
cd carelog

# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key"

# Frontend
cd frontend
npm install
```

### Run

```bash
# Terminal 1: Backend
source venv/bin/activate
uvicorn api:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

## What's Next

- [ ] Pattern detection: automatic alerts for trends (increasing confusion, missed medications)
- [ ] Voice input for hands-free logging
- [ ] Multi-care-circle support per account
- [ ] Export summaries as PDF for doctor visits
- [ ] Push notifications for care circle updates

## Background

This project was born from personal experience caring for a family member with dementia. The core problem — that patients can be confidently wrong about their own condition, and the social dynamics of caregiving make it hard for family to correct the record — is one that existing tools don't address.

Built as part of a 90-day AI Product Management development plan, focusing on the Anthropic SDK and practical AI applications for underserved users.

## License

MIT

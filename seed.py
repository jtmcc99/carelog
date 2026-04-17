"""Seed the database with two Care Circles:
  1. The real family circle (Mark)
  2. A demo circle with dummy data for presentations
"""
import sys
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import CareCircle, User, Entry, Visit
from auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── Circle 1: Mark (real family) ─────────────

mark_circle = db.query(CareCircle).filter(CareCircle.patient_name == "Mark").first()
if not mark_circle:
    mark_circle = CareCircle(name="Mark's Care Circle", patient_name="Mark")
    db.add(mark_circle)
    db.commit()
    db.refresh(mark_circle)
    print(f"Created circle: {mark_circle.name} (id={mark_circle.id})")
else:
    print(f"Circle already exists: {mark_circle.name} (id={mark_circle.id})")

admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        display_name="Jack",
        role="admin",
        relationship="son",
        circle_id=mark_circle.id,
    )
    db.add(admin)
    db.commit()
    print("Created admin user: username='admin', password='admin123', display_name='Jack'")
else:
    if not admin.circle_id:
        admin.circle_id = mark_circle.id
        db.commit()
    print("Admin user already exists.")

# ── Circle 2: Demo (Booboo) ───────────────

demo_circle = db.query(CareCircle).filter(CareCircle.patient_name == "Booboo").first()
if not demo_circle:
    demo_circle = db.query(CareCircle).filter(CareCircle.patient_name == "Margaret").first()
if not demo_circle:
    demo_circle = CareCircle(name="Booboo's Care Circle", patient_name="Booboo")
    db.add(demo_circle)
    db.commit()
    db.refresh(demo_circle)
    print(f"\nCreated demo circle: {demo_circle.name} (id={demo_circle.id})")
else:
    print(f"\nDemo circle already exists: {demo_circle.name} (id={demo_circle.id})")
    if demo_circle.patient_name == "Margaret":
        demo_circle.patient_name = "Booboo"
        demo_circle.name = "Booboo's Care Circle"
        db.commit()
        db.refresh(demo_circle)
        print("  Migrated demo circle label: Margaret → Booboo")

demo_users_data = [
    ("demo_admin", "demo123", "Sarah", "admin", "daughter"),
    ("demo_tom", "demo123", "Tom", "user", "son"),
    ("demo_linda", "demo123", "Linda", "user", "wife"),
    ("demo_nurse", "demo123", "Nurse Rachel", "user", "home health aide"),
    ("demo_booboo", "baseball", "Booboo", "patient", "patient"),
]

demo_users = {}
for uname, pwd, display, role, rel in demo_users_data:
    u = db.query(User).filter(User.username == uname).first()
    if not u:
        u = User(
            username=uname,
            password_hash=hash_password(pwd),
            display_name=display,
            role=role,
            relationship=rel,
            circle_id=demo_circle.id,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        print(f"  Created demo user: {uname} ({display}, {role})")
    else:
        print(f"  Demo user already exists: {uname}")
        if uname == "demo_booboo" and u.display_name == "Margaret":
            u.display_name = "Booboo"
            db.commit()
            db.refresh(u)
            print("  Migrated demo_booboo display name: Margaret → Booboo")
    demo_users[u.display_name] = u

legacy_reporters = (
    db.query(Entry)
    .filter(Entry.circle_id == demo_circle.id, Entry.reporter == "Margaret")
    .update({"reporter": "Booboo"}, synchronize_session=False)
)
if legacy_reporters:
    db.commit()
    print(f"  Migrated {legacy_reporters} journal row(s): reporter Margaret → Booboo")

today = datetime.now().date()

existing_entries = db.query(Entry).filter(Entry.circle_id == demo_circle.id).count()
if existing_entries > 0:
    print(f"\n  Demo entries already exist ({existing_entries}). Will backfill missing history.")
else:
    print("\n  Demo entries missing. Creating initial sample rows.")


def add_demo_entries(rows):
    existing_rows = db.query(Entry).filter(Entry.circle_id == demo_circle.id).all()
    existing_keys = {(e.timestamp, e.reporter, e.raw_text) for e in existing_rows}
    created = 0
    for row in rows:
        key = (row["timestamp"], row["reporter"], row["raw_text"])
        if key in existing_keys:
            continue
        user = demo_users[row["reporter"]]
        entry = Entry(
            circle_id=demo_circle.id,
            timestamp=row["timestamp"],
            reporter=row["reporter"],
            raw_text=row["raw_text"],
            categories=row["categories"],
            is_journal=row.get("is_journal", False),
            created_by=user.id,
        )
        db.add(entry)
        existing_keys.add(key)
        created += 1
    if created:
        db.commit()
    return created


if existing_entries == 0:
    starter_entries = [
        (-14, "Linda", "Booboo had a really good morning. She was humming in the kitchen and remembered to water her plants without reminders.", {"mood": "Good mood, humming and engaged", "cognition": "Remembered to water plants independently", "social": "Asked about grandchildren"}, False),
        (-12, "Nurse Rachel", "Vitals normal. BP 128/82. Weight stable. Slight unsteadiness when standing from a chair, so we reviewed grab bar use.", {"medication": "Medication compliance remains good", "physical_activity": "Slight unsteadiness on standing", "sleep": "Reports sleeping well"}, False),
        (-10, "Sarah", "Called Booboo this morning. She said she had breakfast, but Linda said she had not eaten yet and had forgotten.", {"cognition": "Conflicting memory about breakfast", "meals": "Needs meal reminders", "sleep": "Reported sleeping well"}, False),
        (-8, "Booboo", "Daily Check-In:\nMental: 4/7\nFeeling: Foggy, Confused\nPhysical: 5/7\nBody: Normal\nI do not remember this morning very well but I feel calmer now.", {"mood": "Foggy and confused earlier, calmer later", "cognition": "Uncertain memory of morning"}, True),
        (-5, "Tom", "Spent the afternoon at the park with Booboo. She enjoyed it but became tired after about 30 minutes.", {"mood": "Enjoyed outing", "physical_activity": "Fatigued after 30 minute walk", "social": "Positive time with family"}, False),
        (-3, "Booboo", "Daily Check-In:\nMental: 6/7\nFeeling: Happy, Hopeful\nPhysical: 5/7\nBody: Normal\nTalking with Sarah yesterday made me feel better.", {"mood": "Happy and hopeful", "social": "Positive call with Sarah"}, True),
        (-1, "Linda", "Good day overall. We did a jigsaw puzzle and she was focused. Slight time confusion around 3pm, then self-corrected.", {"cognition": "Brief time confusion with self-correction", "social": "Engaged in puzzle activity"}, False),
    ]
    starter_rows = [
        {
            "timestamp": (today + timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "reporter": reporter,
            "raw_text": raw_text,
            "categories": categories,
            "is_journal": is_journal,
        }
        for days_ago, reporter, raw_text, categories, is_journal in starter_entries
    ]
    created = add_demo_entries(starter_rows)
    print(f"  Created {created} initial demo entries.")


weekly_templates = [
    {
        "reporter": "Linda",
        "raw_text": "Weekly family note: Booboo was more engaged on {weekday}. We reviewed meals and she needed one reminder at dinner.",
        "categories": {"mood": "Generally engaged and calm", "meals": "Needed one meal reminder", "social": "Spent structured time with Linda"},
        "is_journal": False,
    },
    {
        "reporter": "Tom",
        "raw_text": "Visited Booboo and looked through old photos. She recalled several names but mixed up one timeline detail.",
        "categories": {"cognition": "Mostly accurate recall with one mixed detail", "social": "Positive family visit"},
        "is_journal": False,
    },
    {
        "reporter": "Nurse Rachel",
        "raw_text": "Home health check completed. Vitals stable, gait steady with walker, medications reviewed and on schedule.",
        "categories": {"medication": "On schedule", "physical_activity": "Steady gait with walker", "other": "Routine nursing check"},
        "is_journal": False,
    },
    {
        "reporter": "Booboo",
        "raw_text": "Daily Check-In:\nMental: 5/7\nFeeling: Calm, Hopeful\nPhysical: 5/7\nBody: Normal, Slightly Tired\nI enjoyed chatting with family and resting in the afternoon.",
        "categories": {"mood": "Calm and hopeful", "physical_activity": "Mild fatigue", "social": "Enjoyed family conversation"},
        "is_journal": True,
    },
    {
        "reporter": "Sarah",
        "raw_text": "Phone update: Booboo sounded in good spirits. She asked about the grandkids and remembered weekend plans.",
        "categories": {"mood": "Good spirits", "cognition": "Remembered plans", "social": "Engaged phone call"},
        "is_journal": False,
    },
]

history_rows = []
for days_ago in range(180, -1, -7):
    target_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    template = weekly_templates[(180 - days_ago) % len(weekly_templates)]
    history_rows.append(
        {
            "timestamp": target_date,
            "reporter": template["reporter"],
            "raw_text": template["raw_text"].format(weekday=(today - timedelta(days=days_ago)).strftime("%A")),
            "categories": template["categories"],
            "is_journal": template["is_journal"],
        }
    )

history_created = add_demo_entries(history_rows)
print(f"  Added {history_created} backfill entries covering 6 months.")


existing_visit_rows = db.query(Visit).filter(Visit.circle_id == demo_circle.id).all()
existing_visit_keys = {(v.date, v.doctor_name) for v in existing_visit_rows}
required_visits = [
    {
        "doctor_name": "Dr. Patel",
        "date": (today - timedelta(days=170)).strftime("%Y-%m-%d"),
        "transcript": "Routine checkup with Dr. Patel. Reviewed sleep quality, appetite, and caregiver notes about occasional confusion after waking.",
        "key_takeaways": "- Continue current meds\n- Keep logging morning confusion episodes\n- Maintain hydration and regular meals",
        "created_by": demo_users["Sarah"].id,
    },
    {
        "doctor_name": "Dr. Nguyen",
        "date": (today - timedelta(days=120)).strftime("%Y-%m-%d"),
        "transcript": "Orthopedic follow-up for intermittent knee stiffness. Symptoms stable with gentle exercise and rest breaks.",
        "key_takeaways": "- Continue light exercise\n- Use topical anti-inflammatory for flare-ups\n- Return if pain worsens",
        "created_by": demo_users["Linda"].id,
    },
    {
        "doctor_name": "Dr. Patel",
        "date": (today - timedelta(days=75)).strftime("%Y-%m-%d"),
        "transcript": "Memory-care follow-up. Family reports mixed days with occasional disorientation but good response to routines.",
        "key_takeaways": "- Reinforce consistent daily routine\n- No medication changes\n- Follow up in 8-10 weeks",
        "created_by": demo_users["Sarah"].id,
    },
    {
        "doctor_name": "Dr. Rivera",
        "date": (today - timedelta(days=28)).strftime("%Y-%m-%d"),
        "transcript": "Primary care check. Discussed activity level, appetite, and family concerns about late-afternoon fatigue.",
        "key_takeaways": "- Keep regular meal schedule\n- Encourage short walks with breaks\n- Monitor fatigue pattern",
        "created_by": demo_users["Tom"].id,
    },
    {
        "doctor_name": "Dr. Patel",
        "date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
        "transcript": "Recent follow-up with review of care log trends from the last month.",
        "key_takeaways": "- Continue current plan\n- Keep documenting discrepancies between self-report and caregiver observations",
        "created_by": demo_users["Sarah"].id,
    },
]

visit_created = 0
for v in required_visits:
    key = (v["date"], v["doctor_name"])
    if key in existing_visit_keys:
        continue
    visit = Visit(
        circle_id=demo_circle.id,
        doctor_name=v["doctor_name"],
        date=v["date"],
        transcript=v["transcript"],
        key_takeaways=v["key_takeaways"],
        created_by=v["created_by"],
    )
    db.add(visit)
    existing_visit_keys.add(key)
    visit_created += 1

if visit_created:
    db.commit()
print(f"  Added {visit_created} backfill doctor visits.")

print("\nDone! Login credentials:")
print("  Family circle (Mark):     admin / admin123")
print("  Demo circle (Booboo):     demo_admin / demo123")
print("  Demo family:              demo_tom / demo_linda / demo_nurse (all demo123), demo_booboo / baseball")

db.close()

"""Remove Daily Check-In entries for all patient accounts (per circle + reporter).

Run from repo root (needs DATABASE_URL reachable from your machine; Railway internal URLs will not work locally):
  python3 reset_patient_daily_checkins.py
  python3 reset_patient_daily_checkins.py --username demo_booboo

Production / QA: use admin API after Railway deploy — POST /api/admin/reset-patient-daily-checkins
with JSON {"username":"demo_booboo"} and Authorization: Bearer <demo_admin token>.
"""
import argparse

from database import SessionLocal
from models import Entry, User

PREFIX = "Daily Check-In:"


def main():
    parser = argparse.ArgumentParser(description="Remove Daily Check-In journal rows for patient(s).")
    parser.add_argument(
        "--username",
        help="Only reset this login (e.g. demo_booboo). Default: all patients.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        q = db.query(User).filter(User.role == "patient")
        if args.username:
            q = q.filter(User.username == args.username)
        patients = q.all()
        if args.username and not patients:
            print(f"No patient user found with username {args.username!r}.")
            return
        total = 0
        for p in patients:
            n = (
                db.query(Entry)
                .filter(
                    Entry.circle_id == p.circle_id,
                    Entry.reporter == p.display_name,
                    Entry.raw_text.like(f"{PREFIX}%"),
                    Entry.deleted_at.is_(None),
                )
                .delete(synchronize_session=False)
            )
            total += n
            if n:
                print(
                    f"  {p.username!r} circle {p.circle_id} reporter {p.display_name!r}: deleted {n} entries"
                )
        db.commit()
    finally:
        db.close()
    scope = f"user {args.username!r}" if args.username else "patient users"
    print(f"Done. Removed {total} daily check-in entry/entries for {scope}.")


if __name__ == "__main__":
    main()

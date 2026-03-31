"""Remove Daily Check-In entries for all patient accounts (per circle + reporter).

Run from repo root: python3 reset_patient_daily_checkins.py
"""
from database import SessionLocal
from models import Entry, User

PREFIX = "Daily Check-In:"


def main():
    db = SessionLocal()
    patients = db.query(User).filter(User.role == "patient").all()
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
            print(f"  Circle {p.circle_id} patient {p.display_name!r}: deleted {n} entries")
    db.commit()
    db.close()
    print(f"Done. Removed {total} daily check-in entry/entries for patient users.")


if __name__ == "__main__":
    main()

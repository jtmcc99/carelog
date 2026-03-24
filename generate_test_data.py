import anthropic
import json
from datetime import datetime, timedelta

client = anthropic.Anthropic()

def generate_test_data():
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system="""You generate realistic care log test data for a dementia patient named Mark.
The reporters are: Dad (Mark himself), Mom (his wife Linda), Jack (his son), Nurse Amy, Nurse Beth, PT Mike (physical therapist).

Generate 40 entries spanning from January 25, 2026 to March 24, 2026.
Mix good days and bad days. Include realistic patterns:
- Mark generally does better in the morning than afternoon
- He tends to underreport his own symptoms
- He had a fall on Feb 10
- His medication compliance is inconsistent
- He has PT twice a week
- Some days his memory is sharp, other days he's very confused
- He gets frustrated when he can't remember things
- He enjoys watching baseball and talking about his career

Each entry should be a JSON object with: timestamp (YYYY-MM-DD), reporter, raw_text (what they would naturally say), categories (parsed categories).

Return ONLY a valid JSON array of entries, no other text.""",
        messages=[
            {"role": "user", "content": "Generate the test data."}
        ]
    )

    try:
        entries = json.loads(response.content[0].text)
        return entries
    except json.JSONDecodeError:
        print("Error parsing response. Raw output:")
        print(response.content[0].text)
        return []

print("Generating test data... this may take a moment.")
new_entries = generate_test_data()

if new_entries:
    # Load existing entries
    try:
        with open("care_entries.json", "r") as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    # Combine and sort by date
    all_entries = existing + new_entries
    all_entries.sort(key=lambda x: x['timestamp'])

    with open("care_entries.json", "w") as f:
        json.dump(all_entries, f, indent=2)

    print(f"Added {len(new_entries)} entries. Total: {len(all_entries)} entries.")
    print("Entries span from", all_entries[0]['timestamp'], "to", all_entries[-1]['timestamp'])
else:
    print("No entries generated.")
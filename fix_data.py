import anthropic
import json

client = anthropic.Anthropic()

# Load the raw data that was generated
with open("care_entries.json", "r") as f:
    existing = json.load(f)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system="""Convert the care log entries below into the correct format.
Each entry's "categories" must be a dictionary where keys are category names and values are descriptions.
Use ONLY these category names: mood, cognition, medication, meals, physical_activity, sleep, incidents, social, other.
Map any non-standard categories to these (e.g., "falls" -> "incidents", "mobility" -> "physical_activity", 
"confusion" or "memory" -> "cognition", "activities" or "family_interaction" -> "social", 
"communication" -> "cognition", "safety" -> "other").
Return ONLY valid JSON array, no backticks, no other text.""",
    messages=[
        {"role": "user", "content": """Convert these entries. Here are a few to convert:
[
  {"timestamp": "2026-01-25", "reporter": "Dad", "raw_text": "Feeling pretty good today. Watched the morning news, had my coffee. Can't remember if I took my pills but Linda will know. Baseball season can't come soon enough!", "categories": ["mood", "medication", "activities"]},
  {"timestamp": "2026-01-26", "reporter": "Mom", "raw_text": "Mark forgot to take his morning medications again. I found him looking for his glasses while they were on his head. He got frustrated and snapped at me when I pointed it out. Better afternoon though - we looked through old baseball photos.", "categories": ["medication", "memory", "mood", "activities"]},
  {"timestamp": "2026-01-27", "reporter": "PT Mike", "raw_text": "Good session with Mark today. Balance exercises went well, he remembered most of the routine from last week. Talked about his pitching days - his face really lights up. Strength is maintaining well.", "categories": ["physical_therapy", "memory", "mood", "mobility"]},
  {"timestamp": "2026-01-28", "reporter": "Nurse Amy", "raw_text": "Mark seemed confused during visit. Asked me three times who I was and why I was there. Linda reports he had a restless night. Vitals stable but he appeared more disoriented than usual.", "categories": ["memory", "sleep", "confusion"]},
  {"timestamp": "2026-01-29", "reporter": "Dad", "raw_text": "Not sure what day it is. Feel okay though. Linda made pancakes I think? Or was that yesterday? Everything's a bit fuzzy but I'm not worried.", "categories": ["memory", "confusion", "mood"]},
  {"timestamp": "2026-01-30", "reporter": "Jack", "raw_text": "Visited Dad today. He recognized me right away and we had a great conversation about my work. Sharp as a tack in the morning. By evening though, he was asking where Mom was even though she was right there.", "categories": ["memory", "family_interaction", "confusion"]},
  {"timestamp": "2026-02-01", "reporter": "Mom", "raw_text": "Mark had a good morning, helped me sort through mail and even balanced the checkbook correctly. Took his pills without reminding. This afternoon he napped for 3 hours.", "categories": ["activities", "medication", "sleep", "cognitive_function"]},
  {"timestamp": "2026-02-02", "reporter": "Dad", "raw_text": "Beautiful day! Feeling strong. Think I'll go for a walk around the block. Can't wait for spring training to start - the Yankees are looking good this year.", "categories": ["mood", "activities", "mobility"]},
  {"timestamp": "2026-02-03", "reporter": "PT Mike", "raw_text": "Mark seemed more unsteady today. Had to spot him more during balance work. He kept asking about his 'game tonight' - seemed to think he had a baseball game to pitch. Gently redirected but he remained confused about the year.", "categories": ["physical_therapy", "mobility", "confusion", "memory"]},
  {"timestamp": "2026-02-04", "reporter": "Mom", "raw_text": "Difficult day. Mark woke up disoriented, didn't recognize our bedroom. Refused to take medications, said I was trying to poison him. Calmed down by afternoon but very tired.", "categories": ["confusion", "medication", "paranoia", "sleep"]},
  {"timestamp": "2026-02-05", "reporter": "Nurse Beth", "raw_text": "Mark was pleasant and cooperative during today's visit. Good recall of recent events, knew the date. Linda reports medication compliance has been better with the pill organizer system.", "categories": ["memory", "medication", "mood"]},
  {"timestamp": "2026-02-06", "reporter": "Dad", "raw_text": "Having trouble remembering words today. You know, the thing you eat cereal with... spoon! There it is. Linda's being patient with me but I can see she's worried.", "categories": ["memory", "communication", "mood"]},
  {"timestamp": "2026-02-07", "reporter": "Jack", "raw_text": "Dad was waiting for me at the window when I arrived, remembered I was coming. We watched a baseball documentary and he provided commentary like he was still calling plays. His long-term memory for baseball is incredible.", "categories": ["memory", "family_interaction", "activities"]},
  {"timestamp": "2026-02-09", "reporter": "Mom", "raw_text": "Mark seemed unsteady on his feet today, catching himself on furniture. I suggested using his walker but he refused. 'I'm not an invalid,' he said. Worried about him falling.", "categories": ["mobility", "safety", "mood"]},
  {"timestamp": "2026-02-10", "reporter": "Mom", "raw_text": "Mark fell in the bathroom this morning. He was trying to get to the toilet without his walker. No serious injuries, just bruised his hip and ego. ER checked him out, sent him home. He's very shaken up.", "categories": ["falls", "safety", "mobility", "mood"]},
  {"timestamp": "2026-02-11", "reporter": "Dad", "raw_text": "Sore from yesterday but okay. Don't know what all the fuss is about. Just lost my footing a little. These pills they gave me make me dizzy though.", "categories": ["falls", "medication", "mobility"]},
  {"timestamp": "2026-02-12", "reporter": "PT Mike", "raw_text": "Light session focusing on fall recovery confidence. Mark is hesitant to move without support now, which is actually good for safety. Reviewed bathroom safety techniques. His wife installed grab bars.", "categories": ["physical_therapy", "safety", "mobility", "falls"]},
  {"timestamp": "2026-02-13", "reporter": "Nurse Amy", "raw_text": "Post-fall assessment shows Mark is moving more cautiously. Bruising on hip is healing well. He's frustrated by the new safety restrictions but Linda is being firm about walker use.", "categories": ["falls", "mobility", "safety", "mood"]},
  {"timestamp": "2026-02-14", "reporter": "Mom", "raw_text": "Valentine's Day. Mark surprised me by remembering and had Jack pick up flowers. Such a sweet gesture. He's been using his walker consistently since the fall. Good day overall.", "categories": ["memory", "family_interaction", "safety", "mood"]},
  {"timestamp": "2026-02-16", "reporter": "Dad", "raw_text": "This walker is embarrassing but Linda insists. Feeling stronger today. Watched some spring training highlights - the boys are looking good this year. Wait, did I already say that?", "categories": ["mobility", "safety", "activities", "memory"]},
  {"timestamp": "2026-02-17", "reporter": "Jack", "raw_text": "Dad seemed depressed today. Keeps talking about being a burden, not wanting to be a 'problem.' I assured him he's not. We looked at his old baseball cards which cheered him up some.", "categories": ["mood", "family_interaction", "activities"]},
  {"timestamp": "2026-02-19", "reporter": "PT Mike", "raw_text": "Mark's confidence is slowly returning. Did well with balance exercises today. He joked about being 'too old for this' but his effort was good. Discussing home modifications with Linda.", "categories": ["physical_therapy", "mobility", "mood", "safety"]},
  {"timestamp": "2026-02-20", "reporter": "Mom", "raw_text": "Mark had a very confused episode this afternoon. Thought I was his mother and kept asking when 'the game' was. Lasted about an hour then he snapped back to normal, didn't remember the confusion.", "categories": ["confusion", "memory", "delusions"]},
  {"timestamp": "2026-02-21", "reporter": "Nurse Beth", "raw_text": "Mark was oriented and pleasant today. No recollection of yesterday's confusion per Linda's report. Discussed medication timing - some confusion episodes might be related to late-day medication wearing off.", "categories": ["memory", "medication", "confusion"]},
  {"timestamp": "2026-02-22", "reporter": "Dad", "raw_text": "Good morning! Linda made my favorite breakfast. I remember taking my pills. Looking forward to spring - want to get out in the garden this year if these old bones will let me.", "categories": ["mood", "medication", "activities", "mobility"]},
  {"timestamp": "2026-02-24", "reporter": "Mom", "raw_text": "Mark forgot Jack was coming over and was surprised to see him. But once he adjusted, they had a wonderful visit. Mark told the same story about his no-hitter three times but Jack was patient.", "categories": ["memory", "family_interaction", "repetitive_behavior"]},
  {"timestamp": "2026-02-26", "reporter": "PT Mike", "raw_text": "Excellent session today. Mark's balance is much improved since the fall. He's gained confidence with the walker and joked about 'pimping his ride' with baseball stickers. Great attitude.", "categories": ["physical_therapy", "mobility", "mood", "safety"]},
  {"timestamp": "2026-02-27", "reporter": "Dad", "raw_text": "Couldn't find my glasses this morning. Looked everywhere. Linda found them in the refrigerator - how did they get there? This is getting ridiculous. I feel like I'm losing my mind.", "categories": ["memory", "confusion", "mood"]},
  {"timestamp": "2026-02-28", "reporter": "Mom", "raw_text": "Mark was very agitated today after the glasses incident. Keeps saying 'what's wrong with me?' I try to reassure him but he's scared. Evening was better after dinner and his favorite TV show.", "categories": ["mood", "confusion", "activities"]},
  {"timestamp": "2026-03-01", "reporter": "Nurse Amy", "raw_text": "Mark expressed concerns about his memory during today's visit. We discussed normal aging vs. his condition. He understands more than he sometimes lets on. Vitals good, medication compliance improving.", "categories": ["memory", "mood", "medication", "awareness"]},
  {"timestamp": "2026-03-03", "reporter": "Jack", "raw_text": "Spring training started and Dad is glued to the TV. His baseball knowledge is still amazing - he can recall players' stats from decades ago but can't remember what he had for lunch.", "categories": ["activities", "memory", "cognitive_function"]},
  {"timestamp": "2026-03-05", "reporter": "PT Mike", "raw_text": "Mark seemed distracted during therapy today. Kept asking about 'the game tonight' and whether his uniform was clean. Had to redirect him several times but he completed the exercises.", "categories": ["physical_therapy", "confusion", "delusions"]},
  {"timestamp": "2026-03-06", "reporter": "Mom", "raw_text": "Mark woke up thinking he was late for baseball practice. Took over an hour to orient him to the present. These episodes are becoming more frequent. He napped most of the afternoon.", "categories": ["confusion", "delusions", "sleep", "time_disorientation"]},
  {"timestamp": "2026-03-07", "reporter": "Dad", "raw_text": "Feeling okay today. Watched the Yankees game - they won! Or was that yesterday? Linda keeps track of these things better than me. At least I remember to use this walker now.", "categories": ["activities", "memory", "safety"]},
  {"timestamp": "2026-03-09", "reporter": "Nurse Beth", "raw_text": "Mark had good and bad moments during today's visit. Clear and conversational at first, then became confused about why I was there. Linda reports sleep has been restless lately.", "categories": ["memory", "confusion", "sleep"]},
  {"timestamp": "2026-03-11", "reporter": "Mom", "raw_text": "Better day today. Mark helped me organize his baseball card collection. His memory for players and stats is still incredible. He was proud showing me cards I've seen a hundred times.", "categories": ["activities", "memory", "mood"]},
  {"timestamp": "2026-03-12", "reporter": "PT Mike", "raw_text": "Strong session today. Mark's mobility continues to improve. He told me about pitching in the minor leagues - such detailed stories, you can tell baseball was his life. Walking with more confidence.", "categories": ["physical_therapy", "mobility", "memory", "mood"]},
  {"timestamp": "2026-03-14", "reporter": "Jack", "raw_text": "Dad had a really sharp morning. We discussed current baseball trades and he had insightful opinions. By the time I left though, he'd asked me the same question about my job four times.", "categories": ["family_interaction", "memory", "cognitive_function", "repetitive_behavior"]},
  {"timestamp": "2026-03-16", "reporter": "Dad", "raw_text": "Can't seem to get my words out right today. You know, the thing that... the round thing you hit with the bat. Baseball! There we go. This is frustrating but I'm managing.", "categories": ["communication", "memory", "mood"]},
  {"timestamp": "2026-03-19", "reporter": "PT Mike", "raw_text": "Mark seemed tired today but pushed through exercises. Balance is good, strength maintaining. He got emotional talking about not being able to play catch with his grandson anymore.", "categories": ["physical_therapy", "mood", "family_interaction"]},
  {"timestamp": "2026-03-24", "reporter": "Mom", "raw_text": "Spring cleaning day. Mark tried to help but got overwhelmed and frustrated. Found him sitting in his chair looking at old team photos. Some days I see glimpses of the man I married, other days he feels like a stranger.", "categories": ["activities", "mood", "memory", "confusion"]}
]"""}
    ]
)

try:
    text = response.content[0].text.replace("```json", "").replace("```", "").strip()
    new_entries = json.loads(text)
    
    with open("care_entries.json", "w") as f:
        json.dump(new_entries, f, indent=2)
    
    print(f"Saved {len(new_entries)} entries.")
except Exception as e:
    print(f"Error: {e}")
    print(response.content[0].text[:500])

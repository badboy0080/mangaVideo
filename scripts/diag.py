
import sys, os
sys.path.insert(0, ".")
from mock_api import apply_mocks
apply_mocks()

from init_db import init_db, create_project, upsert_storyboard, get_storyboard
from video_prompts import parse_storyboard

with open("mock_script.txt", encoding="utf-8") as f:
    script = f.read()

print("Script length:", len(script))
parsed = parse_storyboard(script)
shot_ids = [s["id"] for s in parsed["shots"]]
print("Parsed shots:", shot_ids)
print("First shot text length:", len(parsed["shots"][0]["text"]) if parsed["shots"] else 0)

init_db()
create_project("test_pid", "test", 40)

for shot in parsed["shots"]:
    upsert_storyboard("test_pid", shot["id"], shot["id"], shot["text"], shot["refs"])
    print("Inserted", shot["id"])

result = get_storyboard("test_pid")
print("Retrieved shots:", len(result))
for r in result:
    print(" ", r["id"], ":", r["script_text"][:30])

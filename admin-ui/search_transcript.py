import json

transcript_path = "/Users/hminhnhut/.gemini/antigravity/brain/83c6b29b-d2ea-407c-b507-d38033448dd0/.system_generated/logs/transcript.jsonl"

with open(transcript_path, "r") as f:
    for line in f:
        try:
            data = json.loads(line)
            content = data.get("content", "")
            if content and ("sidebar" in content.lower() or "menu" in content.lower()):
                print(f"Step {data.get('step_index')}: User input about sidebar/menu: {content[:200]}")
        except Exception as e:
            pass

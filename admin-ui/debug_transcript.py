import json

transcript_path = "/Users/hminhnhut/.gemini/antigravity/brain/83c6b29b-d2ea-407c-b507-d38033448dd0/.system_generated/logs/transcript_full.jsonl"

calls = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            if "tool_calls" in data:
                for call in data["tool_calls"]:
                    name = call.get("name")
                    if name in ['default_api:replace_file_content', 'default_api:multi_replace_file_content']:
                        calls.append(call)
        except Exception as e:
            pass

print(f"Found {len(calls)} calls")
if calls:
    print(calls[-1])

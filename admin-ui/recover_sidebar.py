import json

transcript_path = "/Users/hminhnhut/.gemini/antigravity/brain/83c6b29b-d2ea-407c-b507-d38033448dd0/.system_generated/logs/transcript.jsonl"

with open(transcript_path, "r") as f:
    for line in f:
        try:
            data = json.loads(line)
            if "tool_calls" in data:
                for call in data["tool_calls"]:
                    if call["name"] == "replace_file_content" or call["name"] == "multi_replace_file_content":
                        args = call.get("args", {})
                        target = args.get("TargetFile", "")
                        if "page.tsx" in target:
                            if "Drawer" in args.get("ReplacementContent", "") or "Drawer" in json.dumps(args):
                                print(f"Found Drawer edit at step {data.get('step_index')}")
        except Exception as e:
            pass

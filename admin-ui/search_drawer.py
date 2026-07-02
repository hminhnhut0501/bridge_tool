import json
import re

transcript_path = "/Users/hminhnhut/.gemini/antigravity/brain/83c6b29b-d2ea-407c-b507-d38033448dd0/.system_generated/logs/transcript.jsonl"

with open(transcript_path, "r") as f:
    for line in f:
        try:
            data = json.loads(line)
            if "tool_calls" in data:
                for call in data["tool_calls"]:
                    if call["name"] == "replace_file_content" or call["name"] == "multi_replace_file_content":
                        args = call.get("args", {})
                        repl = args.get("ReplacementContent", "")
                        if "Drawer" in repl and "app/page.tsx" in args.get("TargetFile", ""):
                            print(f"Step {data.get('step_index')} replaced Drawer. Content:")
                            print(repl[:500])
        except Exception as e:
            pass

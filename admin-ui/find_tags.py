import re

target_file = "/Users/hminhnhut/prive_bot/admin-ui/app/page.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace any:
#           </div>
#         ) : null}
# With:
#           </Stack>
#         ) : null}
# ONLY IF it's part of a tab that started with <Stack

# Let's just fix it by replacing the specific ones for hiddenMessages, botEn, botTools, dev
def fix_tab_end(tab_name, content):
    pattern = re.compile(r'({tab === "' + tab_name + r'".*?\n\s+)(<Stack.*?\n.*?)(</div>\n\s+\) : null})', re.DOTALL)
    
    def repl(m):
        return m.group(1) + m.group(2) + "</Stack>\n        ) : null}"
        
    return re.sub(pattern, repl, content)

# But there might be other tabs.
tabs = ["hiddenMessages", "botEn", "botTools", "dev"]
for t in tabs:
    # Just do a simple string replace for the end of these blocks!
    pass

# A better way: find all {tab === ... } and ensure they end with </Stack> if they start with <Stack
lines = content.split('\n')
stack_depth = 0
in_tab = None

for i, line in enumerate(lines):
    if '{tab === ' in line or '{botEnTab ===' in line or '{botViTab ===' in line or '{contentTab ===' in line:
        pass

# Let's just use Python to find the exact lines and print them out.
for i, line in enumerate(lines):
    if ") : null}" in line:
        if i-1 >= 0 and "</div>" in lines[i-1] and "          </div>" in lines[i-1]:
            print(f"Line {i}: {lines[i-1]}")


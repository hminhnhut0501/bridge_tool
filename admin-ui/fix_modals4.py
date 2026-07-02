import re

target_file = "/Users/hminhnhut/prive_bot/admin-ui/app/page.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to find:
# onClose={() =
# actions={
#   <>
#     ...
#   </>
# }> ... } maxWidth="..." >

pattern = re.compile(
    r'(onClose=\{\(\) =)\n'
    r'\s*actions=\{\n\s*<>\n(.*?)\n\s*</>\n\s*\}>\s*(.*?\})([^>]*?)(>)',
    re.DOTALL
)

def replacer(match):
    actions_content = match.group(2)
    on_close_rest = match.group(3) # e.g. "setCampaignModalOpen(false)}"
    rest = match.group(4) # e.g. ' maxWidth="lg"'
    bracket = match.group(5) # '>'
    
    new_on_close = f"onClose={{() => {on_close_rest}"
    actions_prop = f"actions={{\n              <>\n{actions_content}\n              </>\n            }}"
    
    return f"{new_on_close}{rest}\n            {actions_prop}\n          {bracket}"

new_content, count = pattern.subn(replacer, content)

print(f"Replaced {count} instances.")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(new_content)

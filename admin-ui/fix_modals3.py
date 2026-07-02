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
# }> ... }
# maxWidth="..."
# >

pattern = re.compile(
    r'(onClose=\{\(\) =)\n'
    r'\s*actions=\{\n\s*<>\n(.*?)\n\s*</>\n\s*\}>([^>]*?)'
    r'(maxWidth="[^"]*?")\n\s*>',
    re.DOTALL
)

def replacer(match):
    on_close_start = match.group(1) # onClose={() =
    actions_content = match.group(2)
    on_close_end = match.group(3) # > setGroupModalOpen(false)}
    max_width = match.group(4) # maxWidth="md"
    
    # We want to change:
    # onClose={() => setGroupModalOpen(false)}
    # maxWidth="md"
    # actions={
    #   <>
    #     {actions_content}
    #   </>
    # }
    # >
    
    # But wait, match.group(3) is " setGroupModalOpen(false)}\n            "
    # match.group(1) is "onClose={() ="
    
    new_on_close = f"onClose={{() =>{on_close_end}"
    actions_prop = f"actions={{\n              <>\n{actions_content}\n              </>\n            }}"
    
    return f"{new_on_close}{max_width}\n            {actions_prop}\n          >"

new_content, count = pattern.subn(replacer, content)

print(f"Replaced {count} instances.")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(new_content)

import re

target_file = "/Users/hminhnhut/prive_bot/admin-ui/app/page.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to find MuiDialogShell WITHOUT actions prop but WITH a Stack at the end
# Group 1: <MuiDialogShell ... > (up to just before >)
# Group 2: The closing > of MuiDialogShell
# Group 3: The body (everything up to the Stack)
# Group 4: The inner content of the Stack
pattern = re.compile(
    r'(<MuiDialogShell[^>]*?)(?<!actions=\{)(>)' # MuiDialogShell tag
    r'(.*?)' # Body
    r'<Stack direction="row" spacing=\{1\} sx=\{\{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" \}\}>\s*'
    r'(.*?)\s*'
    r'</Stack>\s*'
    r'</MuiDialogShell>',
    re.DOTALL
)

def replacer(match):
    # Ensure this is not a MuiDialogShell that already has actions (though we checked somewhat)
    if 'actions=' in match.group(1):
        return match.group(0)
    
    # Extract the buttons
    buttons = match.group(4).strip()
    
    # Create the actions prop
    actions_prop = f'\n            actions={{\n              <>\n                {buttons}\n              </>\n            }}'
    
    # Reconstruct
    res = f"{match.group(1)}{actions_prop}{match.group(2)}{match.group(3)}</MuiDialogShell>"
    return res

new_content, count = pattern.subn(replacer, content)

print(f"Replaced {count} instances.")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(new_content)

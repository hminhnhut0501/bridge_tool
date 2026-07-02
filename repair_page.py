with open("admin-ui/app/page.tsx", "r") as f:
    content = f.read()

# Find where the duplication starts
marker = "import {\n  Activity,"
idx = content.find(marker, 1000) # find the second occurrence, deep in the file

if idx == -1:
    print("Could not find duplication marker.")
else:
    # Original file is the first part + the rest
    first_part = content[:idx].split(") : null}")[0] # Not exactly right. The first part is the top of the file.
    
    # Actually, the original file is just content[0:97] + content[idx:]
    # Wait, the string at the top is:
    # "use client";
    # /* eslint-disable react-hooks/exhaustive-deps, @typescript-eslint/no-unused-vars */
    # 
    # import { ...
    
    # So we just take the top part before 'import {' and prepend it to the duplicated part!
    top_part = content[:content.find(marker)]
    
    original_content = top_part + content[idx:]
    
    with open("admin-ui/app/page.tsx", "w") as f:
        f.write(original_content)
        
    print(f"Repaired file. New length: {len(original_content)}")

target_file = "/Users/hminhnhut/prive_bot/admin-ui/app/page.tsx"
head_file = "/Users/hminhnhut/prive_bot/admin-ui/page_head.tsx"

with open(head_file, "r", encoding="utf-8") as f:
    head_lines = f.readlines()

# Extract lines from page_head.tsx (0-indexed)
# 7590 to 7880 is 7589 to 7879
replacement_lines = head_lines[7589:7879]

with open(target_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find adminReplyOpen && in page.tsx
start_idx = -1
for i, line in enumerate(lines):
    if "{adminReplyOpen && adminReplyTarget ?" in line:
        start_idx = i
        break

# Find customerModalOpen && selectedCustomer in page.tsx
end_idx = -1
for i, line in enumerate(lines):
    if "{customerModalOpen && selectedCustomer ?" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing {start_idx+1} to {end_idx+1}")
    new_lines = lines[:start_idx] + replacement_lines + lines[end_idx:]
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Done!")
else:
    print("Could not find start or end index in page.tsx")

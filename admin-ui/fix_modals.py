import re

file_path = "/Users/hminhnhut/prive_bot/admin-ui/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to find MuiDialogShell blocks and extract their footers.
# We will just look for the Stack footer and move it to the MuiDialogShell opening tag.
# Actually, since the regex is complex, we'll do it manually for each component we found earlier.

replacements = [
    # groupModalOpen
    (
        r'<MuiDialogShell\n\s+open\n\s+title={`Cấu hình nhóm G\${groupNo}`}\n\s+subtitle="Tên nhóm, group ID và giá bán được lưu tập trung tại đây."\n\s+onClose={\(\) => setGroupModalOpen\(false\)}\n\s+maxWidth="md"\n\s+>',
        r'<MuiDialogShell\n            open\n            title={`Cấu hình nhóm G${groupNo}`}\n            subtitle="Tên nhóm, group ID và giá bán được lưu tập trung tại đây."\n            onClose={() => setGroupModalOpen(false)}\n            maxWidth="md"\n            actions={\n              <Stack direction="row" spacing={1}>\n                <Button variant="outlined" onClick={() => setGroupModalOpen(false)}>Đóng</Button>\n                <Button variant="outlined" color="error" onClick={removeGroupConfig} disabled={saving === "group-delete"} startIcon={<Trash2 size={16} />}>Xoá nhóm</Button>\n                <Button variant="contained" onClick={saveGroupConfig} disabled={saving === "group"} startIcon={saving === "group" ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu nhóm</Button>\n              </Stack>\n            }\n          >'
    ),
    (
        r'            </Box>\n            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>\n              <Button variant="outlined" onClick={\(\) => setGroupModalOpen\(false\)}>Đóng</Button>\n              <Button variant="outlined" color="error" onClick={removeGroupConfig} disabled={saving === "group-delete"} startIcon={<Trash2 size={16} />}>Xoá nhóm</Button>\n              <Button variant="contained" onClick={saveGroupConfig} disabled={saving === "group"} startIcon={saving === "group" \? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu nhóm</Button>\n            </Stack>\n          </MuiDialogShell>',
        r'            </Box>\n          </MuiDialogShell>'
    ),
    
    # hiddenGroupModalOpen
    (
        r'<MuiDialogShell\n\s+open\n\s+title={hiddenGroupForm.id \? `Hidden Group: \${hiddenGroupForm.id}` : "Tạo Hidden Group"}\n\s+subtitle="Thiết lập group extra ẩn, giá, hạn và điều kiện mua. Không còn phải nhập JSON thủ công."\n\s+onClose={\(\) => setHiddenGroupModalOpen\(false\)}\n\s+maxWidth="md"\n\s+>',
        r'<MuiDialogShell\n            open\n            title={hiddenGroupForm.id ? `Hidden Group: ${hiddenGroupForm.id}` : "Tạo Hidden Group"}\n            subtitle="Thiết lập group extra ẩn, giá, hạn và điều kiện mua. Không còn phải nhập JSON thủ công."\n            onClose={() => setHiddenGroupModalOpen(false)}\n            maxWidth="md"\n            actions={\n              <Stack direction="row" spacing={1}>\n                <Button variant="outlined" onClick={() => setHiddenGroupModalOpen(false)}>Đóng</Button>\n                {hiddenGroupForm.id ? <Button variant="outlined" onClick={() => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(hiddenGroupForm.name) || hiddenGroupForm.id })} startIcon={<RefreshCw size={16} />}>Tạo lại ID từ tên</Button> : null}\n                <Button variant="contained" onClick={saveHiddenGroup} disabled={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}`} startIcon={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Hidden Group</Button>\n              </Stack>\n            }\n          >'
    ),
    (
        r'            </Box>\n            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>\n              <Button variant="outlined" onClick={\(\) => setHiddenGroupModalOpen\(false\)}>Đóng</Button>\n              {hiddenGroupForm.id \? <Button variant="outlined" onClick={\(\) => setHiddenGroupForm\({ \.\.\.hiddenGroupForm, id: hiddenSlug\(hiddenGroupForm.name\) \|\| hiddenGroupForm.id }\)} startIcon={<RefreshCw size={16} />}>Tạo lại ID từ tên</Button> : null}\n              <Button variant="contained" onClick={saveHiddenGroup} disabled={saving === `hidden-group-\${hiddenGroupForm.id \|\| hiddenSlug\(hiddenGroupForm.name\) \|\| "new"}`} startIcon={saving === `hidden-group-\${hiddenGroupForm.id \|\| hiddenSlug\(hiddenGroupForm.name\) \|\| "new"}` \? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Hidden Group</Button>\n            </Stack>\n          </MuiDialogShell>',
        r'            </Box>\n          </MuiDialogShell>'
    ),
    
    # hiddenCodeModalOpen
    (
        r'<MuiDialogShell\n\s+open\n\s+title={hiddenCodeForm.code \? `Hidden Code: \${hiddenCodeForm.code}` : "Tạo Hidden Code"}\n\s+subtitle="Mã reveal catalog hidden group. Có thể giới hạn group, điều kiện và khoảng thời gian sử dụng."\n\s+onClose={\(\) => setHiddenCodeModalOpen\(false\)}\n\s+maxWidth="md"\n\s+>',
        r'<MuiDialogShell\n            open\n            title={hiddenCodeForm.code ? `Hidden Code: ${hiddenCodeForm.code}` : "Tạo Hidden Code"}\n            subtitle="Mã reveal catalog hidden group. Có thể giới hạn group, điều kiện và khoảng thời gian sử dụng."\n            onClose={() => setHiddenCodeModalOpen(false)}\n            maxWidth="md"\n            actions={\n              <Stack direction="row" spacing={1}>\n                <Button variant="outlined" onClick={() => setHiddenCodeModalOpen(false)}>Đóng</Button>\n                <Button variant="outlined" onClick={() => setHiddenCodeForm({ ...hiddenCodeForm, code: hiddenCodeSeed(hiddenCodeForm.name || hiddenCodeForm.description || "hidden-code") })} startIcon={<RefreshCw size={16} />}>Gợi ý mã từ tên</Button>\n                <Button variant="contained" onClick={saveHiddenCode} disabled={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}`} startIcon={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Hidden Code</Button>\n              </Stack>\n            }\n          >'
    ),
    (
        r'              </Box>\n            </Box>\n            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>\n              <Button variant="outlined" onClick={\(\) => setHiddenCodeModalOpen\(false\)}>Đóng</Button>\n              <Button variant="outlined" onClick={\(\) => setHiddenCodeForm\({ \.\.\.hiddenCodeForm, code: hiddenCodeSeed\(hiddenCodeForm.name \|\| hiddenCodeForm.description \|\| "hidden-code"\) }\)} startIcon={<RefreshCw size={16} />}>Gợi ý mã từ tên</Button>\n              <Button variant="contained" onClick={saveHiddenCode} disabled={saving === `hidden-code-\${\(hiddenCodeForm.code.trim\(\) \|\| hiddenCodeSeed\(hiddenCodeForm.name\)\).toUpperCase\(\)}`} startIcon={saving === `hidden-code-\${\(hiddenCodeForm.code.trim\(\) \|\| hiddenCodeSeed\(hiddenCodeForm.name\)\).toUpperCase\(\)}` \? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Hidden Code</Button>\n            </Stack>\n          </MuiDialogShell>',
        r'              </Box>\n            </Box>\n          </MuiDialogShell>'
    ),
    
    # menuModalOpen
    (
        r'<MuiDialogShell\n\s+open\n\s+title={menuForm.page_id \? `Menu: \${menuForm.page_id}` : "Thêm trang menu"}\n\s+subtitle={menuLanguage === "en" \? "Trang tiếng Anh bắt buộc kết thúc bằng _en." : "Trang tiếng Việt không dùng hậu tố _en."}\n\s+onClose={\(\) => setMenuModalOpen\(false\)}\n\s+maxWidth="md"\n\s+>',
        r'<MuiDialogShell\n            open\n            title={menuForm.page_id ? `Menu: ${menuForm.page_id}` : "Thêm trang menu"}\n            subtitle={menuLanguage === "en" ? "Trang tiếng Anh bắt buộc kết thúc bằng _en." : "Trang tiếng Việt không dùng hậu tố _en."}\n            onClose={() => setMenuModalOpen(false)}\n            maxWidth="md"\n            actions={\n              <Stack direction="row" spacing={1}>\n                <Button variant="outlined" onClick={() => setMenuModalOpen(false)}>Đóng</Button>\n                <Button variant="outlined" color="error" onClick={() => removeMenuPage()} disabled={!menuForm.page_id} startIcon={<Trash2 size={16} />}>Xoá trang</Button>\n                <Button variant="contained" onClick={saveMenuPage} startIcon={<Save size={16} />}>Lưu menu</Button>\n              </Stack>\n            }\n          >'
    ),
    (
        r'              </div>\n            </Box>\n            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>\n              <Button variant="outlined" onClick={\(\) => setMenuModalOpen\(false\)}>Đóng</Button>\n              <Button variant="outlined" color="error" onClick={\(\) => removeMenuPage\(\)} disabled={!menuForm.page_id} startIcon={<Trash2 size={16} />}>Xoá trang</Button>\n              <Button variant="contained" onClick={saveMenuPage} startIcon={<Save size={16} />}>Lưu menu</Button>\n            </Stack>\n          </MuiDialogShell>',
        r'              </div>\n            </Box>\n          </MuiDialogShell>'
    ),
]

for old, new_c in replacements:
    content = re.sub(old, new_c, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done phase 1")

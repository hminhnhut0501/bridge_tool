import re

with open("app/page.tsx", "r") as f:
    content = f.read()

# Update sidebarTabSx
new_sidebar_tab_sx = """const sidebarTabSx = {
  mt: 0.5,
  minHeight: 0,
  pr: 0.5,
  overflow: "visible",
  bgcolor: "transparent",
  backgroundColor: "transparent",
  border: 0,
  borderRadius: 0,
  boxShadow: "none",
  p: 0,
  "& .MuiTabs-flexContainer": {
    gap: 0.75,
    alignItems: "stretch",
    width: "100%",
  },
  "& .MuiTab-root": {
    justifyContent: "flex-start",
    minHeight: 42,
    px: 1.5,
    py: 0.8,
    borderRadius: "12px",
    border: "1px solid transparent",
    bgcolor: "transparent",
    width: "100%",
    boxSizing: "border-box",
    textTransform: "none",
    fontWeight: 600,
    color: "#94a3b8",
    boxShadow: "none",
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    borderLeft: "0",
    overflow: "hidden",
    position: "relative",
    zIndex: 1,
    "&.Mui-selected": {
      color: "#fff",
      bgcolor: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.3)",
      boxShadow: "0 4px 12px rgba(59, 130, 246, 0.2)",
      "&::before": {
        content: '""',
        position: "absolute",
        left: 0,
        top: "20%",
        bottom: "20%",
        width: "4px",
        borderRadius: "0 4px 4px 0",
        bgcolor: "#3b82f6",
        boxShadow: "0 0 8px rgba(59,130,246,0.6)",
      }
    },
    "&:hover:not(.Mui-selected)": {
      bgcolor: "rgba(255, 255, 255, 0.06)",
      color: "#f8fafc",
      transform: "translateX(4px)",
    },
    "& .MuiTab-iconWrapper": {
      mr: 1.5,
      mb: "0 !important",
    },
  },
  "& .MuiTabs-indicator": {
    display: "none",
  },
};"""

content = re.sub(r'const sidebarTabSx = \{.*?\s*\},?\n  "& \.MuiTabs-indicator": \{.*?\n\s*\},\n\};', new_sidebar_tab_sx, content, flags=re.DOTALL)


# Update Drawer styles
drawer_search = """"& .MuiDrawer-paper": {
            width: 280,
            boxSizing: "border-box",
            borderRight: "1px solid",
            borderColor: "divider",
            bgcolor: "#111827",
            color: "#f9fafb",
            top: "68px",
            height: "calc(100vh - 68px)",
          },"""

drawer_replace = """"& .MuiDrawer-paper": {
            width: 280,
            boxSizing: "border-box",
            borderRight: "1px solid rgba(255, 255, 255, 0.08)",
            bgcolor: "rgba(17, 24, 39, 0.65)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            color: "#f8fafc",
            top: "68px",
            height: "calc(100vh - 68px)",
          },"""

content = content.replace(drawer_search, drawer_replace)

with open("app/page.tsx", "w") as f:
    f.write(content)

print("Sidebar UI replaced successfully.")

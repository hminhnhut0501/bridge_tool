"""Create source-only release with an allowlist; no credentials or runtime state."""

import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
output = root / "data/releases/telegram-vault-0.2.0.tar.gz"
output.parent.mkdir(parents=True, exist_ok=True)
top = (
    "README.md",
    "SECURITY.md",
    "pyproject.toml",
    "requirements.lock",
    "requirements-dev.txt",
    "Dockerfile",
    "docker-compose.yml",
    ".dockerignore",
    ".gitignore",
    ".env.example",
)
folders = ("telegram_vault", "frontend", "tests", "scripts", "docs", "deploy")
excluded = {
    "node_modules",
    "dist",
    "__pycache__",
    "test-results",
    "playwright-report",
    ".ruff_cache",
}
files = [root / name for name in top]
for name in folders:
    for path in (root / name).rglob("*"):
        if not path.is_file() or excluded.intersection(path.relative_to(root).parts):
            continue
        if (
            path.suffix in (".conf", ".pyc")
            or ".session" in path.name
            or (path.name.startswith(".env") and path.name != ".env.example")
        ):
            continue
        files.append(path)
with tarfile.open(output, "w:gz") as archive:
    for path in sorted(files):
        archive.add(path, arcname="telegram-vault/" + str(path.relative_to(root)), recursive=False)
with tarfile.open(output) as archive:
    members = archive.getnames()
    if any(
        "/data/" in name or "/private/" in name or name.endswith(".session") for name in members
    ):
        raise RuntimeError("Unexpected runtime data in release")
print(f"Source release: {output} ({len(members)} files). No runtime data or credentials included.")

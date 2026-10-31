import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from zoneinfo import ZoneInfo

STATUSES = {
    "DISCOVERED",
    "QUEUED",
    "TRANSFERRING",
    "VERIFYING",
    "COMPLETED",
    "RETRY_WAIT",
    "FAILED",
    "SKIPPED",
    "CANCELLED",
}
TRANSITIONS = {
    "DISCOVERED": {"QUEUED", "SKIPPED"},
    "QUEUED": {"TRANSFERRING", "CANCELLED", "SKIPPED"},
    "TRANSFERRING": {"VERIFYING", "RETRY_WAIT", "FAILED", "CANCELLED", "SKIPPED"},
    "VERIFYING": {"TRANSFERRING", "COMPLETED", "RETRY_WAIT", "FAILED", "CANCELLED", "SKIPPED"},
    "RETRY_WAIT": {"QUEUED", "TRANSFERRING", "FAILED", "CANCELLED", "SKIPPED"},
    "FAILED": {"QUEUED", "SKIPPED", "CANCELLED"},
    "CANCELLED": {"QUEUED", "SKIPPED"},
    "SKIPPED": {"QUEUED"},
    "COMPLETED": {"FAILED"},
}


def sanitize(value, fallback="unnamed", limit=100):
    value = unicodedata.normalize("NFC", str(value))
    value = "".join(
        "_" if unicodedata.category(c).startswith("C") or c in '/\\<>:"|?*' else c for c in value
    )
    value = re.sub(r"\s+", " ", value).strip(" .")
    while len(value.encode("utf-8")) > limit:
        value = value[:-1]
    return value or fallback


@dataclass
class Message:
    chat_id: int
    message_id: int
    date: float
    topic_id: int = 0
    file_id: str = ""
    filename: str = ""
    mime_type: str = ""
    size: int = 0
    native_video: bool = False
    media_index: int = 0
    album_id: int | None = None
    album_index: int = 0
    caption: str = ""

    def eligible(self, source):
        extension = PurePosixPath(self.filename).suffix.lower().lstrip(".")
        extensions = set(source.get("extensions", "mp4,mkv,mov,webm,avi,m4v,ts").split(","))
        video = self.native_video or self.mime_type.startswith("video/") or extension in extensions
        return (
            bool(self.file_id)
            and video
            and self.size > 0
            and self.size >= source["min_size"]
            and (not source["max_size"] or self.size <= source["max_size"])
            and (not source["date_after"] or self.date >= source["date_after"])
            and (not source["date_before"] or self.date <= source["date_before"])
        )

    def remote_path(self, root, source, topic):
        date = datetime.fromtimestamp(self.date, ZoneInfo("Asia/Ho_Chi_Minh"))
        original = PurePosixPath(self.filename or "file.mp4")
        extension = (
            ("." + sanitize(original.suffix.lower().lstrip("."), fallback="", limit=16))
            if original.suffix
            else ""
        )
        stem = sanitize(original.stem, limit=100)
        caption = sanitize(self.caption, fallback="", limit=80)
        caption = re.sub(r"\s+", " ", caption)
        identity = (
            f"G{self.album_id}-{self.album_index:02d}" if self.album_id else f"M{self.message_id}"
        )
        name = f"{date:%y%m%d}_{identity}_{stem}" + (f"_{caption}" if caption else "") + extension
        components = [root, "Telegram", source["path_name"]]
        if source["forum"]:
            components.append(topic["path_name"])
        return "/".join([*components, name])

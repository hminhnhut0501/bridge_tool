import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")).resolve())
    database_path: str = ""
    app_url: str = "http://127.0.0.1:8080"
    username: str = "admin"
    password_hash: str = ""
    secure_cookie: bool = False
    telegram_mode: str = "real"
    api_id: int = 0
    api_hash: str = ""
    session_path: str = ""
    rclone_config: str = ""
    rclone_binary: str = "rclone"
    remote: str = "crypt:"
    storage_root: str = "TelegramVault_TEST"
    scan_batch_size: int = 100
    reconciliation_interval: int = 300
    max_retries: int = 6
    concurrency: int = 1
    request_pace: float = 0.5
    download_bandwidth: int = 1024 * 1024
    upload_bandwidth: int = 1024 * 1024
    verify_hash: bool = True
    file_pause_enabled: bool = True
    file_pause_min_seconds: int = 5
    file_pause_max_seconds: int = 60
    event_retention_days: int = 30
    backup_retention: int = 14
    frontend_dir: str = ""

    def __post_init__(self):
        self.data_dir = Path(self.data_dir).resolve()
        self.database_path = self.database_path or str(self.data_dir / "db/vault.sqlite3")
        self.session_path = self.session_path or str(self.data_dir / "session/account")
        self.frontend_dir = self.frontend_dir or str(
            Path(__file__).resolve().parent.parent / "frontend/dist"
        )
        if not 1 <= self.concurrency <= 4:
            raise ValueError("DOWNLOAD_CONCURRENCY must be 1..4")
        if not 1 <= self.scan_batch_size <= 1000:
            raise ValueError("SCAN_BATCH_SIZE must be 1..1000")
        if self.telegram_mode not in ("real", "mock"):
            raise ValueError("TELEGRAM_MODE must be real or mock")
        if min(self.download_bandwidth, self.upload_bandwidth, self.request_pace) < 0:
            raise ValueError("Bandwidth and pacing must be nonnegative")
        if self.reconciliation_interval < 30 or not 1 <= self.max_retries <= 20:
            raise ValueError("Invalid reconciliation interval or retry limit")
        if not 0 <= self.file_pause_min_seconds <= self.file_pause_max_seconds <= 3600:
            raise ValueError("File pause must satisfy 0 <= min <= max <= 3600 seconds")
        if self.secure_cookie and not self.app_url.startswith("https://"):
            raise ValueError("Secure cookie requires HTTPS APP_URL")
        if self.telegram_mode == "mock" and self.storage_root != "TelegramVault_TEST":
            raise ValueError("Mock mode may only write to TEST storage root")
        for directory in (
            self.data_dir,
            Path(self.database_path).parent,
            Path(self.session_path).parent,
        ):
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    @classmethod
    def from_env(cls):
        load_dotenv(override=False)
        if os.getenv("TRANSFER_MODE", "stream") != "stream":
            raise ValueError("This MVP supports TRANSFER_MODE=stream only")
        from .telegram_auth import read_credentials

        saved = read_credentials(Path(os.getenv("DATA_DIR", "data")).resolve())
        return cls(
            database_path=os.getenv("DATABASE_PATH", ""),
            app_url=os.getenv("APP_URL", "http://127.0.0.1:8080").rstrip("/"),
            username=os.getenv("AUTH_USERNAME", "admin"),
            password_hash=os.getenv("AUTH_PASSWORD_HASH", ""),
            secure_cookie=os.getenv("COOKIE_SECURE", "false").lower() == "true",
            telegram_mode=os.getenv("TELEGRAM_MODE", "real"),
            api_id=int(saved.get("api_id") or os.getenv("TELEGRAM_API_ID") or 0),
            api_hash=saved.get("api_hash") or os.getenv("TELEGRAM_API_HASH", ""),
            session_path=os.getenv("TELEGRAM_SESSION_PATH", ""),
            rclone_config=os.getenv("RCLONE_CONFIG", ""),
            rclone_binary=os.getenv("RCLONE_BINARY", "rclone"),
            remote=os.getenv("RCLONE_REMOTE", "crypt:"),
            storage_root=os.getenv("STORAGE_ROOT", "TelegramVault_TEST"),
            scan_batch_size=int(os.getenv("SCAN_BATCH_SIZE", "100")),
            reconciliation_interval=int(os.getenv("RECONCILIATION_INTERVAL", "300")),
            max_retries=int(os.getenv("MAX_RETRIES", "6")),
            concurrency=int(os.getenv("DOWNLOAD_CONCURRENCY", "1")),
            request_pace=float(os.getenv("TELEGRAM_REQUEST_PACE", "0.5")),
            download_bandwidth=int(os.getenv("MAX_DOWNLOAD_BANDWIDTH", "1048576")),
            upload_bandwidth=int(os.getenv("MAX_UPLOAD_BANDWIDTH", "1048576")),
            file_pause_enabled=os.getenv("FILE_PAUSE_ENABLED", "true").lower() == "true",
            file_pause_min_seconds=int(os.getenv("FILE_PAUSE_MIN_SECONDS", "5")),
            file_pause_max_seconds=int(os.getenv("FILE_PAUSE_MAX_SECONDS", "60")),
            verify_hash=os.getenv("VERIFY_SHA256", "true").lower() == "true",
            frontend_dir=os.getenv("FRONTEND_DIR", ""),
        )

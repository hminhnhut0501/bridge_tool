import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .models import TRANSITIONS, sanitize

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
 id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER UNIQUE NOT NULL, name TEXT NOT NULL,
 path_name TEXT NOT NULL, kind TEXT NOT NULL, forum INTEGER NOT NULL DEFAULT 0,
 enabled INTEGER NOT NULL DEFAULT 1, paused INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0,
 all_topics INTEGER NOT NULL DEFAULT 1, min_size INTEGER NOT NULL DEFAULT 0, max_size INTEGER NOT NULL DEFAULT 0,
 date_after REAL, date_before REAL, extensions TEXT NOT NULL DEFAULT 'mp4,mkv,mov,webm,avi,m4v,ts',
 scan_requested INTEGER NOT NULL DEFAULT 1, scan_target INTEGER, scan_cursor INTEGER NOT NULL DEFAULT 0,
 scanned INTEGER NOT NULL DEFAULT 0, last_scan REAL, last_reconcile REAL, scan_error TEXT, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS topics (
 source_id INTEGER NOT NULL REFERENCES sources(id), topic_id INTEGER NOT NULL, name TEXT NOT NULL,
 path_name TEXT NOT NULL, selected INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(source_id, topic_id));
CREATE TABLE IF NOT EXISTS messages (
 chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL, topic_id INTEGER NOT NULL, date REAL NOT NULL,
 PRIMARY KEY(chat_id,message_id));
CREATE TABLE IF NOT EXISTS media (
 id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL REFERENCES sources(id),
 chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL, media_index INTEGER NOT NULL DEFAULT 0,
 topic_id INTEGER NOT NULL, telegram_file_id TEXT NOT NULL, original_filename TEXT NOT NULL,
 mime_type TEXT NOT NULL, size INTEGER NOT NULL, telegram_date REAL NOT NULL, remote_path TEXT NOT NULL UNIQUE,
 plaintext_sha256 TEXT, created_at REAL NOT NULL,
 UNIQUE(chat_id,message_id,media_index,telegram_file_id));
CREATE TABLE IF NOT EXISTS jobs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, media_id INTEGER NOT NULL UNIQUE REFERENCES media(id),
 status TEXT NOT NULL CHECK(status IN ('DISCOVERED','QUEUED','TRANSFERRING','VERIFYING','COMPLETED','RETRY_WAIT','FAILED','SKIPPED','CANCELLED')),
 priority INTEGER NOT NULL DEFAULT 10, attempts INTEGER NOT NULL DEFAULT 0,
 next_attempt REAL NOT NULL DEFAULT 0, last_error TEXT, started_at REAL, completed_at REAL,
 temp_path TEXT, cancel_requested TEXT, downloaded INTEGER NOT NULL DEFAULT 0,
 uploaded INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS jobs_claim ON jobs(status,next_attempt,priority,id);
CREATE INDEX IF NOT EXISTS jobs_complete ON jobs(completed_at);
CREATE INDEX IF NOT EXISTS media_source ON media(source_id,topic_id);
CREATE INDEX IF NOT EXISTS media_identity ON media(chat_id,message_id);
CREATE TABLE IF NOT EXISTS transfers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL REFERENCES jobs(id),
 started_at REAL NOT NULL, finished_at REAL, status TEXT NOT NULL, downloaded INTEGER NOT NULL DEFAULT 0,
 uploaded INTEGER NOT NULL DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, source_id INTEGER, job_id INTEGER,
 detail TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS events_time ON events(created_at);
CREATE TABLE IF NOT EXISTS auth_sessions (
 token_hash TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS login_attempts (client TEXT PRIMARY KEY, count INTEGER NOT NULL, reset_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS stats (status TEXT PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0, bytes INTEGER NOT NULL DEFAULT 0);
CREATE TRIGGER IF NOT EXISTS stats_insert AFTER INSERT ON jobs BEGIN
 INSERT INTO stats(status,count,bytes) VALUES(NEW.status,1,(SELECT size FROM media WHERE id=NEW.media_id))
 ON CONFLICT(status) DO UPDATE SET count=count+1,bytes=bytes+excluded.bytes;
END;
CREATE TRIGGER IF NOT EXISTS stats_update AFTER UPDATE OF status ON jobs WHEN OLD.status != NEW.status BEGIN
 UPDATE stats SET count=count-1,bytes=bytes-(SELECT size FROM media WHERE id=OLD.media_id) WHERE status=OLD.status;
 INSERT INTO stats(status,count,bytes) VALUES(NEW.status,1,(SELECT size FROM media WHERE id=NEW.media_id))
 ON CONFLICT(status) DO UPDATE SET count=count+1,bytes=bytes+excluded.bytes;
END;
"""


class Database:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.connection = sqlite3.connect(path, isolation_level=None, timeout=10)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA synchronous=FULL")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 2:
            raise RuntimeError("Database schema is newer than this application")
        if version == 0:
            if self.connection.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]:
                self.backup(Path(path).with_suffix(".pre-migration.sqlite3"))
            self.connection.executescript(
                "BEGIN IMMEDIATE;" + SCHEMA + "PRAGMA user_version=1;COMMIT;"
            )

        if version < 2:
            if version == 1:
                self.backup(Path(path).with_suffix(".pre-v2.sqlite3"))
            self.connection.executescript(
                "BEGIN IMMEDIATE; ALTER TABLE sources ADD COLUMN scan_generation INTEGER NOT NULL DEFAULT 0;"
                "PRAGMA user_version=2; COMMIT;"
            )

    def rows(self, sql, parameters=()):
        return [dict(row) for row in self.connection.execute(sql, parameters).fetchall()]

    def one(self, sql, parameters=()):
        row = self.connection.execute(sql, parameters).fetchone()
        return dict(row) if row else None

    def execute(self, sql, parameters=()):
        return self.connection.execute(sql, parameters)

    @contextmanager
    def transaction(self):
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    def setting(self, key, default=None):
        row = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return json.loads(row["value"]) if row else default

    def set_setting(self, key, value):
        self.execute(
            "INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )

    def event(self, kind, detail="", source_id=None, job_id=None):
        self.execute(
            "INSERT INTO events(kind,detail,source_id,job_id,created_at) VALUES(?,?,?,?,?)",
            (kind, detail[:300], source_id, job_id, time.time()),
        )
        import logging

        logging.getLogger("telegram_vault").info(
            json.dumps(dict(event=kind, source_id=source_id, job_id=job_id))
        )

    def add_source(self, source, paused=False):
        old = self.one("SELECT * FROM sources WHERE chat_id=?", (source["chat_id"],))
        if old:
            self.execute(
                "UPDATE sources SET deleted=0,enabled=1,paused=?,scan_requested=1,name=? WHERE id=?",
                (int(paused), source["name"], old["id"]),
            )
            return old["id"]
        cursor = self.execute(
            "INSERT INTO sources(chat_id,name,path_name,kind,forum,paused,created_at) VALUES(?,?,?,?,?,?,?)",
            (
                source["chat_id"],
                source["name"],
                f"{sanitize(source['name'])}_{source['chat_id']}",
                source["kind"],
                source["forum"],
                int(paused),
                time.time(),
            ),
        )
        self.upsert_topic(
            cursor.lastrowid,
            1 if source["forum"] else 0,
            "General" if source["forum"] else "All media",
        )
        return cursor.lastrowid

    def upsert_topic(self, source_id, topic_id, name):
        source = self.one("SELECT all_topics FROM sources WHERE id=?", (source_id,))
        self.execute(
            """INSERT INTO topics(source_id,topic_id,name,path_name,selected) VALUES(?,?,?,?,?)
            ON CONFLICT(source_id,topic_id) DO UPDATE SET name=excluded.name""",
            (source_id, topic_id, name, f"{sanitize(name)}_{topic_id}", int(source["all_topics"])),
        )

    def ingest(self, source, message, root, priority=10, checkpoint=False, scan_generation=None):
        with self.transaction():
            if scan_generation is not None:
                current = self.one("SELECT * FROM sources WHERE id=?", (source["id"],))
                if (
                    not current
                    or current["scan_generation"] != scan_generation
                    or current["paused"]
                    or not current["enabled"]
                    or current["deleted"]
                ):
                    return False
                source = current
            self.execute(
                "INSERT INTO messages VALUES(?,?,?,?) ON CONFLICT(chat_id,message_id) DO UPDATE SET topic_id=excluded.topic_id,date=excluded.date",
                (message.chat_id, message.message_id, message.topic_id, message.date),
            )
            topic = self.one(
                "SELECT * FROM topics WHERE source_id=? AND topic_id=?",
                (source["id"], message.topic_id),
            )
            if not topic:
                self.upsert_topic(
                    source["id"],
                    message.topic_id,
                    "General" if message.topic_id in (0, 1) else f"Topic {message.topic_id}",
                )
                topic = self.one(
                    "SELECT * FROM topics WHERE source_id=? AND topic_id=?",
                    (source["id"], message.topic_id),
                )
            if message.eligible(source) and (source["all_topics"] or topic["selected"]):
                remote_path = message.remote_path(root, source, topic)
                # Replaced Telegram media keeps its prior backup; suffix only on collision.
                existing = self.one(
                    "SELECT telegram_file_id FROM media WHERE remote_path=?", (remote_path,)
                )
                if existing and existing["telegram_file_id"] != message.file_id:
                    import hashlib
                    from pathlib import PurePosixPath

                    path = PurePosixPath(remote_path)
                    revision = hashlib.sha256(message.file_id.encode()).hexdigest()[:10]
                    remote_path = str(path.with_name(f"{path.stem}_R{revision}{path.suffix}"))

                cursor = self.execute(
                    """INSERT OR IGNORE INTO media(source_id,chat_id,message_id,media_index,topic_id,telegram_file_id,
                    original_filename,mime_type,size,telegram_date,remote_path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        source["id"],
                        message.chat_id,
                        message.message_id,
                        message.media_index,
                        message.topic_id,
                        message.file_id,
                        message.filename,
                        message.mime_type,
                        message.size,
                        message.date,
                        remote_path,
                        time.time(),
                    ),
                )
                if cursor.rowcount:
                    self.execute(
                        "INSERT INTO jobs(media_id,status,priority,created_at) VALUES(?,'QUEUED',?,?)",
                        (cursor.lastrowid, priority, time.time()),
                    )
                    self.event("media_discovered", source_id=source["id"])
                elif priority == 100:
                    self.execute(
                        "UPDATE jobs SET priority=MAX(priority,100) WHERE media_id=(SELECT id FROM media WHERE chat_id=? AND message_id=? AND media_index=? AND telegram_file_id=?) AND status IN ('QUEUED','RETRY_WAIT')",
                        (message.chat_id, message.message_id, message.media_index, message.file_id),
                    )
            if checkpoint:
                self.execute(
                    "UPDATE sources SET scan_cursor=MAX(scan_cursor,?),scanned=scanned+1,last_scan=?,scan_error=NULL WHERE id=?",
                    (message.message_id, time.time(), source["id"]),
                )

        return True

    def job(self, job_id):
        return self.one(
            """SELECT j.*,m.source_id,m.chat_id,m.message_id,m.media_index,m.topic_id,m.telegram_file_id,
            m.original_filename,m.mime_type,m.size,m.remote_path,m.plaintext_sha256,s.name AS source_name
            FROM jobs j JOIN media m ON m.id=j.media_id JOIN sources s ON s.id=m.source_id WHERE j.id=?""",
            (job_id,),
        )

    def claim(self):
        now = time.time()
        with self.transaction():
            if self.setting("scheduler_paused", False) or self.setting("transfer_pause_until", 0) > now:
                return None
            cursor = self.setting("fair_source", -1)
            candidate = self.one(
                """SELECT j.id,m.source_id FROM jobs j JOIN media m ON m.id=j.media_id
                JOIN sources s ON s.id=m.source_id JOIN topics t ON t.source_id=s.id AND t.topic_id=m.topic_id
                WHERE j.status IN ('QUEUED','RETRY_WAIT') AND j.next_attempt<=? AND j.cancel_requested IS NULL
                AND s.enabled=1 AND s.paused=0 AND s.deleted=0 AND (s.all_topics=1 OR t.selected=1)
                AND m.size>=s.min_size AND (s.max_size=0 OR m.size<=s.max_size)
                AND (s.date_after IS NULL OR m.telegram_date>=s.date_after)
                AND (s.date_before IS NULL OR m.telegram_date<=s.date_before)
                ORDER BY j.priority DESC,CASE WHEN m.source_id>? THEN 0 ELSE 1 END,m.source_id,j.id LIMIT 1""",
                (now, cursor),
            )
            if not candidate:
                return None
            self.set_setting("fair_source", candidate["source_id"])
            self.execute(
                "UPDATE jobs SET status='TRANSFERRING',attempts=attempts+1,started_at=?,downloaded=0,uploaded=0,last_error=NULL WHERE id=?",
                (now, candidate["id"]),
            )
            self.execute(
                "INSERT INTO transfers(job_id,started_at,status) VALUES(?,?,'TRANSFERRING')",
                (candidate["id"], now),
            )
            return self.job(candidate["id"])

    def transition(self, job_id, status, **fields):
        job = self.one("SELECT status FROM jobs WHERE id=?", (job_id,))
        if not job:
            raise ValueError("Unknown job")
        if status != job["status"] and status not in TRANSITIONS[job["status"]]:
            raise ValueError(f"Invalid job transition {job['status']} → {status}")
        allowed = {
            "next_attempt",
            "last_error",
            "completed_at",
            "temp_path",
            "cancel_requested",
            "downloaded",
            "uploaded",
            "priority",
            "attempts",
        }
        if not set(fields) <= allowed:
            raise ValueError("Unsupported state field")
        values = {"status": status, **fields}
        self.execute(
            f"UPDATE jobs SET {','.join(f'{key}=?' for key in values)} WHERE id=?",
            (*values.values(), job_id),
        )
        if status not in ("TRANSFERRING", "VERIFYING"):
            self.execute(
                "UPDATE transfers SET finished_at=?,status=?,error=? WHERE job_id=? AND finished_at IS NULL",
                (time.time(), status, fields.get("last_error"), job_id),
            )

    def backup(self, destination):
        Path(destination).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with sqlite3.connect(destination) as target:
            self.connection.backup(target)

    def close(self):
        self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.connection.close()

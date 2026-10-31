import asyncio
import getpass
import json
import logging
import time

from argon2 import PasswordHasher

from .config import Config
from .database import Database


def execute(args):
    config = Config.from_env()
    if args.command == "serve":
        import uvicorn

        from .api import create_app

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        uvicorn.run(
            create_app(config),
            host=args.host,
            port=args.port,
            workers=1,
            access_log=False,
            proxy_headers=True,
            forwarded_allow_ips="127.0.0.1",
        )
        return
    db = Database(config.database_path)
    try:
        if args.command == "init-admin":
            password = getpass.getpass("New admin password (minimum 12 characters): ")
            confirm = getpass.getpass("Confirm password: ")
            if len(password) < 12 or password != confirm:
                raise SystemExit("Passwords must match and contain at least 12 characters")
            db.set_setting("admin_password_hash", PasswordHasher().hash(password))
            db.execute("DELETE FROM auth_sessions")
            print("Admin password saved as Argon2id hash. Existing web sessions revoked.")
            if config.password_hash:
                print("AUTH_PASSWORD_HASH is configured and overrides the saved hash.")
        elif args.command == "status":
            print(
                json.dumps(
                    {
                        "counts": db.rows("SELECT * FROM stats"),
                        "sources": db.rows(
                            "SELECT id,name,paused,scan_cursor,last_scan FROM sources WHERE deleted=0"
                        ),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        elif args.command == "scan":
            condition = "AND id=?" if args.source else ""
            db.execute(
                f"UPDATE sources SET scan_generation=scan_generation+1,scan_requested=1,scan_target=NULL,scan_cursor=CASE WHEN ? THEN 0 ELSE scan_cursor END WHERE deleted=0 {condition}",
                (args.full, args.source) if args.source else (args.full,),
            )
            print("Scan requested. Run serve to process it.")
        elif args.command == "retry-failed":
            db.execute(
                "UPDATE jobs SET status='QUEUED',attempts=0,next_attempt=0,priority=50,last_error=NULL WHERE status='FAILED'"
            )
            print("Failed jobs queued for retry.")
        elif args.command == "backup-db":
            target = config.data_dir / "db-backups" / f"vault-manual-{int(time.time())}.sqlite3"
            db.backup(target)
            print(f"Database snapshot saved to {target}")
        elif args.command == "reconcile":
            from .engine import Engine

            engine = Engine(config, db=db)
            # Reconcile must not race with a running service's transfers.
            import fcntl

            with open(config.database_path + ".lock", "a") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise SystemExit(
                        "Service is running. Use Storage → Reconcile in the Web UI."
                    ) from None
                print(json.dumps(asyncio.run(engine.reconcile()), indent=2))
    finally:
        db.close()

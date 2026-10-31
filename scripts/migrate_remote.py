"""One-off VPS migration: copy verified completed jobs, then switch crypt remote."""
import configparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time

from telegram_vault.database import Database

WORK = Path('/var/backups/telegram-vault/migrate-gcrypt-20261007')
WORK.mkdir(parents=True, exist_ok=True, mode=0o700)
os.umask(0o077)
ENV = Path('/etc/telegram-vault/vault.env')
ROOT_CONFIG = '/root/.config/rclone/rclone.conf'
DB_PATH = '/var/lib/telegram-vault/db/vault.sqlite3'
BASE = ['rclone', '--config', ROOT_CONFIG, '--contimeout', '20s', '--timeout', '2m', '--retries', '3']

def state(phase, **values):
    (WORK / 'status.json').write_text(json.dumps({'phase': phase, 'updated_at': time.time(), **values}, indent=2))

def service(action):
    subprocess.run(['systemctl', action, 'telegram-vault'], check=True)

def main():
    env_text = ENV.read_text()
    values = dict(line.split('=', 1) for line in env_text.splitlines() if '=' in line and not line.startswith('#'))
    old_remote = values['RCLONE_REMOTE'].strip('"\'')
    root = values.get('STORAGE_ROOT', 'TelegramVault_TEST').strip('"\'')
    if old_remote != 'gcrypt_kis:':
        raise RuntimeError('Unexpected current remote; refusing migration')
    config_path = Path(values['RCLONE_CONFIG'].strip('"\''))
    config_stat = config_path.stat()
    env_stat = ENV.stat()
    (WORK / 'vault.env.before').write_text(env_text)
    (WORK / 'rclone.conf.before').write_bytes(config_path.read_bytes())
    state('snapshot')
    service('stop')
    try:
        db = Database(DB_PATH)
        db.connection.backup(sqlite3.connect(WORK / 'vault.sqlite3'))
        rows = [dict(r) for r in db.rows("SELECT j.id,m.remote_path,m.size,m.plaintext_sha256 FROM jobs j JOIN media m ON m.id=j.media_id WHERE j.status='COMPLETED'")]
        if any(not r['plaintext_sha256'] or not r['remote_path'].startswith(root + '/') for r in rows):
            raise RuntimeError('Completed job missing digest or outside root')
        db.set_setting('storage_pause_until', time.time() + 86400)
        db.close()
        (WORK / 'manifest.json').write_text(json.dumps(rows))
        files = WORK / 'files.txt'
        files.write_text(''.join(r['remote_path'][len(root)+1:] + '\n' for r in rows))
    finally:
        service('start')
    state('copying', files=len(rows), bytes=sum(r['size'] for r in rows))
    # Multi-stream download uses encrypted disk staging, never plaintext.
    source_config = configparser.ConfigParser(interpolation=None)
    source_config.read(ROOT_CONFIG)
    if any(source_config['gcrypt'].get(k) != source_config['gcrypt_kis'].get(k)
           for k in ('password', 'password2', 'filename_encryption', 'directory_name_encryption')):
        raise RuntimeError('Raw staging requires identical crypt configuration')
    listing = json.loads(subprocess.check_output(BASE + ['lsjson', 'gcrypt:' + root,
        '--recursive', '--files-only', '--files-from-raw', str(files)]))
    sizes = {entry['Path']: entry['Size'] for entry in listing}
    def copy_row(row):
        relative = row['remote_path'][len(root)+1:]
        if relative in sizes:
            if sizes[relative] != row['size']:
                raise RuntimeError('Destination size conflict for job ' + str(row['id']))
            return
        encoded_source = subprocess.check_output(BASE + ['backend', 'encode', 'gcrypt_kis:', row['remote_path']]).decode().strip()
        encoded_dest = subprocess.check_output(BASE + ['backend', 'encode', 'gcrypt:', row['remote_path']]).decode().strip()
        if encoded_source != encoded_dest:
            raise RuntimeError('Encrypted path mapping differs')
        src = source_config['gcrypt_kis']['remote'].rstrip('/') + '/' + encoded_source
        dst = source_config['gcrypt']['remote'].rstrip('/') + '/' + encoded_dest
        staging = WORK / ('encrypted-stage-' + str(row['id']))
        with (WORK / 'rclone.log').open('a') as log:
            subprocess.run(BASE + ['copyto', src, str(staging), '--multi-thread-streams', '8',
                '--multi-thread-cutoff', '1M', '--buffer-size', '1M', '--stats', '30s',
                '--stats-one-line', '--stats-log-level', 'NOTICE'], stdout=log, stderr=log, check=True)
            subprocess.run(BASE + ['copyto', str(staging), dst, '--immutable', '--drive-chunk-size', '32M',
                '--stats', '30s', '--stats-one-line', '--stats-log-level', 'NOTICE'], stdout=log, stderr=log, check=True)
        staging.unlink()
    missing = [row for row in rows if row['remote_path'][len(root)+1:] not in sizes]
    completed = len(rows) - len(missing)
    state('copying', completed=completed, files=len(rows), mode='encrypted_staging_parallel')
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(copy_row, row) for row in missing]
        for future in as_completed(futures):
            future.result()
            completed += 1
            state('copying', completed=completed, files=len(rows), mode='encrypted_staging_parallel')
    cache = WORK / 'verify-cache'
    cache.mkdir(exist_ok=True, mode=0o700)
    verification_config = configparser.ConfigParser(interpolation=None)
    verification_config['verifycrypt'] = dict(source_config['gcrypt'])
    verification_config['verifycrypt']['remote'] = str(cache)
    verification_path = WORK / 'verify.conf'
    with verification_path.open('w') as output:
        verification_config.write(output)
    verification_path.chmod(0o600)
    def verify_row(row):
        # Download encrypted bytes in multiple ranges, then decrypt only in RAM.
        encoded = subprocess.check_output(BASE + ['backend', 'encode', 'gcrypt:', row['remote_path']]).decode().strip()
        if any(part in ('..', '') for part in encoded.split('/')):
            raise RuntimeError('Unsafe encoded path')
        local = cache / encoded
        local.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        remote = source_config['gcrypt']['remote'].rstrip('/') + '/' + encoded
        with (WORK / 'rclone.log').open('a') as log:
            subprocess.run(BASE + ['copyto', remote, str(local), '--multi-thread-streams', '8',
                '--multi-thread-cutoff', '1M', '--buffer-size', '1M'], stdout=log, stderr=log, check=True)
            proc = subprocess.Popen(['rclone', '--config', str(verification_path), 'cat',
                'verifycrypt:' + row['remote_path']], stdout=subprocess.PIPE, stderr=log)
            digest, size = hashlib.sha256(), 0
            while chunk := proc.stdout.read(524288):
                digest.update(chunk)
                size += len(chunk)
            code = proc.wait()
        if code or size != row['size'] or digest.hexdigest() != row['plaintext_sha256']:
            raise RuntimeError('Destination verification failed for job ' + str(row['id']))
        local.unlink()
    state('verifying', verified=0, files=len(rows))
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(verify_row, row) for row in rows]
        for index, future in enumerate(as_completed(futures), 1):
            future.result()
            state('verifying', verified=index, files=len(rows))
    state('switching', verified=len(rows), files=len(rows))
    service('stop')
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(config_path)
        source = configparser.ConfigParser(interpolation=None)
        source.read(ROOT_CONFIG)
        for section in ('gcrypt', 'hangcu'):
            parser[section] = dict(source[section])
        temporary = config_path.with_suffix('.migration.tmp')
        with temporary.open('w') as output:
            parser.write(output)
        os.chown(temporary, config_stat.st_uid, config_stat.st_gid)
        temporary.chmod(0o600)
        temporary.replace(config_path)
        updated = '\n'.join('RCLONE_REMOTE=gcrypt:' if line.startswith('RCLONE_REMOTE=') else line for line in env_text.splitlines()) + '\n'
        temporary_env = ENV.with_suffix('.migration.tmp')
        temporary_env.write_text(updated)
        os.chown(temporary_env, env_stat.st_uid, env_stat.st_gid)
        temporary_env.chmod(env_stat.st_mode & 0o777)
        temporary_env.replace(ENV)
        db = Database(DB_PATH)
        with db.transaction():
            db.execute("UPDATE jobs SET temp_path=NULL,downloaded=0,uploaded=0 WHERE status!='COMPLETED'")
            for row in db.rows("SELECT id FROM jobs WHERE status IN ('FAILED','RETRY_WAIT') AND last_error IN ('google_rate_limit','BrokenPipeError') AND cancel_requested IS NULL"):
                db.transition(row['id'], 'QUEUED', attempts=0, next_attempt=0, last_error=None)
            db.set_setting('storage_pause_until', 0)
            db.event('storage_remote_migrated', 'gcrypt_kis to gcrypt; completed backups verified; originals retained')
        db.close()
    except Exception:
        ENV.write_text(env_text)
        config_path.write_bytes((WORK / 'rclone.conf.before').read_bytes())
        raise
    finally:
        service('start')
    state('complete', files=len(rows), verified=len(rows), bytes=sum(r['size'] for r in rows), remote='gcrypt:')

try:
    main()
except Exception as error:
    state('failed', error=type(error).__name__, detail=str(error)[:200])
    raise

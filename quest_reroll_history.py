"""Human-readable quest reroll audit trail, retained for the last 48 hours."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
import time

from runtime_paths import runtime_file

RETENTION = timedelta(hours=48)
_LOCK = threading.RLock()
_last_cleanup: dict[Path, float] = {}


def history_path() -> Path:
    # Resolve at call time so test runners and MTGA_RUNTIME_DIR stay isolated.
    return runtime_file('logs', 'quest_rerolls.txt')


def _utc(now: datetime | None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError('Quest history timestamps must include a timezone')
    return value.astimezone(timezone.utc)


def _retained(path: Path, now: datetime) -> list[str]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            timestamp = datetime.fromisoformat(line.split(' | ', 1)[0])
            if timestamp.tzinfo is not None and now - RETENTION <= timestamp <= now:
                rows.append(line)
        except ValueError:
            # Incomplete or undated entries cannot satisfy a retention policy.
            continue
    return rows


def _replace(path: Path, rows: list[str]) -> None:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as f:
            temp_path = Path(f.name)
            f.write(''.join(line + '\n' for line in rows))
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def maintain_history(*, now: datetime | None = None, force: bool = False) -> Path:
    """Prune at startup and at most once a minute during idle UI polling."""
    path = history_path()
    with _LOCK:
        tick = time.monotonic()
        if not force and now is None and tick - _last_cleanup.get(path, float('-inf')) < 60:
            return path
        current = _utc(now)
        _replace(path, _retained(path, current))
        _last_cleanup[path] = tick
    return path


def _quest_summary(snapshot: dict | None) -> list[dict] | None:
    if snapshot is None:
        return None
    result = []
    for quest in snapshot.get('quests', []):
        if not isinstance(quest, dict):
            continue
        chest = quest.get('chestDescription') or {}
        params = (chest.get('locParams') or {}) if isinstance(chest, dict) else {}
        result.append({
            'id': quest.get('questId'), 'objective': quest.get('locKey'),
            'progress': quest.get('endingProgress'), 'goal': quest.get('goal'),
            'gold': params.get('number1') if isinstance(params, dict) else None,
        })
    return result


def record_event(outcome: str, *, account: str = '', detail: str = '',
                 before: dict | None = None, after: dict | None = None,
                 now: datetime | None = None) -> Path:
    """Append an outcome plus quest identities/rewards, never account credentials."""
    current = _utc(now)
    payload = {'account': account or 'unknown', 'outcome': outcome, 'detail': detail,
               'before': _quest_summary(before), 'after': _quest_summary(after)}
    if before is not None:
        payload['canSwap_before'] = before.get('canSwap')
    if after is not None:
        payload['canSwap_after'] = after.get('canSwap')
    # JSON escaping keeps names/newlines on one physical, timestamped text line.
    line = current.isoformat(timespec='seconds') + ' | ' + json.dumps(payload, ensure_ascii=False)
    path = history_path()
    with _LOCK:
        rows = _retained(path, current)
        rows.append(line)
        _replace(path, rows)
        _last_cleanup[path] = time.monotonic()
    return path

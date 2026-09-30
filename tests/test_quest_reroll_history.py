"""Retention and persistence tests using only temporary audit files."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import quest_reroll_history as history


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = patch.dict(os.environ, MTGA_RUNTIME_DIR=self.tmp.name)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.now = datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)

    def read(self):
        return [json.loads(row.split(' | ', 1)[1])
                for row in history.history_path().read_text(encoding='utf-8').splitlines()]

    def test_append_prunes_only_entries_older_than_48_hours(self):
        history.record_event('expired', now=self.now - timedelta(hours=48, seconds=1))
        history.record_event('boundary', now=self.now - timedelta(hours=48))
        history.record_event('yesterday', now=self.now - timedelta(hours=24))
        history.record_event('today', now=self.now)
        self.assertEqual([r['outcome'] for r in self.read()], ['boundary', 'yesterday', 'today'])

    def test_idle_cleanup_prunes_without_a_new_reroll_and_creates_empty_file(self):
        path = history.maintain_history(now=self.now)
        self.assertEqual(path.read_text(encoding='utf-8'), '')
        history.record_event('verified', now=self.now)
        history.maintain_history(now=self.now + timedelta(hours=48, seconds=1))
        self.assertEqual(self.read(), [])

    def test_restart_cleanup_uses_persisted_timestamps_not_memory(self):
        history.record_event('expired', now=self.now - timedelta(hours=47))
        history._last_cleanup.clear()
        history.maintain_history(now=self.now + timedelta(hours=2), force=True)
        self.assertEqual(self.read(), [])

    def test_only_quest_fields_are_written_and_newlines_are_escaped(self):
        snapshot = {'canSwap': True, 'pw': 'secret', 'email': 'private', 'quests': [
            {'questId': 'q1', 'locKey': 'Cast spells', 'goal': 20, 'endingProgress': 3,
             'chestDescription': {'locParams': {'number1': 500}}, 'token': 'secret'}]}
        history.record_event('submitted', account='Name\nAnother line', before=snapshot, now=self.now)
        raw = history.history_path().read_text(encoding='utf-8')
        self.assertEqual(len(raw.splitlines()), 1)
        self.assertNotIn('secret', raw)
        self.assertNotIn('private', raw)
        self.assertEqual(self.read()[0]['before'][0]['gold'], 500)

    def test_atomic_replace_failure_keeps_existing_file(self):
        path = history.record_event('first', now=self.now)
        original = path.read_bytes()
        with patch('quest_reroll_history.os.replace', side_effect=PermissionError('locked')):
            with self.assertRaises(PermissionError):
                history.record_event('second', now=self.now)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(list(path.parent.glob('*.tmp')), [])

    def test_concurrent_writers_preserve_all_events(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda i: history.record_event(str(i), now=self.now), range(20)))
        self.assertEqual({r['outcome'] for r in self.read()}, {str(i) for i in range(20)})

    def test_timezone_boundary_and_malformed_line_cleanup(self):
        offset = timezone(timedelta(hours=2))
        history.record_event('same instant', now=self.now.astimezone(offset))
        path = history.history_path()
        with path.open('a', encoding='utf-8') as f:
            f.write('incomplete line\n')
        history.maintain_history(now=self.now)
        self.assertEqual(len(self.read()), 1)
        self.assertTrue(path.read_text(encoding='utf-8').startswith('2026-09-29T10:00:00+00:00'))

    def test_runtime_path_is_resolved_per_call(self):
        first = history.record_event('first', now=self.now)
        with patch.dict(os.environ, MTGA_RUNTIME_DIR=str(Path(self.tmp.name) / 'other')):
            second = history.record_event('second', now=self.now)
            self.assertNotEqual(first, second)
            self.assertEqual(self.read()[0]['outcome'], 'second')


if __name__ == '__main__':
    unittest.main()

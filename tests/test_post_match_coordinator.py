"""Post-match timer invalidation and exactly-once handoff are deterministic."""
import threading
import time
import unittest
from unittest import mock

from navigation.post_match import PostMatchCoordinator
from Controller.MTGAController.Controller import Controller
import runtime_status
from state.state_machine import BotState


class _ManualTimer:
    def __init__(self, delay, callback):
        self.delay = delay
        self.callback = callback
        self.cancelled = False
        self.daemon = False
        self.started = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True

    def fire(self):
        self.callback()


class PostMatchCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.timers = []
        self.coordinator = PostMatchCoordinator(
            timer_factory=lambda delay, callback: self._new_timer(delay, callback)
        )

    def _new_timer(self, delay, callback):
        timer = _ManualTimer(delay, callback)
        self.timers.append(timer)
        return timer

    def test_replacing_a_callback_cancels_old_timer_and_runs_once(self):
        seen = []
        cycle = self.coordinator.begin()
        self.coordinator.schedule(cycle, "handoff", 4, lambda: seen.append("old"))
        old = self.timers[-1]
        self.coordinator.schedule(cycle, "handoff", 2, lambda: seen.append("new"))
        current = self.timers[-1]
        self.assertTrue(old.cancelled)
        old.fire()
        current.fire()
        current.fire()
        self.assertEqual(seen, ["new"])

    def test_new_match_invalidates_every_callback_from_old_cycle(self):
        seen = []
        old_cycle = self.coordinator.begin()
        self.coordinator.schedule(old_cycle, "dismiss", 6, lambda: seen.append("old"))
        old = self.timers[-1]
        new_cycle = self.coordinator.begin()
        old.fire()
        self.assertTrue(old.cancelled)
        self.assertFalse(self.coordinator.current(old_cycle))
        self.assertTrue(self.coordinator.current(new_cycle))
        self.assertEqual(seen, [])

    def test_schedule_rejects_invalidated_generation(self):
        cycle = self.coordinator.begin()
        self.coordinator.invalidate()
        self.assertFalse(self.coordinator.schedule(cycle, "handoff", 0, lambda: None))

    def test_post_match_handoff_is_debounced_until_ui_is_stable(self):
        c = Controller.__new__(Controller)
        c._stop_requested = False
        c._account_switch_in_progress = False
        c._account_switch_pending = False
        c._account_switch_due = lambda: False
        c._queue_after_login = False
        c._post_match_coordinator = PostMatchCoordinator(timer_factory=self._new_timer)
        c._post_match_cycle = c._post_match_coordinator.begin()
        c._post_match_handoff_started = False
        c._post_match_ready_streak = 0
        c._post_match_ready_ts = time.time() - 3
        c._post_match_min_delay_sec = 2
        c._post_match_main_nav_loaded = True
        c._queue_spam_thread = None
        c._stop_queue_spam = False
        c._get_state_from_log = mock.Mock(return_value=BotState.HOME)
        c.start_queueing = mock.Mock()
        with mock.patch.object(runtime_status, "set_mode"), \
             mock.patch.object(runtime_status, "set_intentional_wait"), \
             mock.patch.object(runtime_status, "clear_intentional_wait"):
            c._maybe_post_match_action()
            self.assertEqual(c.start_queueing.call_count, 0)
            self.assertEqual(self.timers[-1].delay, 0.45)
            c._maybe_post_match_action()
            c._maybe_post_match_action()
        c.start_queueing.assert_called_once_with()
        self.assertTrue(c._post_match_handoff_started)

    def test_stop_invalidates_a_pending_post_match_handoff(self):
        c = Controller.__new__(Controller)
        c._post_match_coordinator = PostMatchCoordinator(timer_factory=self._new_timer)
        cycle = c._begin_post_match_cycle()
        c._post_match_ready_ts = time.time() - 3
        timer = c._post_match_coordinator
        c._invalidate_post_match_cycle("Stop")
        self.assertFalse(timer.current(cycle))
        self.assertIsNone(c._post_match_cycle)


if __name__ == "__main__":
    unittest.main()

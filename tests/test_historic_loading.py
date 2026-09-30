"""The 2026-09-28 Historic incident: Home in the log, server spinner on screen."""
import unittest
from unittest.mock import Mock, patch

from actions.actions import ActionResult
from Controller.MTGAController.Controller import Controller
from state.state_machine import BotState


class HistoricLoadingTests(unittest.TestCase):
    def setUp(self):
        # No Controller initialization, desktop capture, or physical input.
        self.c = Controller.__new__(Controller)
        self.c._stop_requested = False
        self.c._get_state_from_log = Mock(return_value=BotState.HOME)
        self.c._ensure_arena_region = Mock(return_value=None)
        self.c._write_nav_debug_bundle = Mock()
        self.c._click_abs = Mock()
        self.c._vision = Mock()
        self.c._queue_button_rel = (1733, 1007)
        self.c._navigation_verify_failures = 0
        self.now = 0.0
        def sleep(seconds):
            self.now += seconds
        self.sleep = patch('Controller.MTGAController.Controller.time.sleep', side_effect=sleep)
        self.monotonic = patch('Controller.MTGAController.Controller.time.monotonic', side_effect=lambda: self.now)
        self.status = patch('Controller.MTGAController.Controller.runtime_status.set_startup_phase')
        for p in (self.sleep, self.monotonic, self.status):
            p.start()
            self.addCleanup(p.stop)

    def test_home_log_does_not_authorize_clicks_until_visible_arena_returns(self):
        arena = (277, 167, 1366, 768)
        self.c._ensure_arena_region.side_effect = [None, None, arena]
        with patch('Controller.MTGAController.Controller.run_action', return_value=ActionResult(True, 'ok')) as action:
            self.assertTrue(self.c._run_post_login_navigation_oob())
        self.assertEqual(self.now, 1.0)
        self.assertEqual(self.c._ensure_arena_region.call_count, 3)
        self.assertTrue(all(call.kwargs['force_reacquire'] for call in self.c._ensure_arena_region.call_args_list))
        self.assertEqual([call.args[0].name for call in action.call_args_list], [
            'POST_LOGIN_PLAY', 'POST_LOGIN_FIND_MATCH', 'POST_LOGIN_PLAY_SUBTAB',
            'POST_LOGIN_HIST_PLAY', 'POST_LOGIN_MY_DECKS'])
        self.c._click_abs.assert_not_called()

    def test_loading_timeout_never_runs_navigation_or_uses_cached_coordinates(self):
        self.c._POST_LOGIN_READY_TIMEOUT = 1.0
        self.c._arena_region = (277, 167, 1366, 768)
        with patch('Controller.MTGAController.Controller.run_action') as action:
            self.assertFalse(self.c._run_post_login_navigation_oob())
        self.assertEqual(self.now, 1.0)
        action.assert_not_called()
        self.c._click_abs.assert_not_called()
        self.c._write_nav_debug_bundle.assert_called_once()

    def test_stop_cancels_wait_without_clicking(self):
        def stop(**kwargs):
            self.c._stop_requested = True
            return None
        self.c._ensure_arena_region.side_effect = stop
        self.assertIsNone(self.c._wait_for_post_login_arena())
        self.c._click_abs.assert_not_called()

    def test_stop_during_successful_capture_does_not_start_navigation(self):
        def stop(**kwargs):
            self.c._stop_requested = True
            return (277, 167, 1366, 768)
        self.c._ensure_arena_region.side_effect = stop
        with patch('Controller.MTGAController.Controller.run_action') as action:
            self.assertFalse(self.c._run_post_login_navigation_oob())
        action.assert_not_called()

    def test_match_ownership_blocks_the_wait_and_all_capture(self):
        for state in (BotState.IN_GAME, BotState.FIND_MATCH):
            self.c._get_state_from_log.return_value = state
            self.assertIsNone(self.c._wait_for_post_login_arena())
        self.c._ensure_arena_region.assert_not_called()


if __name__ == '__main__':
    unittest.main()

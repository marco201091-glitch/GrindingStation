"""End-screen clicks must leave Arena time to finish loading Home."""

import unittest
from unittest import mock

from Controller.MTGAController.Controller import Controller
from state.state_machine import BotState


class PostMatchHomeTransitionTests(unittest.TestCase):
    def test_main_nav_event_ends_click_retries_after_ten_second_grace(self):
        controller = Controller.__new__(Controller)
        controller._stop_requested = False
        controller._post_match_main_nav_loaded = False
        controller._match_end_dismissed = False
        controller._matches_since_quest_refresh = 0
        controller._post_match_delay_sec = 30
        controller._queue_ready = False
        controller._win_counted_this_match = False
        controller._Controller__last_match_won = False
        controller._Controller__match_end_callback = None
        controller._get_state_from_log = mock.Mock(return_value=BotState.IN_GAME)
        controller._get_ui_action_arena_region = mock.Mock(return_value=(100, 50, 1920, 1080))
        controller._arena_region_provider = mock.Mock()
        controller._arena_region_provider.detect.return_value = mock.Mock(ok=False)
        controller.input = mock.Mock()
        controller._update_gold_from_inventory = mock.Mock()
        controller._note_match_finished = mock.Mock()

        def advance_clock(seconds):
            if seconds == 10.0:
                controller._post_match_main_nav_loaded = True

        with mock.patch("Controller.MTGAController.Controller.focus_mtga_window", return_value=False), \
             mock.patch("Controller.MTGAController.Controller.time.sleep", side_effect=advance_clock) as sleep, \
             mock.patch("Controller.MTGAController.Controller.threading.Timer"):
            controller.dismiss_end_screen()

        controller.input.left_click.assert_called_once_with(1)
        controller.input.move_abs.assert_called_once_with(1060, 1054)
        sleep.assert_any_call(10.0)
        self.assertTrue(controller._match_end_dismissed)
        controller._note_match_finished.assert_called_once()

    def test_main_nav_event_is_fresh_for_each_match(self):
        controller = Controller.__new__(Controller)
        controller._post_match_main_nav_loaded = True
        controller._queue_ready = False
        controller._handle_main_nav_loaded()
        self.assertTrue(controller._post_match_main_nav_loaded)
        controller._post_match_main_nav_loaded = False
        controller._arena_region_provider = mock.Mock()
        controller._arena_region_provider.detect.return_value = mock.Mock(ok=False)
        controller._get_state_from_log = mock.Mock(return_value=BotState.IN_GAME)
        self.assertFalse(controller._match_end_screen_cleared())

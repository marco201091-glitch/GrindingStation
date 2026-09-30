"""Reconnect prompt recovery with no access to the real desktop."""

import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

from Controller.MTGAController.Controller import Controller
from state.state_machine import BotState
from vision.vision import VisionEngine
from vision.window_locator import WindowRect


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "assert" / "reconnect_button.png"


class ReconnectOverlayTests(unittest.TestCase):
    def make_controller(self, width, height, *, visible=True, retry_label=False):
        controller = Controller.__new__(Controller)
        controller._stop_requested = False
        controller._get_state_from_log = mock.Mock(return_value=BotState.IN_GAME)
        controller._get_state_from_log = lambda: __import__("state.state_machine", fromlist=["BotState"]).BotState.IN_GAME
        controller._reconnect_retry_after = 0.0
        controller._historic_selection_key = "old-selection"
        controller._arena_region_provider = mock.Mock()
        controller._arena_region_provider._find_mtga_window_rect.return_value = WindowRect(200, 100, width, height)
        controller._vision = VisionEngine()
        controller._locate_image_center_in_scaled_arena_region = mock.Mock(side_effect=AssertionError("desktop probe"))
        controller._click_image_in_scaled_arena_region = mock.Mock(side_effect=AssertionError("desktop click"))
        controller._click_abs = mock.Mock()
        reference = np.zeros((460, 1220, 3), dtype=np.uint8)
        if visible:
            button = cv2.imread(str(TEMPLATE))
            if retry_label:
                bh, bw = button.shape[:2]
                cv2.rectangle(button, (int(bw * 0.18), int(bh * 0.30)),
                              (int(bw * 0.82), int(bh * 0.72)), (0, 0, 0), -1)
                cv2.putText(button, "Retry", (int(bw * 0.36), int(bh * 0.68)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1,
                            cv2.LINE_AA)
            bh, bw = button.shape[:2]
            reference[230:230 + bh, 465:465 + bw] = button
        arena = (200, 100, width, height)
        roi = controller._scale_base_region_to_arena(arena, (350, 330, 1220, 460))
        screen_roi = cv2.resize(reference, (roi[2], roi[3]))
        controller._vision.capture = mock.Mock(return_value=screen_roi)
        return controller

    def test_clicks_reconnect_once_at_both_arena_sizes(self):
        for width, height in ((1920, 1080), (1366, 768)):
            with self.subTest(size=(width, height)):
                controller = self.make_controller(width, height)
                with mock.patch("Controller.MTGAController.Controller.focus_mtga_window", return_value=True), \
                     mock.patch("Controller.MTGAController.Controller.time.time", return_value=100.0):
                    self.assertTrue(controller._handle_disconnect_overlay())
                    self.assertTrue(controller._handle_disconnect_overlay())
                controller._click_abs.assert_called_once()
                x, y, tag = controller._click_abs.call_args.args
                self.assertEqual(tag, "RECONNECT")
                self.assertAlmostEqual(x, 200 + round(960 * width / 1920), delta=3)
                self.assertAlmostEqual(y, 100 + round(594 * height / 1080), delta=3)
                self.assertIsNone(controller._historic_selection_key)

    def test_clicks_retry_label_using_the_disconnect_button_outline(self):
        for width, height in ((1920, 1080), (1366, 768)):
            with self.subTest(size=(width, height)):
                controller = self.make_controller(width, height, retry_label=True)
                with mock.patch("Controller.MTGAController.Controller.focus_mtga_window", return_value=True), \
                     mock.patch("Controller.MTGAController.Controller.time.time", return_value=100.0):
                    self.assertTrue(controller._handle_disconnect_overlay())
                controller._click_abs.assert_called_once()
                self.assertEqual(controller._click_abs.call_args.args[2], "RETRY")
                self.assertIsNone(controller._historic_selection_key)

    def test_no_prompt_means_no_click(self):
        controller = self.make_controller(1920, 1080, visible=False)
        with mock.patch("Controller.MTGAController.Controller.focus_mtga_window") as focus:
            self.assertFalse(controller._handle_disconnect_overlay())
        focus.assert_not_called()
        controller._click_abs.assert_not_called()

    def test_no_live_window_means_no_click_even_with_old_selection(self):
        controller = self.make_controller(1920, 1080)
        controller._arena_region_provider._find_mtga_window_rect.return_value = None
        self.assertFalse(controller._handle_disconnect_overlay())
        controller._click_abs.assert_not_called()

    def test_unfocused_arena_is_never_clicked(self):
        controller = self.make_controller(1920, 1080)
        with mock.patch("Controller.MTGAController.Controller.focus_mtga_window", return_value=False):
            self.assertTrue(controller._handle_disconnect_overlay())
        controller._click_abs.assert_not_called()

    def test_queue_checks_disconnect_before_normal_navigation(self):
        controller = Controller.__new__(Controller)
        controller._stop_queue_spam = False
        controller._handle_disconnect_overlay = mock.Mock(return_value=True)
        controller.start_game_from_home_screen = mock.Mock()

        def finish_tick(_seconds):
            controller._stop_queue_spam = True

        with mock.patch("Controller.MTGAController.Controller.time.sleep", side_effect=finish_tick):
            controller._queue_spam_loop()
        controller._handle_disconnect_overlay.assert_called_once()
        controller.start_game_from_home_screen.assert_not_called()

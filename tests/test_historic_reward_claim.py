"""Historic reward Claim is guarded by its title and tested without desktop input."""

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


class HistoricRewardClaimTests(unittest.TestCase):
    def make_controller(self, width, height, *, header_present=True):
        controller = Controller.__new__(Controller)
        controller._game_mode = "historic"
        controller._stop_requested = False
        controller._historic_reward_claim_retry_after = 0.0
        controller._historic_selection_key = "previous"
        controller._historic_selection_retry_ts = 100.0
        controller._historic_selection_failures = 4
        controller._get_state_from_log = mock.Mock(return_value=BotState.HOME)
        controller._arena_region_provider = mock.Mock()
        controller._arena_region_provider._find_mtga_window_rect.return_value = WindowRect(277, 167, width, height)
        controller._vision = VisionEngine()
        controller._click_abs = mock.Mock()
        reference = np.zeros((768, 1366, 3), dtype=np.uint8)
        title = cv2.imread(str(ROOT / "assets" / "assert" / "reward_header.png"))
        if header_present:
            reference[57:57 + title.shape[0], 598:598 + title.shape[1]] = title
        claim = cv2.imread(str(ROOT / "Buttons" / "claim.png"))
        claim = cv2.resize(claim, (round(claim.shape[1] * 0.7), round(claim.shape[0] * 0.7)))
        reference[688:688 + claim.shape[0], 1134:1134 + claim.shape[1]] = claim
        resized = cv2.resize(reference, (width, height))
        full_screen = np.zeros((height + 167, width + 277, 3), dtype=np.uint8)
        full_screen[167:167 + height, 277:277 + width] = resized
        controller._vision.capture = lambda region: full_screen[
            region[1]:region[1] + region[3], region[0]:region[0] + region[2]
        ]
        return controller

    def test_claim_works_at_both_arena_sizes_and_waits_before_retry(self):
        for width, height in ((1366, 768), (1920, 1080)):
            with self.subTest(size=(width, height)):
                controller = self.make_controller(width, height)
                clock = [100.0]
                def tick():
                    value = clock[0]
                    clock[0] += 0.4
                    return value
                with mock.patch("Controller.MTGAController.Controller.focus_mtga_window", return_value=True), \
                     mock.patch("Controller.MTGAController.Controller.time.time", side_effect=tick):
                    self.assertTrue(controller._dismiss_historic_reward_popup())
                    self.assertTrue(controller._dismiss_historic_reward_popup())
                controller._click_abs.assert_called_once()
                x, y, tag = controller._click_abs.call_args.args
                self.assertEqual(tag, "HISTORIC_REWARD_CLAIM")
                self.assertAlmostEqual(x, 277 + round(1234 * width / 1366), delta=3)
                self.assertAlmostEqual(y, 167 + round(716 * height / 768), delta=3)
                self.assertIsNone(controller._historic_selection_key)
                self.assertEqual(controller._historic_selection_retry_ts, 0.0)

    def test_claim_without_reward_title_is_not_clicked(self):
        controller = self.make_controller(1366, 768, header_present=False)
        with mock.patch("Controller.MTGAController.Controller.focus_mtga_window") as focus:
            self.assertFalse(controller._dismiss_historic_reward_popup())
        focus.assert_not_called()
        controller._click_abs.assert_not_called()

    def test_in_game_never_probes_reward(self):
        controller = self.make_controller(1366, 768)
        controller._get_state_from_log.return_value = BotState.IN_GAME
        self.assertFalse(controller._dismiss_historic_reward_popup())
        controller._click_abs.assert_not_called()

    def test_queue_claims_reward_before_historic_navigation(self):
        controller = Controller.__new__(Controller)
        controller._stop_queue_spam = False
        controller._handle_disconnect_overlay = mock.Mock(return_value=False)
        controller._dismiss_historic_reward_popup = mock.Mock(return_value=True)
        controller.start_game_from_home_screen = mock.Mock()

        def finish_tick(_seconds):
            controller._stop_queue_spam = True

        with mock.patch("Controller.MTGAController.Controller.time.sleep", side_effect=finish_tick):
            controller._queue_spam_loop()
        controller._dismiss_historic_reward_popup.assert_called_once()
        controller.start_game_from_home_screen.assert_not_called()

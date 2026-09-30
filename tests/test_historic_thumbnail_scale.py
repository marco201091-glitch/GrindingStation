import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
import cv2
import numpy as np
from Controller.MTGAController.Controller import Controller
from vision.vision import VisionEngine


class ThumbnailScaleTests(unittest.TestCase):
    def test_saved_thumbnail_at_different_grid_zoom(self):
        with tempfile.TemporaryDirectory() as folder:
            template = np.random.default_rng(7).integers(0, 256, (80, 120, 3), dtype=np.uint8)
            path = str(Path(folder) / "W.png")
            cv2.imwrite(path, template)
            frame = np.zeros((730, 1540, 3), dtype=np.uint8)
            scaled = cv2.resize(template, (round(120 * 1.36), round(80 * 1.36)))
            h, w = scaled.shape[:2]
            frame[200:200+h, 300:300+w] = scaled
            controller = Controller.__new__(Controller)
            controller._stop_requested = False
            controller._get_ui_action_arena_region = Mock(return_value=(100, 50, 1920, 1080))
            controller._vision = VisionEngine()
            controller._vision.capture = Mock(return_value=frame)
            controller._click_abs = Mock()
            controller._locate_image_center_direct = Mock(side_effect=AssertionError("desktop probe forbidden"))
            for label in ("HISTORIC_DECK", "POST_LOGIN_DECK"):
                self.assertTrue(controller._click_image(path, label, timeout=2))
                controller._click_abs.assert_called_with(100+300+w//2, 50+350+200+h//2, label)
            controller._vision.capture.assert_called_with((100, 400, 1540, 730))
            # Same client content at 1366x768: recognition stays in reference
            # coordinates; the resulting click must map back to desktop pixels.
            controller._get_ui_action_arena_region.return_value = (250, 120, 1366, 768)
            roi = controller._scale_base_region_to_arena((250, 120, 1366, 768), (0, 350, 1540, 730))
            controller._vision.capture.return_value = cv2.resize(frame, (roi[2], roi[3]))
            self.assertTrue(controller._click_image(path, "HISTORIC_DECK", timeout=2))
            x, y, _ = controller._click_abs.call_args.args
            self.assertAlmostEqual(x, roi[0] + round((300+w//2) * roi[2]/1540), delta=2)
            self.assertAlmostEqual(y, roi[1] + round((200+h//2) * roi[3]/730), delta=2)
            controller._stop_requested = True
            controller._click_abs.reset_mock()
            self.assertFalse(controller._click_image(path, "HISTORIC_DECK", timeout=2))
            controller._click_abs.assert_not_called()

    def test_missing_thumbnail_never_clicks(self):
        controller = Controller.__new__(Controller)
        controller._click_abs = Mock()
        self.assertFalse(controller._click_image("missing-thumbnail.png", "HISTORIC_DECK"))
        controller._click_abs.assert_not_called()

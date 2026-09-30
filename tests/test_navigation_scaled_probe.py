"""Non-reference clients should not wait on a mismatched native-size probe."""
import unittest
from unittest.mock import Mock

from Controller.MTGAController.Controller import Controller


class NavigationScaledProbeTests(unittest.TestCase):
    def controller(self, size):
        controller = Controller.__new__(Controller)
        controller._get_ui_action_arena_region = Mock(return_value=(100, 50, *size))
        controller._locate_image_center_direct = Mock(return_value=None)
        controller._locate_image_center_in_rescaled_region = Mock(return_value=(300, 200))
        return controller

    def test_small_client_uses_normalized_probe_without_native_timeout(self):
        controller = self.controller((1366, 768))
        point = controller._locate_image_center_in_scaled_arena_region(
            'home.png', 'HOME', rel_region=(0, 0, 760, 260), timeout=2.0)
        self.assertEqual(point, (300, 200))
        controller._locate_image_center_direct.assert_not_called()
        controller._locate_image_center_in_rescaled_region.assert_called_once()
        kwargs = controller._locate_image_center_in_rescaled_region.call_args.kwargs
        self.assertEqual(kwargs['normalized_size'], (760, 260))
        self.assertEqual(kwargs['timeout'], 2.0)

    def test_reference_client_retains_successful_native_probe(self):
        controller = self.controller((1920, 1080))
        controller._locate_image_center_direct.return_value = (200, 100)
        self.assertEqual(controller._locate_image_center_in_scaled_arena_region(
            'home.png', 'HOME'), (200, 100))
        controller._locate_image_center_in_rescaled_region.assert_not_called()

    def test_reference_client_with_multiscale_uses_normalized_probe(self):
        controller = self.controller((1920, 1080))
        controller._locate_image_center_in_scaled_arena_region(
            'deck.png', 'DECK', scales=(0.8, 1.0, 1.2))
        controller._locate_image_center_direct.assert_not_called()
        controller._locate_image_center_in_rescaled_region.assert_called_once()

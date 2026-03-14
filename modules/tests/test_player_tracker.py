"""
test player_tracker
"""
import unittest
from unittest.mock import patch
from modules.player_tracker import PlayerTracker

class TestPlayerTracker(unittest.TestCase):
    """
    class PlayerTracker tests
    """
    def setUp(self):
        """
        test setup
        """
        # Mocking YOLO initialization to avoid loading weights during tests
        with patch('modules.player_tracker.YOLO'):
            self.tracker = PlayerTracker(model_size="yolov8n", min_confidence=0.5)

    def test_calculate_speed_success(self):
        """
        To be describeded
        """
        # Frame 1 at (0,0), Frame 2 at (5,0) with dt=1s -> 5m/s -> 18km/h
        self.tracker.calculate_speed(player_id=1, current_pos_m=(0, 0), dt=1.0)
        self.tracker.calculate_speed(player_id=1, current_pos_m=(5, 0), dt=1.0)

        speed = self.tracker.player_data[1]["speeds"][-1]
        self.assertAlmostEqual(speed, 18.0)

    def test_apply_filter_short_data(self):
        """
        To be describeded
        """
        # Should not crash if data is too short for median filter
        self.tracker.player_data[1] = {"speeds": [10, 12]}
        self.tracker.apply_filter(1)
        self.assertEqual(len(self.tracker.player_data[1]["speeds"]), 2)

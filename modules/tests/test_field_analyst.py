"""
test field_analyst
"""
import unittest
from modules.field_analyst import FieldAnalyst

class TestFieldAnalyst(unittest.TestCase):
    """
    class field_analyst tests
    """
    def setUp(self):
        """
        test setup
        """
        self.analyst = FieldAnalyst(pitch_length=105, pitch_width=68)
        self.src_points = [[0, 0], [100, 0], [100, 100], [0, 100]]

    def test_calibration_success(self):
        """
        To be describeded
        """
        self.analyst.calibrate(self.src_points)
        self.assertIsNotNone(self.analyst.homography_matrix)

    def test_pixel_to_meters_without_calibration(self):
        """
        To be describeded
        """
        # Should return original coordinates if no matrix exists
        x, y = self.analyst.pixel_to_meters(10, 10)
        self.assertEqual((x, y), (10, 10))

    def test_calibration_failure_invalid_points(self):
        """
        To be describeded
        """
        # Passing empty list should raise an error or fail matrix generation
        with self.assertRaises(Exception):
            self.analyst.calibrate([[0,0]])

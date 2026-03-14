"""
test match_analyzer
"""
import unittest
from unittest.mock import patch, MagicMock
from modules.match_analyzer import MatchAnalyzer

class TestMatchAnalyzer(unittest.TestCase):
    """
    class match_analyzer tests
    """
    @patch('modules.match_analyzer.yaml.safe_load')
    @patch('builtins.open', new_callable=MagicMock)
    def test_init_config_loading(self, mock_open, mock_yaml):
        """
        To be describeded
        """
        mock_yaml.return_value = {
            'pitch': {'length': 105, 'width': 68},
            'analysis': {'model_size': 'yolov8n', 'min_confidence': 0.5, 'sample_rate': 0.2}
        }
        analyzer = MatchAnalyzer("dummy.yaml")
        self.assertEqual(analyzer.analyst.pitch_length, 105)

    def test_process_video_invalid_path(self):
        """
        To be describeded
        """
        with patch('modules.match_analyzer.yaml.safe_load'):
            with patch('builtins.open'):
                analyzer = MatchAnalyzer("dummy.yaml")
                with self.assertRaises(ValueError):
                    analyzer.process_video("non_existent.mp4")

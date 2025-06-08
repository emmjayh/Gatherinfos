import unittest
import json
import os
from interactive_map import create_interactive_map

class TestInteractiveMap(unittest.TestCase):

    def test_vertical_stretch_factor_effect_on_center(self):
        mock_spawn_points = [
            {'coordinates': [10, 20, 0], 'type_id': 1, 'collection_desc': 'A', 'collection_id': '100'},
            {'coordinates': [30, 40, 0], 'type_id': 1, 'collection_desc': 'B', 'collection_id': '101'}
        ]
        dummy_data_file_path = "dummy_test_spawn_data.json"
        test_output_map_file = "test_map_output.html"

        # Create the dummy JSON file
        with open(dummy_data_file_path, 'w') as f:
            json.dump(mock_spawn_points, f)

        vertical_stretch_factor = 2.0

        # Expected calculations:
        # Original Ys: 20, 40
        # Stretched Ys: 20 * 2.0 = 40, 40 * 2.0 = 80
        # Avg Stretched Y: (40 + 80) / 2 = 120 / 2 = 60
        expected_avg_y_stretched = (mock_spawn_points[0]['coordinates'][1] * vertical_stretch_factor +
                                    mock_spawn_points[1]['coordinates'][1] * vertical_stretch_factor) / len(mock_spawn_points)

        # Original Xs: 10, 30
        # Avg X: (10 + 30) / 2 = 40 / 2 = 20
        expected_avg_x = (mock_spawn_points[0]['coordinates'][0] +
                          mock_spawn_points[1]['coordinates'][0]) / len(mock_spawn_points)

        map_center_lat, map_center_lon = create_interactive_map(
            data_file=dummy_data_file_path,
            output_file=test_output_map_file,
            vertical_stretch_factor=vertical_stretch_factor
        )

        self.assertIsNotNone(map_center_lat, "Function returned None for latitude, possibly due to an error reading dummy file or no points.")
        self.assertIsNotNone(map_center_lon, "Function returned None for longitude.")

        self.assertAlmostEqual(map_center_lat, expected_avg_y_stretched)
        self.assertAlmostEqual(map_center_lon, expected_avg_x)

        # Clean up created files
        if os.path.exists(dummy_data_file_path):
            os.remove(dummy_data_file_path)
        if os.path.exists(test_output_map_file):
            os.remove(test_output_map_file)

if __name__ == '__main__':
    unittest.main()

import pytest
import os
import random
import math
from PIL import Image
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QPointF,  Qt
from PyQt6.QtGui import QPolygonF
from SideScanSonarEditor.app import MyWindow  # adjust path based on your repo structure
from unittest.mock import patch, MagicMock, mock_open
from SideScanSonarEditor.widgets.draw_shapes import Polygon

# Test globals
test_dir = "/some/fake/path"
test_file = "data.xtf"
test_coco_anns_filename = "annotations.json"
test_labels_file = f"{test_file.rsplit('.', 1)[0]}_labels.json"
test_tiles_file = f"{test_file.rsplit('.', 1)[0]}_tiles.json"
test_labels_path = os.path.join(test_dir, test_labels_file)
test_tiles_path = os.path.join(test_dir, test_tiles_file)
test_port_data = "test_port_data"
test_starboard_data = "test_starboard_data"
test_decimation = 3
test_stretch = 5
test_load_params = {"decimation": test_decimation, "stretch": test_stretch, "full_image_height": 2000, "full_image_width": 1000}
test_port_image = Image.new("RGB", (1000, 2000))
test_port_params = {"channel_min": 0.0, "channel_max": 100.0}
test_starboard_image = Image.new("RGB", (1000, 2000))
test_starboard_params = {"channel_min": 0.0, "channel_max": 100.0}
test_merged_image = "test_merged_image"

test_polygon_data = {
    "shapes": {
        "0": {
            "label": "rock",
            "points": [[10, 10], [20, 20]]
        }
    }
}
test_tile_data = {
    "full_height": 8000, 
    "full_width": 12000,
    "shapes": {
        "0": {
            "rectangle": [0, 0, 5, 5]
        }
    }
}

@pytest.fixture
def window(qtbot):
    win = MyWindow()
    qtbot.addWidget(win)
    win.show()
    return win

def test_window_title(window):
    """
    Test App name.
    """
    assert window.windowTitle() == ("Side Scan Sonar Editor")

def test_open_file_dialog_loads_image(window, qtbot):
    """
    Test Open file button action.
    """
    with patch("SideScanSonarEditor.app.QFileDialog.getOpenFileName") as mock_dialog, \
         patch("SideScanSonarEditor.app.read_xtf") as mock_read_xtf, \
         patch("SideScanSonarEditor.app.convert_to_image") as mock_convert_image, \
         patch("SideScanSonarEditor.app.merge_images") as mock_merge_images, \
         patch("SideScanSonarEditor.app.toqpixmap") as mock_toqpixmap, \
         patch("SideScanSonarEditor.app.os.path.exists") as mock_exists, \
         patch("SideScanSonarEditor.app.open", mock_open()) as mock_file, \
         patch("SideScanSonarEditor.app.json.load") as mock_json_load:

        # Setup return values
        mock_dialog.return_value = (os.path.join(test_dir, test_file), "Triton Extended Format (*.xtf)")
        mock_read_xtf.return_value = (test_port_data, test_starboard_data, test_load_params)
        mock_convert_image.side_effect = [(test_port_image, test_port_params), (test_starboard_image, test_starboard_params)]
        mock_merge_images.return_value = test_merged_image
        mock_toqpixmap.return_value = MagicMock()

        # Simulate label and tile file existence
        def exists_side_effect(path):
            return path in [test_labels_path, test_tiles_path]

        mock_exists.side_effect = exists_side_effect

        # Simulate loading labels and tiles
        def json_load_side_effect(file_obj):
            if mock_file.call_args[0][0] == test_labels_path:
                return test_polygon_data
            elif mock_file.call_args[0][0] == test_tiles_path:
                return test_tile_data
            return {}

        mock_json_load.side_effect = json_load_side_effect

        # Simulate clicking the "Open file" button
        qtbot.mouseClick(window.open_file_btn, Qt.MouseButton.LeftButton)

        # Assert all actions:
        assert window.open_file_btn.text() == "Open file"
        assert window.input_filepath == test_dir
        assert window.input_filename == test_file
        assert window.labels_filename == f"{test_file.rsplit('.', 1)[0]}_labels.json"
        assert window.tiles_filename == f"{test_file.rsplit('.', 1)[0]}_tiles.json"
        assert window.coco_anns_filename == f"{test_file.rsplit('.', 1)[0]}.json"
        assert window.port_data == test_port_data
        assert window.starboard_data == test_starboard_data
        assert window.load_params == test_load_params
        assert window.port_image == test_port_image
        assert window.port_params == test_port_params
        assert window.starboard_image == test_starboard_image
        assert window.starboard_params == test_starboard_params
        assert window.merged_image == test_merged_image
        assert window.input_filepath == test_dir
        assert window.polygons_data == test_polygon_data["shapes"]
        assert window.tiles_data == test_tile_data["shapes"]
        assert window.canvas.selected_polygons == []
        assert window.canvas.selected_tiles == []
        assert "rock" in window.old_classes
        assert window.windowTitle().endswith(test_file)
        assert window.draw_crop_tile_btn.isEnabled()

def test_save_labels(window, qtbot):
    """
    Test saving of the polygons and tiles into respective json files.
    The test is generating mock polygon and tile sets for saving.
    """
    window.port_image = test_port_image
    window.starboard_image = test_starboard_image
    window.old_classes = {}
    window.canvas.classes = ["classA", "classB"]
    window.input_filepath = test_dir
    window.tiles_filename = test_tiles_file
    window.labels_filename = test_labels_file
    window.load_params = test_load_params

    # Create a mock polygon set
    valid_polygons = []
    expected_corners = []

    for _ in range(2):
        corners_raw = [
            (random.randint(0, 500), random.randint(0, 1000)),
            (random.randint(0, 500), random.randint(0, 1000))
        ]
        mock_polygon = MagicMock()
        mock_polygon._polygon_corners = corners_raw
        mock_polygon.polygon_class = "classA"
        valid_polygons.append({"polygon": mock_polygon})

        # Compute expected transformed corners
        corners_transformed = []
        for x, y in corners_raw:
            tx = math.floor(x) * window.load_params["decimation"]
            ty = math.floor(window.port_image.size[1] / window.load_params["stretch"] -
                            math.floor(y / window.load_params["stretch"]))
            corners_transformed.append([tx, ty])
        expected_corners.append(corners_transformed)

    window.canvas._polygons = [valid_polygons[0], "del", valid_polygons[1]]

    # Create a mock tile set
    expected_tiles = []

    def create_random_rect():
        x = random.randint(0, 500)
        y = random.randint(0, 500)
        w = random.randint(10, 200)
        h = random.randint(10, 200)
        rect = MagicMock()
        rect.rect.return_value.x.return_value = x
        rect.rect.return_value.y.return_value = y
        rect.rect.return_value.width.return_value = w
        rect.rect.return_value.height.return_value = h

        # Calculate expected rectangle
        rect_data = [
            math.floor(x) * window.load_params["decimation"],
            math.floor((window.port_image.size[1] - math.floor(y)) / window.load_params["stretch"]),
            w * window.load_params["decimation"],
            math.floor(math.floor(h) / window.load_params["stretch"])
        ]
        expected_tiles.append(rect_data)

        return {"tiles": rect}

    tile_data_0 = create_random_rect()
    tile_data_1 = create_random_rect()
    window.canvas._tiles = [tile_data_0, "del", tile_data_1]

    with patch("SideScanSonarEditor.app.open", mock_open()) as mock_file, \
         patch("SideScanSonarEditor.app.json.dump") as mock_json_dump, \
         patch("SideScanSonarEditor.app.os.path.join", side_effect=os.path.join):

        window.merged_image = MagicMock()
        qtbot.mouseClick(window.save_btn, Qt.MouseButton.LeftButton)

        assert mock_json_dump.call_count == 2

        # Validate tiles data
        tiles_data = mock_json_dump.call_args_list[0][0][0]
        assert "shapes" in tiles_data
        assert isinstance(tiles_data["shapes"], dict)
        assert tiles_data["full_height"] == test_starboard_image.size[1]
        assert tiles_data["full_width"] == test_starboard_image.size[0]
        assert 0 in tiles_data["shapes"]
        assert 1 in tiles_data["shapes"]
        assert tiles_data["shapes"][0]["rectangle"] == expected_tiles[0]
        assert tiles_data["shapes"][1]["rectangle"] == expected_tiles[1]

        # Validate polygons data
        polygons_data = mock_json_dump.call_args_list[1][0][0]
        assert "shapes" in polygons_data
        shapes = polygons_data["shapes"]
        assert isinstance(shapes, dict)
        assert 0 in shapes
        assert 1 in shapes
        assert shapes[0]["label"] == "classA"
        assert shapes[1]["label"] == "classA"
        assert shapes[0]["points"] == expected_corners[0]
        assert shapes[1]["points"] == expected_corners[1]

def test_crop_tiles(window, qtbot):
    """
    Test crop_tiles method generates COCO-style JSON with tiles and annotations.
    """
    # Setup image and parameters
    window.port_image = test_port_image
    window.starboard_image = test_starboard_image
    window.merged_image = MagicMock()
    window.input_filepath = test_dir
    window.coco_anns_filename = test_coco_anns_filename
    window.load_params = test_load_params

    def create_polygon(corners, idx=0, poly_class="Boulder"):
        qpoly = QPolygonF([QPointF(x, y) for x, y in corners])
        return {"polygon": Polygon(qpoly, polygon_idx=idx, polygon_class=poly_class, color=[255, 0, 0, 255])}

    # Create 3 polygons with one within tile 0 and 2 within tile 2
    corners_0 = [(100, 100), (120, 120), (110, 140)]
    poly_0 = create_polygon(corners_0, idx=0)
    corners_1 = [(300, 300), (320, 320), (310, 340)]
    poly_1 = create_polygon(corners_1, idx=1)
    corners_2 = [(250, 250), (500, 300), (640, 190)]
    poly_2 = create_polygon(corners_2, idx=2)
    window.canvas._polygons = [poly_0, poly_1, poly_2]

    # Create 4 tiles and assign polygons
    rect0 = MagicMock()
    rect0.rect.return_value.x.return_value = 90
    rect0.rect.return_value.y.return_value = 90
    rect0.rect.return_value.width.return_value = 100
    rect0.rect.return_value.height.return_value = 100
    rect0.polygons_inside = [0]

    tile1 = "del"

    rect2 = MagicMock()
    rect2.rect.return_value.x.return_value = 290
    rect2.rect.return_value.y.return_value = 290
    rect2.rect.return_value.width.return_value = 150
    rect2.rect.return_value.height.return_value = 150
    rect2.polygons_inside = [1, 2]

    rect3 = MagicMock()
    rect3.rect.return_value.x.return_value = 500
    rect3.rect.return_value.y.return_value = 500
    rect3.rect.return_value.width.return_value = 100
    rect3.rect.return_value.height.return_value = 100
    rect3.polygons_inside = []

    window.canvas._tiles = [
        {"tiles": rect0},
        tile1,
        {"tiles": rect2},
        {"tiles": rect3}
    ]

    with patch("SideScanSonarEditor.app.cv2.flip", side_effect=lambda arr, flipCode: np.flipud(arr)), \
         patch("SideScanSonarEditor.app.open", mock_open()) as mock_file, \
         patch("SideScanSonarEditor.app.json.dump") as mock_json_dump, \
         patch("SideScanSonarEditor.app.os.path.join", side_effect=os.path.join):

        window.crop_tiles()

        assert mock_json_dump.call_count == 1
        coco_data = mock_json_dump.call_args[0][0]

        # Validate overall structure
        assert "images" in coco_data
        assert "annotations" in coco_data
        assert "categories" in coco_data

        # Check correct number of images and annotations
        assert len(coco_data["images"]) == 3
        assert len(coco_data["annotations"]) == 2

        # Check if annotation belongs to correct tile/image ID
        image_ids = {ann["image_id"] for ann in coco_data["annotations"]}
        assert image_ids == {0, 1}

def test_decimation_slider_updates(window, qtbot):
    """
    Test Decimation slider action.
    """
    slider = window.decimation_slider
    label = window.decimation_label

    # Set slider value
    slider.setValue(test_decimation)
    
    # Wait for UI update
    qtbot.wait(100)

    assert slider.minimum() == 1
    assert slider.maximum() == 10
    assert slider.value() == test_decimation
    assert label.text().split(": ")[1] == str(test_decimation)

def test_stretch_slider_updates(window, qtbot):
    """
    Test Stretch slider action.
    """
    slider = window.stretch_slider
    label = window.stretch_label
    checkbox = window.stretch_checkbox

    checkbox.setChecked(True)
    qtbot.wait(50)

    slider.setValue(test_stretch)
    qtbot.wait(100)

    assert checkbox.isChecked()
    assert slider.value() == test_stretch
    assert label.text().split(": ")[1] == str(test_stretch)
    assert slider.value() == test_stretch
    assert label.text().split(": ")[1] == str(test_stretch)

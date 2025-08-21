import unittest
import tkinter as tk
import settings as S
from cube import Cube

class TestCube(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # don't show a window during tests
        w = S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE + S.GRID_PADDING
        h = S.CARD_AREA_Y + S.CARD_AREA_H + S.GRID_PADDING
        self.canvas = tk.Canvas(self.root, width=w, height=h)
        self.canvas.pack()
        self.cube = Cube(self.canvas, idx=0, x=40, y=40, color="#ff7f50")

    def tearDown(self):
        self.canvas.destroy()
        self.root.destroy()

    def test_center_on_cell_sets_current_cell_and_position(self):
        self.cube.center_on_cell(1, 1)
        self.assertEqual(self.cube.current_cell, (1, 1))
        # Check that cube top-left aligns to expected center placement
        x0, y0, x1, y1 = self.canvas.bbox(self.cube.rect)
        cell_x = S.GRID_ORIGIN_X + 1 * S.CELL_SIZE
        cell_y = S.GRID_ORIGIN_Y + 1 * S.CELL_SIZE
        expected_x = cell_x + (S.CELL_SIZE - S.CUBE_SIZE) / 2
        expected_y = cell_y + (S.CELL_SIZE - S.CUBE_SIZE) / 2
        self.assertAlmostEqual(x0, expected_x, delta=1)
        self.assertAlmostEqual(y0, expected_y, delta=1)

    def test_return_to_start(self):
        self.cube.center_on_cell(2, 3)
        self.cube.return_to_start()
        x0, y0, x1, y1 = self.canvas.bbox(self.cube.rect)
        self.assertAlmostEqual(x0, 38, delta=1)
        self.assertAlmostEqual(y0, 38, delta=1)
        self.assertIsNone(self.cube.current_cell)

    def test_drag_flags(self):
        # begin/end drag should toggle internal flags
        self.cube.begin_drag(50, 50)
        self.assertTrue(self.cube.dragging)
        self.cube.end_drag()
        self.assertFalse(self.cube.dragging)

if __name__ == "__main__":
    unittest.main()

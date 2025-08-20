import os
import unittest
import tkinter as tk

import settings as S
from game import Game, Image, ImageTk  # Image, ImageTk may be None

class TestGameUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = Game(self.root)

    def tearDown(self):
        self.game.canvas.destroy()
        self.root.destroy()

    def test_hand_has_8_slots_and_fits_area(self):
        # ensure we made exactly 8 slots
        self.assertEqual(len(self.game.hand_slot_ids), 8)
        # ensure no slot overflows the card area bounds
        max_x = S.CARD_AREA_X + S.CARD_AREA_W
        max_y = S.CARD_AREA_Y + S.CARD_AREA_H
        for rect_id, _ in self.game.hand_slot_ids:
            x0, y0, x1, y1 = self.game.canvas.coords(rect_id)
            self.assertLessEqual(x1, max_x + 0.1)
            self.assertLessEqual(y1, max_y + 0.1)

    def test_actions_button_label_and_position(self):
        self.assertEqual(self.game.reset_button.cget("text"), "Take Actions")
        bx, by = self.game.canvas.coords(self.game.reset_button_window)

        # Button should be strictly to the LEFT of the hand area
        self.assertLess(bx, S.CARD_AREA_X)

        # And vertically within the hand area's vertical span
        self.assertGreaterEqual(by, S.CARD_AREA_Y)
        self.assertLessEqual(by, S.CARD_AREA_Y + S.CARD_AREA_H)

    def test_all_cell_labels_fit_inside_cells(self):
        # Each drawn label's bbox must be within its cell bbox (with small tolerance)
        tol = 1.1
        for r in range(S.GRID_ROWS):
            for c in range(S.GRID_COLS):
                idx = r * S.GRID_COLS + c
                if idx >= len(self.game.cell_text_ids):
                    continue
                text_id = self.game.cell_text_ids.get((r, c))
                if not text_id:
                    continue
                tx0, ty0, tx1, ty1 = self.game.canvas.bbox(text_id)

                cx0 = S.GRID_ORIGIN_X + c * S.CELL_SIZE + 2
                cy0 = S.GRID_ORIGIN_Y + r * S.CELL_SIZE + 2
                cx1 = cx0 + S.CELL_SIZE - 4
                cy1 = cy0 + S.CELL_SIZE - 4

                self.assertGreaterEqual(tx0 + tol, cx0)
                self.assertGreaterEqual(ty0 + tol, cy0)
                self.assertLessEqual(tx1 - tol, cx1)
                self.assertLessEqual(ty1 - tol, cy1)

    def test_side_image_position_if_available(self):
        if Image is None or ImageTk is None or not os.path.exists(S.SIDE_IMAGE_PATH):
            self.skipTest("Side image not available in this environment")

        self.assertIsNotNone(self.game.side_image_id)

        # Coordinates
        x, y = self.game.canvas.coords(self.game.side_image_id)
        grid_right = S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE
        grid_top = S.GRID_ORIGIN_Y
        grid_h = S.GRID_ROWS * S.CELL_SIZE

        # Placed to the right of the grid, aligned to grid top
        self.assertGreaterEqual(x, grid_right + S.GRID_PADDING - 1)
        self.assertAlmostEqual(y, grid_top, delta=1)

        # Height should equal grid height exactly
        img_w, img_h = self.game.side_image_dims
        self.assertEqual(img_h, grid_h)

        # Canvas wide enough to contain it
        canvas_w = int(self.game.canvas.cget("width"))
        expected_min_w = x + img_w + S.GRID_PADDING
        self.assertGreaterEqual(canvas_w, expected_min_w - 1)


if __name__ == "__main__":
    unittest.main()

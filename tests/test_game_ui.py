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
        try:
            self.root.destroy()
        except Exception:
            pass

    def _bold_texts(self):
        """Helper: return the list of texts currently rendered in bold."""
        return [txt for (_tid, bold, txt) in getattr(self.game, "costs_line_ids", []) if bold]

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
        self.assertEqual(self.game.take_action_button.cget("text"), "Take Actions")
        bx, by = self.game.canvas.coords(self.game.take_action_button_window)

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

    def test_start_area_position_and_label(self):
        # Start area rectangle exists
        rect_id = getattr(self.game, "start_area_rect_id", None)
        self.assertIsNotNone(rect_id)

        x0, y0, x1, y1 = self.game.canvas.coords(rect_id)

        # Top flush with grid top
        self.assertAlmostEqual(y0, S.GRID_ORIGIN_Y, delta=1)

        # Right edge should sit exactly one GRID_PADDING to the left of grid
        expected_right = S.GRID_ORIGIN_X - S.GRID_PADDING
        self.assertAlmostEqual(x1, expected_right, delta=1)

        # Left of grid (sanity)
        self.assertLess(x1, S.GRID_ORIGIN_X)

        # Label exists, is black, centered above the box
        label_id = getattr(self.game, "start_area_label_id", None)
        self.assertIsNotNone(label_id)
        lx, ly = self.game.canvas.coords(label_id)
        self.assertAlmostEqual(lx, (x0 + x1) / 2, delta=2)
        self.assertLess(ly, y0)  # above the box
        self.assertEqual(self.game.canvas.itemcget(label_id, "fill"), "black")

    def test_costs_panel_bolds_next_presence_cost(self):
        g = self.game

        # Initially 0 presence -> next presence cost is 1st region: $1
        g._render_costs_panel()
        bolded = self._bold_texts()
        self.assertIn("Model Version Scaling Requirements", bolded)  # header is bold
        self.assertIn("1st Region: $1", bolded)

        # Add presence in one region -> next becomes 2nd region: $2
        g.regions.add_presence("Europe")
        g._render_costs_panel()
        bolded = self._bold_texts()
        self.assertIn("2nd Region: $2", bolded)
        # and 1st no longer needs to be bold (not strictly necessary, but nice to check)
        self.assertNotIn("1st Region: $1", bolded)

    def test_costs_panel_bolds_next_model_requirement(self):
        g = self.game

        # Initially: model=0, so next bold should be V1
        g._render_costs_panel()
        bolded = [txt for (_tid, bold, txt) in g.costs_line_ids if bold]
        self.assertIn(f"V1: Pay ${S.MODEL_UPGRADE_COSTS[1]}, {S.COMPUTE_STEPS[1]}", bolded)

        # Lift the compute cap so model can advance
        g.inc_compute(3)  # now compute_idx >= 3

        # Advance model by 2 (0 -> 2), so next bold should be V3
        g.inc_model(2)
        g._render_costs_panel()
        bolded = [txt for (_tid, bold, txt) in g.costs_line_ids if bold]
        self.assertIn(f"V3: Pay ${S.MODEL_UPGRADE_COSTS[3]}, {S.COMPUTE_STEPS[3]}", bolded)


if __name__ == "__main__":
    unittest.main()

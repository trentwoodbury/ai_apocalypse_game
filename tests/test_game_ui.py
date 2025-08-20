import unittest
import tkinter as tk

import settings as S
from game import Game

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
        # correct label
        self.assertEqual(self.game.reset_button.cget("text"), "Take Actions")
        # button should be above the hand area (y < CARD_AREA_Y)
        bx, by = self.game.canvas.coords(self.game.reset_button_window)
        self.assertLess(by, S.CARD_AREA_Y)

if __name__ == "__main__":
    unittest.main()

import unittest
import tkinter as tk
import settings as S
from funds import Funds

class TestFunds(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk(); self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=400, height=200); self.canvas.pack()
        self.funds = Funds(S.FUNDS_START, S.FUNDS_SERIES, self.canvas, 10, 10)

    def tearDown(self):
        self.canvas.destroy(); self.root.destroy()

    def test_progressions_and_clamp(self):
        # compute_or_model costs: 0,2,4,8,16,32,64,128
        spent = self.funds.charge("compute_or_model", 1);  self.assertEqual(self.funds.value, S.FUNDS_START - 0)
        spent = self.funds.charge("compute_or_model", 1);  self.assertEqual(self.funds.value, S.FUNDS_START - 2)
        spent = self.funds.charge("compute_or_model", 6);  # spend 4+8+16+32+64+128 = 252
        self.assertEqual(self.funds.value, max(0, S.FUNDS_START - (2 + 252)))  # clamped at 0

        # Reset: confirm clamping works with large charge
        self.funds.value = 5
        self.funds.charge("lobby", 10)  # huge charge, should clamp to 0
        self.assertEqual(self.funds.value, 0)

if __name__ == "__main__":
    unittest.main()

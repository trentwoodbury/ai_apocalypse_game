import unittest
from game import Game
import tkinter as tk
import settings as S

class TestOperations(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = Game(self.root)
        self.game.funds.add(1000)  # avoid funds gate for these tests

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_only_one_draggable_initially(self):
        g = self.game
        unlocked = [c for c in g.cubes if not c.locked]
        locked = [c for c in g.cubes if c.locked]
        self.assertEqual(len(unlocked), 1)
        self.assertEqual(len(locked), 3)

    def test_scale_operations_unlocks_and_charges(self):
        g = self.game
        c = next(c for c in g.cubes if not c.locked)
        g.place_cube_and_handle_events(c, 0, 2)
        for extra in [cc for cc in g.cubes if cc is not c]:
            # drop them somewhere cheap to reach 4 placements
            g.place_cube_and_handle_events(extra, 0, 0)

        before = (g.ops_available, g.ops_aspirational, g.funds.value)
        g.take_actions()
        after = (g.ops_available, g.ops_aspirational, g.funds.value)
        self.assertEqual(after[0], before[0] + 1)
        self.assertEqual(after[1], before[1] - 1)
        self.assertEqual(after[2], before[2] - 4)  # first ops scale costs $4

    def test_cost_panel_bolds_next_ops_cost(self):
        g = self.game
        g._render_costs_panel()
        bold_texts = [txt for (_tid, bold, txt) in getattr(g, "costs_line_ids", []) if bold]
        self.assertIn("2 Actions: $4", bold_texts)

        # Buy once → next should bold 3 actions: $10
        c = next(c for c in g.cubes if not c.locked)
        g.place_cube_and_handle_events(c, 0, 2)
        for extra in [cc for cc in g.cubes if cc is not c]:
            g.place_cube_and_handle_events(extra, 0, 0)
        g.take_actions()

        g._render_costs_panel()
        bold_texts = [txt for (_tid, bold, txt) in getattr(g, "costs_line_ids", []) if bold]
        self.assertIn("3 Actions: $10", bold_texts)

    def test_ops_max_four(self):
        g = self.game
        # buy 3 times → 4 available total
        for _ in range(3):
            c = next(c for c in g.cubes if not c.locked)
            g.place_cube_and_handle_events(c, 0, 2)
            for extra in [cc for cc in g.cubes if cc is not c]:
                g.place_cube_and_handle_events(extra, 0, 0)
            g.take_actions()
        self.assertEqual(g.ops_available, S.OPS_MAX_TOKENS)
        self.assertEqual(sum(1 for c in g.cubes if c.locked), 0)


import unittest
import tkinter as tk
import settings as S
from game import Game

class TestGame(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = Game(self.root)

    def tearDown(self):
        self.game.canvas.destroy()
        self.root.destroy()

    def _place_and_free(self, cube, row, col):
        """Helper for tests: place, then free the cell so we can place again."""
        self.game.place_cube_and_handle_events(cube, row, col)
        # free the spot and return cube to start to allow repeated draws in tests
        self.game.occupied.pop((row, col), None)
        cube.return_to_start()

    def test_draw_only_on_col0_rows012(self):
        cube = self.game.cubes[0]
        start_hand = len(self.game.hand)

        # Valid draw cells
        for r in (0, 1, 2):
            self._place_and_free(cube, r, 0)
        self.assertEqual(len(self.game.hand), start_hand + 3)

        # Invalid cells: column 1..3, or row 3 on column 0
        invalid_targets = [(0,1), (1,2), (2,3), (3,0), (3,1), (0,3)]
        for r, c in invalid_targets:
            self._place_and_free(cube, r, c)
        # Hand should not increase from invalid placements
        self.assertEqual(len(self.game.hand), start_hand + 3)

    def test_hand_persists_through_reset(self):
        cube = self.game.cubes[1]
        self._place_and_free(cube, 0, 0)
        self._place_and_free(cube, 1, 0)
        pre_reset_hand = list(self.game.hand)

        # Now reset the board
        self.game.reset_game()

        # Hand remains visible & unchanged
        self.assertEqual(self.game.hand, pre_reset_hand)
        # Check UI shows those values
        for i, card in enumerate(pre_reset_hand):
            _, text_id = self.game.hand_slot_ids[i]
            ui_text = self.game.canvas.itemcget(text_id, "text")
            self.assertEqual(ui_text, str(card))

    def test_hand_limit_enforced(self):
        cube = self.game.cubes[2]
        # Force draws until hitting limit
        target_draws = S.HAND_LIMIT + 2  # try to exceed
        for _ in range(target_draws):
            self._place_and_free(cube, 0, 0)

        self.assertEqual(len(self.game.hand), S.HAND_LIMIT)
        # UI should show "Hand is full" message after exceeding
        msg = self.game.canvas.itemcget(self.game.hand_full_text, "text")
        self.assertIn("Hand is full", msg)

    def test_deck_text_updates(self):
        before = self.game.canvas.itemcget(self.game.deck_text, "text")
        cube = self.game.cubes[0]
        self._place_and_free(cube, 0, 0)  # draw once
        after = self.game.canvas.itemcget(self.game.deck_text, "text")
        self.assertNotEqual(before, after)

    def test_draw_writes_immediately_to_next_slot(self):
        cube = self.game.cubes[0]

        # Force one valid draw
        self.game.place_cube_and_handle_events(cube, 0, 0)
        self.game.occupied.pop((0, 0), None)
        cube.return_to_start()

        self.assertEqual(len(self.game.hand), 1)
        # UI slot 0 should show the exact card value
        card0 = self.game.hand[0]
        _, text_id = self.game.hand_slot_ids[0]
        ui_text = self.game.canvas.itemcget(text_id, "text")
        self.assertEqual(ui_text, str(card0))

if __name__ == "__main__":
    unittest.main()

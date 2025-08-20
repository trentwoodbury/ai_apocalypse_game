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

    def test_take_actions_draws_cards_for_cubes_in_final_column(self):
        # place a cube in final column row 0
        cube = self.game.cubes[0]
        cube.current_cell = (0, S.GRID_COLS - 1)

        before = len(self.game.hand)
        self.game.take_actions()
        after = len(self.game.hand)

        self.assertGreater(after, before)

    def test_place_in_other_columns_does_not_draw(self):
        cube = self.game.cubes[1]
        initial_deck = len(self.game.deck)
        self.game.place_cube_and_handle_events(cube, 1, 2)  # column 2
        self.assertEqual(len(self.game.deck), initial_deck)
        self.assertEqual(len(self.game.hand), 0)

    def test_no_card_drawn_until_take_actions(self):
        cube = self.game.cubes[0]
        cube.current_cell = (0, S.GRID_COLS - 1)

        # hand still empty before pressing button
        self.assertEqual(len(self.game.hand), 0)

    def test_hand_persists_through_reset(self):
        cube = self.game.cubes[1]
        self._place_and_free(cube, 0, 0)
        self._place_and_free(cube, 1, 0)
        pre_reset_hand = list(self.game.hand)

        # Now reset the board
        self.game.take_actions()

        # Hand remains visible & unchanged
        self.assertEqual(self.game.hand, pre_reset_hand)
        # Check UI shows those values
        for i, card in enumerate(pre_reset_hand):
            _, text_id = self.game.hand_slot_ids[i]
            ui_text = self.game.canvas.itemcget(text_id, "text")
            self.assertEqual(ui_text, str(card))

    def test_hand_limit_enforced(self):
        cube = self.game.cubes[2]
        final_col = S.GRID_COLS - 1

        # Fill up to the hand limit via place -> take_actions cycles
        for _ in range(S.HAND_LIMIT):
            self.game.place_cube_and_handle_events(cube, 0, final_col)
            self.game.take_actions()  # draw happens here

        self.assertEqual(len(self.game.hand), S.HAND_LIMIT)

        # Attempt to exceed the hand limit
        self.game.place_cube_and_handle_events(cube, 0, final_col)
        self.game.take_actions()

        self.assertEqual(len(self.game.hand), S.HAND_LIMIT)
        msg = self.game.canvas.itemcget(self.game.hand_full_text, "text")
        self.assertIn("Hand is full", msg)

    def test_deck_text_updates(self):
        before = self.game.canvas.itemcget(self.game.deck_text, "text")
        self.game.draw_card()
        after = self.game.canvas.itemcget(self.game.deck_text, "text")
        self.assertNotEqual(before, after)

    def test_draw_occurs_on_take_actions(self):
        cube = self.game.cubes[0]
        cube.current_cell = (0, S.GRID_COLS - 1)  # simulate cube placed in final column

        self.assertEqual(len(self.game.hand), 0)  # before
        self.game.take_actions()
        self.assertEqual(len(self.game.hand), 1)  # after


if __name__ == "__main__":
    unittest.main()

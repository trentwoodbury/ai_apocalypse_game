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

    def test_initial_deck_size(self):
        self.assertEqual(len(self.game.deck), 50)

    def test_pixel_to_cell_second_column(self):
        # pick a point well inside column index 1, row 0
        x = S.GRID_ORIGIN_X + 1 * S.CELL_SIZE + S.CELL_SIZE // 2
        y = S.GRID_ORIGIN_Y + S.CELL_SIZE // 2
        self.assertEqual(self.game.pixel_to_cell(x, y), (0, 1))

    def test_place_in_second_column_draws_card(self):
        cube = self.game.cubes[0]
        initial_deck = len(self.game.deck)
        # place cube in (row 0, col 1)
        self.game.place_cube_and_handle_events(cube, 0, 1)
        # deck should decrement and last_card should be set
        self.assertEqual(len(self.game.deck), initial_deck - 1)
        self.assertIsNotNone(self.game.last_card)
        # UI updated
        card_text = self.game.canvas.itemcget(self.game.card_text, "text")
        self.assertNotEqual(card_text, "—")

    def test_place_in_other_column_does_not_draw(self):
        cube = self.game.cubes[1]
        initial_deck = len(self.game.deck)
        self.game.place_cube_and_handle_events(cube, 0, 0)  # column 0
        self.assertEqual(len(self.game.deck), initial_deck)
        self.assertIsNone(self.game.last_card)
        card_text = self.game.canvas.itemcget(self.game.card_text, "text")
        self.assertEqual(card_text, "—")

    def test_occupied_prevents_double_place(self):
        c0 = self.game.cubes[0]
        c1 = self.game.cubes[1]
        target = (2, 2)
        self.assertTrue(self.game.can_place(target))
        self.game.place_cube_and_handle_events(c0, *target)
        self.assertFalse(self.game.can_place(target))
        # If we tried to place c1 there via logic (not UI), it should be blocked
        self.assertIn(target, self.game.occupied)

    def test_reset_game_restores_defaults(self):
        # Draw a card first
        cube = self.game.cubes[2]
        self.game.place_cube_and_handle_events(cube, 1, 1)
        self.assertIsNotNone(self.game.last_card)
        self.assertLess(len(self.game.deck), 50)

        self.game.reset_game()
        self.assertEqual(len(self.game.deck), 50)
        self.assertIsNone(self.game.last_card)
        card_text = self.game.canvas.itemcget(self.game.card_text, "text")
        self.assertEqual(card_text, "—")
        # reset button hidden
        state = self.game.canvas.itemcget(self.game.reset_button_window, "state")
        self.assertEqual(state, "hidden")

    def test_reset_button_appears_when_all_four_placed(self):
        # place all four cubes on distinct cells
        spots = [(0,0), (0,1), (1,2), (2,3)]
        for cube, cell in zip(self.game.cubes, spots):
            self.game.place_cube_and_handle_events(cube, *cell)
        self.game.update_reset_visibility()
        state = self.game.canvas.itemcget(self.game.reset_button_window, "state")
        self.assertEqual(state, "normal")

if __name__ == "__main__":
    unittest.main()

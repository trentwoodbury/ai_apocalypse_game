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

    def test_trackers_start_at_leftmost(self):
        self.assertEqual(self.game.compute_idx, 0)
        self.assertEqual(self.game.model_idx, 0)
        self.assertEqual(self.game.chaos_idx, 0)

    def test_take_actions_bumps_compute_on_0_0(self):
        cube = self.game.cubes[0]
        self.game.place_cube_and_handle_events(cube, 0, 0)
        self.game.take_actions()
        self.assertEqual(self.game.compute_idx, 1)

    def test_take_actions_bumps_model_on_0_1_with_cap(self):
        g = self.game
        c = g.cubes[0]

        # Ensure funds aren't the limiting factor for this logic test
        g.funds.add(1000)

        # Try to bump model while compute=0 -> should stay 0 due to cap
        g.place_cube_and_handle_events(c, 0, 1)
        g.take_actions()
        self.assertEqual(g.model_idx, 0)

        # Raise compute to 2
        for _ in range(2):
            g.place_cube_and_handle_events(c, 0, 0)
            g.take_actions()
        self.assertEqual(g.compute_idx, 2)

        # Attempt to bump model 3 times, but cap at compute (2)
        for _ in range(3):
            g.place_cube_and_handle_events(c, 0, 1)
            g.take_actions()
        self.assertEqual(g.model_idx, 2)

    def test_take_actions_bumps_chaos_on_2_1_and_2_2(self):
        c = self.game.cubes[0]
        self.game.place_cube_and_handle_events(c, 2, 1)
        self.game.take_actions()
        self.assertEqual(self.game.chaos_idx, 1)

        self.game.place_cube_and_handle_events(c, 2, 2)
        self.game.take_actions()
        self.assertEqual(self.game.chaos_idx, 2)

    def test_funds_deduct_on_take_actions(self):
        g = self.game
        start = g.funds.value

        # Place tokens that incur costs but do NOT trigger presence selection
        g.place_cube_and_handle_events(g.cubes[0], 0, 0)  # compute_or_model step 0
        g.place_cube_and_handle_events(g.cubes[1], 0, 1)  # compute_or_model step 2
        g.place_cube_and_handle_events(g.cubes[2], 0, 2)  # lobby step 4
        g.place_cube_and_handle_events(g.cubes[3], 2, 0)  # filler

        g.take_actions()

        # 0 + 2 + 4 = 6 total deduction
        self.assertEqual(g.funds.value, start - 6)

    def test_take_actions_button_disables_when_insufficient_funds(self):
        g = self.game
        # Make user broke
        g.funds.value = 1
        g.funds._update_label()

        # Place all 4 tokens so the button should appear
        final_col = S.GRID_COLS - 1
        g.place_cube_and_handle_events(g.cubes[0], 0, 2)  # lobby (cost at least 4)
        g.place_cube_and_handle_events(g.cubes[1], 1, 0)  # filler
        g.place_cube_and_handle_events(g.cubes[2], 2, 0)  # filler
        g.place_cube_and_handle_events(g.cubes[3], 1, 2)  # filler

        g.update_reset_visibility()

        # Window visible
        self.assertEqual(g.canvas.itemcget(g.take_action_button_window, "state"), "normal")
        # Button disabled
        self.assertEqual(g.take_action_button.cget("state"), "disabled")

    def test_take_actions_with_insufficient_funds_shows_toast_and_noop(self):
        g = self.game
        g.funds.value = 1
        g.funds._update_label()

        # Place one expensive action and three fillers
        g.place_cube_and_handle_events(g.cubes[0], 0, 2)  # lobby first = 4
        g.place_cube_and_handle_events(g.cubes[1], 0, 0)  # compute_or_model might be 0 but fine
        g.place_cube_and_handle_events(g.cubes[2], 1, 0)
        g.place_cube_and_handle_events(g.cubes[3], 2, 0)

        g.update_reset_visibility()
        # Force-click handler regardless of disabled state (call method)
        pre_funds = g.funds.value
        pre_positions = [c.current_cell for c in g.cubes]

        g.take_actions()

        # Funds unchanged, cubes not reset (since we no-op'ed)
        self.assertEqual(g.funds.value, pre_funds)
        self.assertEqual([c.current_cell for c in g.cubes], pre_positions)
        # Toast exists
        self.assertTrue(getattr(g, "toast_id", None))

    def test_presence_selection_flow_and_income(self):
        g = self.game
        # Ensure plenty of funds so the gate doesn't stop us
        g.funds.add(1000)

        # Place one token on [1,1] (scale presence), and one on [0,0] to bump compute
        g.place_cube_and_handle_events(g.cubes[0], 1, 1)
        g.place_cube_and_handle_events(g.cubes[1], 0, 0)

        # Start take_actions -> should enter selection mode
        g.take_actions()
        self.assertTrue(g.selecting_regions)
        self.assertEqual(g.selection_queue, 1)

        # Simulate clicking inside North America hitbox
        name = "North America"
        x0, y0, x1, y1 = g.region_hitboxes[name]
        fake_event = type("E", (), {"x": int((x0 + x1) / 2), "y": int((y0 + y1) / 2)})
        g._maybe_region_click(fake_event)

        # Selection consumed, actions finished
        self.assertFalse(g.selecting_regions)
        self.assertTrue(g.regions.has_presence("North America"))

        # Income: set some reputation/power and run another empty take (to add income)
        g.regions.region_at("North America").reputation = 2
        g.regions.region_at("North America").power = 3
        funds_before = g.funds.value

        # No placements, but finish path still adds income (2*3=6)
        g._finish_take_actions_after_selection()
        self.assertEqual(g.funds.value, funds_before + 6)

    def test_global_buff_on_0_1(self):
        g = self.game
        g.funds.add(1000)
        # Give presence in two regions
        g.regions.add_presence("North America")
        g.regions.add_presence("Asia")
        # Place [0,1] and a filler
        g.place_cube_and_handle_events(g.cubes[0], 0, 1)
        g.place_cube_and_handle_events(g.cubes[1], 0, 0)
        g.take_actions()
        self.assertEqual(g.regions["North America"].reputation, 1)
        self.assertEqual(g.regions["North America"].power, 1)
        self.assertEqual(g.regions["Asia"].reputation, 1)
        self.assertEqual(g.regions["Asia"].power, 1)

    def test_presence_required_effects_and_chaos(self):
        g = self.game
        g.funds.add(1000)

        # Give presence in Europe
        g.regions.add_presence("Europe")
        g._update_region_panel("Europe")

        # Queue actions: [1,0] rep+1, [1,2] power+1, [2,1] power+1/rep-2/chaos+10, [2,2] rep-1/chaos+10
        g.place_cube_and_handle_events(g.cubes[0], 1, 0)
        g.place_cube_and_handle_events(g.cubes[1], 1, 2)
        g.place_cube_and_handle_events(g.cubes[2], 2, 1)
        g.place_cube_and_handle_events(g.cubes[3], 2, 2)

        g.take_actions()
        # Click Europe 4 times to resolve each selection
        x0, y0, x1, y1 = g.region_hitboxes["Europe"]
        evt = type("E", (), {"x": int((x0 + x1) / 2), "y": int((y0 + y1) / 2)})
        for _ in range(4):
            g._maybe_region_click(evt)

        R = g.regions["Europe"]
        self.assertEqual(R.reputation, -2)
        self.assertEqual(R.power, 2)
        self.assertEqual(R.chaos, 20)

        # Panel text reflects the values
        tid = g.region_panel_items["Europe"]["text"]
        txt = g.canvas.itemcget(tid, "text")
        self.assertIn("Region: Europe", txt)
        self.assertIn("Presence: Yes", txt)
        self.assertIn("Power: 2", txt)
        self.assertIn("Reputation: -2", txt)
        self.assertIn(f"Chaos: 20 out of {S.CHAOS_MAX}", txt)


    def test_take_actions_bumps_chaos_on_2_1_and_2_2(self):
        g = self.game
        g.funds.add(1000)
        g.regions.add_presence("Europe")
        g._update_region_panel("Europe")

        # Just one chaos action: [2,1]
        g.place_cube_and_handle_events(g.cubes[0], 2, 1)
        # Fill the rest so button shows (if your UI requires 4 placed)
        g.place_cube_and_handle_events(g.cubes[1], 0, 0)
        g.place_cube_and_handle_events(g.cubes[2], 0, 0)
        g.place_cube_and_handle_events(g.cubes[3], 0, 0)

        g.take_actions()
        x0, y0, x1, y1 = g.region_hitboxes["Europe"]
        evt = type("E", (), {"x": int((x0 + x1) / 2), "y": int((y0 + y1) / 2)})
        g._maybe_region_click(evt)

        R = g.regions["Europe"]
        self.assertEqual(R.chaos, 10)

        tid = g.region_panel_items["Europe"]["text"]
        txt = g.canvas.itemcget(tid, "text")
        self.assertIn(f"Chaos: 10 out of {S.CHAOS_MAX}", txt)



if __name__ == "__main__":
    unittest.main()

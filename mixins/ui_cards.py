# mixins/ui_cards.py
import settings as S

class UICardsMixin:
    def draw_card_area(self):
        self.canvas.create_text(
            S.GRID_ORIGIN_X + 100, S.CARD_AREA_Y - 8,
            text=f"Current Hand Limit: {S.HAND_LIMIT}).",
            anchor="w",
            font=("Helvetica", 12, "bold"),
            fill="black"
        )
        self.canvas.create_rectangle(
            S.CARD_AREA_X, S.CARD_AREA_Y,
            S.CARD_AREA_X + S.CARD_AREA_W, S.CARD_AREA_Y + S.CARD_AREA_H,
            outline="#bbbbc6"
        )
        self.deck_text = self.canvas.create_text(
            S.CARD_AREA_X + S.CARD_AREA_W - 10, S.CARD_AREA_Y + 16,
            text=f"Deck: {len(self.deck)}",
            anchor="e",
            font=("Helvetica", 12)
        )
        self.hand_full_text = self.canvas.create_text(
            S.CARD_AREA_X + 10, S.CARD_AREA_Y + 16,
            text="", anchor="w",
            font=("Helvetica", 12, "italic"), fill="#a00"
        )

        self.hand_slot_ids = []
        start_x = S.CARD_AREA_X + 16
        start_y = S.CARD_AREA_Y + 40

        for i in range(S.HAND_LIMIT):
            r, c = divmod(i, S.HAND_COLS)
            x0 = start_x + c * (S.HAND_SLOT_W + S.HAND_SLOT_GAP_X)
            y0 = start_y + r * (S.HAND_SLOT_H + S.HAND_SLOT_GAP_Y)
            rect_id = self.canvas.create_rectangle(
                x0, y0, x0 + S.HAND_SLOT_W, y0 + S.HAND_SLOT_H, fill="#ffffff", outline="#333"
            )
            text_id = self.canvas.create_text(
                x0 + S.HAND_SLOT_W / 2, y0 + S.HAND_SLOT_H / 2,
                text="—", font=("Helvetica", 18, "bold"), fill="#111"
            )
            self.canvas.tag_raise(text_id, rect_id)
            self.hand_slot_ids.append((rect_id, text_id))

        self.render_hand()

    def draw_card(self):
        if len(self.hand) >= S.HAND_LIMIT:
            self.canvas.itemconfigure(self.hand_full_text, text="Hand is full")
            return
        self.canvas.itemconfigure(self.hand_full_text, text="")

        if not self.deck:
            return

        card = self.deck.pop()
        self.hand.append(card)

        slot_index = len(self.hand) - 1
        if 0 <= slot_index < len(self.hand_slot_ids):
            _, text_id = self.hand_slot_ids[slot_index]
            self.canvas.itemconfigure(text_id, text=str(card), fill="#111")
            self.canvas.tag_raise(text_id)

        self.canvas.itemconfigure(self.deck_text, text=f"Deck: {len(self.deck)}")
        try:
            self.canvas.update_idletasks()
        except Exception:
            pass

    def render_hand(self):
        for i, (_rect_id, text_id) in enumerate(self.hand_slot_ids):
            if i < len(self.hand):
                self.canvas.itemconfigure(text_id, text=str(self.hand[i]), fill="#111")
                self.canvas.tag_raise(text_id)
            else:
                self.canvas.itemconfigure(text_id, text="—", fill="#aaa")

class Funds:
    def __init__(self, start_amount: int, series_map: dict, canvas, x: int, y: int):
        """
        start_amount: starting integer funds
        series_map: dict[str, list[int]] cost progressions
        canvas: Tk canvas to render the label
        x, y: position for the label text
        """
        self.value = int(start_amount)
        self.series_map = {k: list(v) for k, v in series_map.items()}
        self.counters = {k: 0 for k in self.series_map.keys()}
        self.canvas = canvas
        self.pos = (x, y)

        self.label_id = self.canvas.create_text(
            x, y,
            text=self._label_text(),
            anchor="w",
            font=("Helvetica", 12, "bold"),
            fill="black",
        )

    def _label_text(self):
        return f"Current Funds: ${self.value}"

    def _update_label(self):
        self.canvas.itemconfigure(self.label_id, text=self._label_text())

    def charge(self, key: str, times: int = 1):
        """Charge the user 'times' steps of the progression for 'key'. Clamp at 0."""
        if times <= 0:
            return 0
        if key not in self.series_map:
            return 0

        total_cost = 0
        seq = self.series_map[key]
        idx = self.counters[key]

        for _ in range(times):
            step_cost = seq[min(idx, len(seq) - 1)]
            total_cost += step_cost
            idx += 1

        # apply and clamp
        self.counters[key] = idx
        self.value = max(0, self.value - total_cost)
        self._update_label()
        return total_cost

    def add(self, amount: int):
        """Increase funds (positive amount)."""
        if amount:
            self.value = max(0, self.value + int(amount))
            self._update_label()

    def peek_cost(self, key: str, times: int = 1) -> int:
        """Return the total cost for 'times' future uses of 'key' without mutating state."""
        if times <= 0 or key not in self.series_map:
            return 0
        seq = self.series_map[key]
        idx = self.counters[key]
        total = 0
        for _ in range(times):
            total += seq[min(idx, len(seq) - 1)]
            idx += 1
        return total
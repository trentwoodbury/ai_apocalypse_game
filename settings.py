START_AREA_PAD = 8  # inner padding inside the start area box

# Grid layout
GRID_ROWS = 3
GRID_COLS = 4
CELL_SIZE = 140
GRID_PADDING = 20
GRID_ORIGIN_X = 300
GRID_ORIGIN_Y = 40

# Cube layout
CUBE_SIZE = 64
CUBE_GAP = 16
START_AREA_X = 40
START_AREA_Y = 40

# Card/hand display area (unchanged unless you want to tweak)
CARD_AREA_X = GRID_ORIGIN_X
CARD_AREA_W = GRID_COLS * CELL_SIZE

# Hand rendering (2 rows x 4 cols)
HAND_LIMIT = 8
HAND_ROWS = 2
HAND_COLS = 4
HAND_SLOT_W = 70
HAND_SLOT_H = 92
HAND_SLOT_GAP_X = 18
HAND_SLOT_GAP_Y = 14
HAND_TOP_PAD = 40
HAND_BOTTOM_PAD = 24

# Height needed to fully contain the hand area
CARD_AREA_H = HAND_TOP_PAD + HAND_ROWS * HAND_SLOT_H + (HAND_ROWS - 1) * HAND_SLOT_GAP_Y + HAND_BOTTOM_PAD

BOARD_LABELS = [
    # Row 0
    "BUY-CHIPS:\n+1 Compute",
    "TRAIN-NEW-MODEL:\n+1 Reputation\n+1 Power (in all regions with >0 influence)\nPay New Model Cost",
    "SCALE-OPERATIONS:\n+1 Action Token\nPay Scaling Operation Costs",
    "RESEARCH:\nDraw 3 research cards, keep 1 and pay cost",
    # Row 1
    "MARKETING:\n+1 power in 1 region with presence",
    "SCALE-PRESENCE:\n+1 Presence in a new region\nPay Scaling Presence Costs",
    "LOBBY:\n+1 power in a region with presence\nPay $4",
    "INFLUENCE:\nDraw 3 Influence cards, keep 1 and pay cost",
    # Row 2
    "SMEAR-CAMPAIGN:\n-1 reputation to a competitor with presence in the same region as you",
    "MISINFORMATION-CAMPAIGN:\n+1 Chaos\n+1 Power\n-2 Reputation\n(Applies to 1 region with presence)",
    "MALICIOUS-APP:\n+1 Chaos\n-1 Reputation",
    "CHAOS:\nDraw 3 chaos cards, keep 1 and pay cost",
]

# Side image (to the right of the grid)
SIDE_IMAGE_PATH = "images/Continents.jpg"
SIDE_IMAGE_MAX_W = 240  # target width to reserve on the canvas
# height will be clamped to grid height automatically (GRID_ROWS * CELL_SIZE)

# --- Tracker steps (left-to-right indices) ---
COMPUTE_STEPS = [
    "10^8 GigaFLOPs","10^11 GigaFLOPs","10^14 GigaFLOPs","10^18 GigaFLOPs",
    "10^27 GigaFLOPs","10^32 GigaFLOPs","10^40 GigaFLOPs","10^50 GigaFLOPs",
]
MODEL_STEPS   = ["V0","V0.5","V1","V1.5","V2","V3","V3.5","V4"]
CHAOS_STEPS   = [str(x) for x in range(10, 181, 10)]  # 10..180

# --- Space for trackers under the globe (height of 3 rows) ---
TRACKERS_HEIGHT = 120   # approx. 3*row height

# Hand/card area is now pushed further down to make room for trackers:
CARD_AREA_Y = GRID_ORIGIN_Y + GRID_ROWS * CELL_SIZE + 30 + TRACKERS_HEIGHT + 10

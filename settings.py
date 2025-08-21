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
    "MARKETING:\n+1 reputation in 1 region with presence",
    "SCALE-PRESENCE:\n+1 Presence in a new region\nPay Scaling Presence Costs",
    "LOBBY:\n+1 power in a region with presence",
    "INFLUENCE:\nDraw 3 Influence cards, keep 1 and pay cost",
    # Row 2
    "SMEAR-CAMPAIGN:\n-1 reputation to a competitor with presence in the same region as you",
    "MISINFORMATION-CAMPAIGN:\n+1 Chaos\n+1 Power\n-2 Reputation\n(Applies to 1 region with presence)",
    "MALICIOUS-APP:\n+1 Chaos\n-1 Reputation",
    "CHAOS:\nDraw 3 chaos cards, keep 1 and pay cost",
]
# Actions that require selecting a region where the player ALREADY has presence
PRESENCE_REQUIRED_COORDS = {(1,0), (1,2), (2,1), (2,2)}


# Side image (to the right of the grid)
SIDE_IMAGE_PATH = "images/Continents.jpg"
SIDE_IMAGE_MAX_W = 240  # target width to reserve on the canvas
# height will be clamped to grid height automatically (GRID_ROWS * CELL_SIZE)

# --- Tracker steps (left-to-right indices) ---
COMPUTE_STEPS = [
    "10^8 GigaFLOPs","10^11 GigaFLOPs","10^14 GigaFLOPs","10^18 GigaFLOPs",
    "10^27 GigaFLOPs","10^32 GigaFLOPs","10^40 GigaFLOPs","10^50 GigaFLOPs",
]
CHAOS_STEPS   = [x for x in range(10, 181, 10)]  # 10..180
# --- Trackers ---
MODEL_STEPS = ["0","1","2","3","4","5","6","7"]

# --- Action token (operations) tracks ---
OPS_MAX_TOKENS = 4         # total tokens when fully scaled
OPS_START_AVAILABLE = 1    # start with 1 draggable
OPS_START_ASPIRATIONAL = 3 # shown, not draggable

# columns just left of the grid (stacked vertically)
OPS_TRACK_W = 140
OPS_TRACK_H = CELL_SIZE * 3 + 40   # enough for 3-4 discs
OPS_TRACK_PAD = 16
OPS_DISC_R = 22
OPS_DISC_GAP = 16

# Left of grid: two vertical boxes (Aspirational, then Available), side-by-side
OPS_ASP_X = GRID_ORIGIN_X - GRID_PADDING - 2*OPS_TRACK_W - 14
OPS_AVAIL_X = OPS_ASP_X + OPS_TRACK_W + 14
OPS_TRACK_TOP = GRID_ORIGIN_Y

# --- Costs / progressions (displayed in right panel) ---
MODEL_UPGRADE_COSTS = [0, 2, 4, 8, 16, 32, 64, 128]     # for going to model 0..7
SCALING_OPERATION_COSTS = {2: 4, 3: 10, 4: 24}          # shown (no bold logic yet)
SCALING_PRESENCE_COSTS  = [1, 2, 3, 5, 8, 13]           # 1st..6th region

# --- Right-hand requirements panel layout ---
COSTS_PANEL_W = 360
COSTS_PANEL_PAD = 12


# --- Funds / costs ---
FUNDS_START = 10

# Progressive cost sequences (truncate to last value if exceeded)
FUNDS_SERIES = {
    # index [0,2]
    "lobby": [4, 10, 24],
    # index [1,1]
    "scale_presence": [1, 2, 3, 5, 8, 13],
    # indices [0,0] OR [0,1] share the same progression
    "compute_or_model": [0, 2, 4, 8, 16, 32, 64, 128],
    "scale_operations": [4, 10, 24]  # adding action tokens
}

# --- Regions (order matters for drawing & tests) ---
REGION_NAMES = ["North America", "South America", "Europe", "Africa", "Asia", "Oceania"]

# Relative hitboxes over the image (x0,y0,x1,y1) in FRACTIONS of the displayed image
# These are approximate, sized to the colored continents in your provided map.
# You can tweak any tuple if a click feels off.
REGION_BBOXES_FRAC = {
    "North America": (0.02, 0.10, 0.35, 0.44),
    "South America": (0.10, 0.15, 0.45, 0.90),
    "Europe":        (0.42, 0.05, 0.55, 0.26),
    "Africa":        (0.42, 0.26, 0.60, 0.70),
    "Asia":          (0.55, 0.08, 0.90, 0.55),
    "Oceania":       (0.78, 0.55, 0.95, 0.90),
}

# Hex marker visuals
REGION_HEX_RADIUS = 14
REGION_HEX_FILL = "#000000"   # black outline only; fill empty looks cleaner on map
REGION_HEX_OUTLINE = "#111"
REGION_HEX_WIDTH = 3

# Tracker geometry
TRACKER_ROW_H = 36

# We now show: 2 fixed rows (Compute, Model) + one chaos row per region
TRACKERS_EXTRA_ROWS = 2 + len(REGION_NAMES)
TRACKERS_HEIGHT = TRACKER_ROW_H * TRACKERS_EXTRA_ROWS + 16

# Hand/card area sits below all trackers
CARD_AREA_Y = GRID_ORIGIN_Y + GRID_ROWS * CELL_SIZE + 30 + TRACKERS_HEIGHT + 10

# --- Region / chaos display ---
CHAOS_STEP = 10
CHAOS_MAX = 180  # per-region maximum shown in panels
REGION_PANEL_ROWS = 2
REGION_PANEL_COLS = 3
REGION_PANEL_W = 260
REGION_PANEL_H = 110
REGION_PANEL_GAP_X = 16
REGION_PANEL_GAP_Y = 14
REGION_PANELS_TITLE = "Regions"


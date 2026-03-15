# xo/constants.py

# --- SYSTEM & DISPLAY ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WINDOW_TITLE = "Gobblet XO"

# --- DIMENSIONS ---
CELL_SIZE = 120
BOARD_SIZE = 3
# คำนวณตำแหน่งกลางกระดาน (มี Offset Y นิดหน่อยเพื่อให้สมดุลกับหัวข้อด้านบน)
BOARD_OFFSET_X = (SCREEN_WIDTH - (CELL_SIZE * BOARD_SIZE)) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - (CELL_SIZE * BOARD_SIZE)) // 2 + 30

# Font Sizes
FONT_SIZE_S = 20
FONT_SIZE_M = 32
FONT_SIZE_L = 48
FONT_SIZE_XL = 64

# --- COLORS (Modern Palette) ---
# Basic Colors (Helpers)
WHITE = (255, 255, 255)
BLACK = (30, 30, 36)
RED = (255, 0, 0)

# Theme Backgrounds
BG_COLOR = (248, 249, 250)  # Off-white background (สบายตา)
BOARD_BG_COLOR = (233, 236, 239)  # Light Gray for board base
BOARD_SLOT_COLOR = (222, 226, 230)  # Darker slots (หลุม)

# UI Text & Effects
TEXT_COLOR = (52, 58, 64)  # Dark Gray almost black
SUBTEXT_COLOR = (134, 142, 150)  # Muted gray
SHADOW_COLOR = (0, 0, 0, 30)  # Transparent black for shadows

# Player 1 (X) - Blue/Teal Theme
COLOR_P1 = (77, 171, 247)
COLOR_P1_DARK = (51, 154, 240)
COLOR_P1_LIGHT = (165, 216, 255)

# Player 2 (O) - Orange/Coral Theme
COLOR_P2 = (255, 135, 135)
COLOR_P2_DARK = (250, 82, 82)
COLOR_P2_LIGHT = (255, 201, 201)

# Status / Feedback Colors
COLOR_SUCCESS = (81, 207, 102)  # Green (Confirm/Safe)
COLOR_WARNING = (255, 212, 59)  # Yellow (Highlight/Selected)
COLOR_DANGER = (255, 107, 107)  # Red (Cancel/Eat)
COLOR_HOVER = (255, 255, 255, 50)  # White overlay for hover effect

# --- GAME LOGIC ---
PLAYER_X = 1
PLAYER_O = 2

SIZE_SMALL = 1
SIZE_MEDIUM = 2
SIZE_LARGE = 3

# --- NETWORK ---
DEFAULT_PORT = 5555
DISCOVERY_PORT = 5556

# --- GAME STATES ---
# รวม State ทั้งหมดให้ตรงกับ UI และ Logic
STATE_MENU = 0
STATE_PLAYING_PVE = 1
STATE_ENTER_USERNAME_HOST = 2
STATE_ENTER_USERNAME_CLIENT = 3
STATE_LOBBY_HOST = 4
STATE_LOBBY_CLIENT = 5
STATE_ROOM_LIST = 6
STATE_PLAYING_ONLINE = 7
STATE_GAME_OVER = 8

STATE_PLAYING_PVP_CLIENT = 9
STATE_PLAYING_PVP_HOST = 10
STATE_ROOM_LIST_CLIENT = 11
STATE_ROOM_LIST_HOST = 12

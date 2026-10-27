"""Game settings and constants."""

import sys
from pathlib import Path


def _base_dir() -> Path:
    """Game root — works for source runs and PyInstaller one-file builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent


def _user_data_dir() -> Path:
    """Writable location for high score (not inside the frozen bundle)."""
    if getattr(sys, "frozen", False):
        home = Path.home()
        if sys.platform == "win32":
            root = Path(
                __import__("os").environ.get("LOCALAPPDATA", home / "AppData" / "Local")
            )
            d = root / "FlappyBird"
        else:
            d = home / ".local" / "share" / "flappy-bird"
        d.mkdir(parents=True, exist_ok=True)
        return d
    return Path(__file__).parent


# Paths
BASE_DIR = _base_dir()
ASSETS_DIR = BASE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
AUDIO_DIR = ASSETS_DIR / "audio"
HIGHSCORE_PATH = _user_data_dir() / "highscore.txt"

# Window
GAME_WIDTH = 288
GAME_HEIGHT = 512
SCALE = 1.5
WINDOW_WIDTH = int(GAME_WIDTH * SCALE)
WINDOW_HEIGHT = int(GAME_HEIGHT * SCALE)
TITLE = "Flappy Bird"
FPS = 60

# Physics (tuned closer to classic feel)
GRAVITY = 0.40
JUMP_VELOCITY = -7.0
MAX_FALL_SPEED = 9.0

# Bird
BIRD_COLOR = "yellow"  # "blue", "yellow", or "red"
BIRD_FLAP_MS = 120
BIRD_ROTATION_SMOOTH = 0.18
BIRD_MAX_UP_ANGLE = 28
BIRD_MAX_DOWN_ANGLE = -75
BIRD_IDLE_BOB_AMPLITUDE = 6.0  # pixels up/down on title
BIRD_IDLE_BOB_SPEED = 0.006   # radians per ms roughly

# Pipes
PIPE_COLOR = "green"  # "green" or "red"
PIPE_SPEED = 2.4
PIPE_GAP = 112
PIPE_SPAWN_OFFSET = 160  # horizontal gap between pipe columns
PIPE_SPAWN_X = GAME_WIDTH + 8
PIPE_MIN_GAP_Y = 140
PIPE_MAX_GAP_BOTTOM = 100

# Background / ground
BASE_SPEED = PIPE_SPEED

# Death — brief delay before world fully freezes (ms)
DEATH_FREEZE_DELAY_MS = 450

# Score
SCORE_Y = 30
HIGH_SCORE_Y = 70

# Audio (0.0 – 1.0)
SOUND_VOLUME = 0.25

# Colors
WINDOW_BACKGROUND = (78, 192, 201)

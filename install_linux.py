#!/usr/bin/env python3
"""
Flappy Bird — Linux TUI installer
Install / Update / Uninstall as a system-detectable app (rofi, app menus).
Builds a single binary and installs a .desktop launcher.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

APP_NAME = "Flappy Bird"
APP_ID = "flappy-bird"
BIN_NAME = "flappy-bird"

HOME = Path.home()
INSTALL_ROOT = HOME / ".local" / "share" / "flappy-bird"
VENV_DIR = INSTALL_ROOT / "venv"
BIN_DIR = HOME / ".local" / "bin"
BIN_PATH = BIN_DIR / BIN_NAME
DESKTOP_DIR = HOME / ".local" / "share" / "applications"
DESKTOP_FILE = DESKTOP_DIR / f"{APP_ID}.desktop"
ICON_PATH = INSTALL_ROOT / "icon.png"

SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_ZIP = SCRIPT_DIR / "Installer" / "Flappy_Bird_Fixed.zip"
GAME_DIR = SCRIPT_DIR / "Game"


# ---------------------------------------------------------------------------
# Terminal UI
# ---------------------------------------------------------------------------

def clear() -> None:
    os.system("clear" if os.name != "nt" else "cls")


def pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(msg)
    except EOFError:
        pass


def menu() -> str:
    clear()
    print("╔══════════════════════════════════════╗")
    print("║     Welcome to Flappy Bird!          ║")
    print("╠══════════════════════════════════════╣")
    print("║                                      ║")
    print("║   1) Install                         ║")
    print("║   2) Update                          ║")
    print("║   3) Uninstall                       ║")
    print("║   4) Quit                            ║")
    print("║                                      ║")
    print("╚══════════════════════════════════════╝")
    print()
    if is_installed():
        print(f"  Status: installed → {BIN_PATH}")
    else:
        print("  Status: not installed")
    print()
    while True:
        choice = input("  Select [1-4]: ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        print("  Invalid choice.")


def info(msg: str) -> None:
    print(f"  → {msg}")


def error(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_installed() -> bool:
    return BIN_PATH.is_file() or DESKTOP_FILE.is_file()


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    print(f"    $ {' '.join(str(c) for c in cmd)}")
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None, env=env)


def find_game_dir() -> Path:
    """Prefer local Game/ folder; otherwise extract from zip into a temp dest."""
    if (GAME_DIR / "main.py").is_file():
        return GAME_DIR
    # fallback: zip in Installer/ or beside script
    candidates = [
        LOCAL_ZIP,
        SCRIPT_DIR / "Flappy_Bird_Fixed.zip",
        SCRIPT_DIR / "Installer" / "Flappy_Bird_Fixed.zip",
        Path.cwd() / "Flappy_Bird_Fixed.zip",
    ]
    zip_path = next((p for p in candidates if p.is_file()), None)
    if zip_path is None:
        raise FileNotFoundError(
            "Game source not found.\n"
            "Expected Game/main.py next to the installer, or a zip in Installer/."
        )
    dest = INSTALL_ROOT / "src"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    mains = list(dest.rglob("main.py"))
    if not mains:
        raise RuntimeError("main.py not found inside the zip.")
    return mains[0].parent


def venv_python() -> Path:
    return VENV_DIR / "bin" / "python"


def ensure_build_env(system_python: str) -> str:
    """Create a local venv and install pygame + PyInstaller into it (PEP 668 safe)."""
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    py = venv_python()
    if not py.is_file():
        info(f"Creating virtualenv at {VENV_DIR} ...")
        run([system_python, "-m", "venv", str(VENV_DIR)])
    info("Installing pygame + PyInstaller into the venv...")
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "--upgrade", "pygame", "pyinstaller"])
    return str(py)


def build_binary(game_dir: Path, out_dir: Path, python: str) -> Path:
    """Build a one-file binary with PyInstaller; return path to binary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="flappy_build_"))
    try:
        cmd = [
            python, "-m", "PyInstaller",
            "--onefile",
            "--noconfirm",
            "--clean",
            "--name", BIN_NAME,
            "--distpath", str(out_dir),
            "--workpath", str(work / "build"),
            "--specpath", str(work),
            "--paths", str(game_dir),
            # bundle assets so runtime finds them under sys._MEIPASS/assets
            "--add-data", f"{game_dir / 'assets'}{os.pathsep}assets",
            str(game_dir / "main.py"),
        ]
        for mod in ("window", "bird", "pipe", "background", "score", "message", "input", "colors", "settings"):
            if (game_dir / f"{mod}.py").is_file():
                cmd.extend(["--hidden-import", mod])
        run(cmd, cwd=game_dir)
        binary = out_dir / BIN_NAME
        if not binary.is_file():
            raise RuntimeError(f"PyInstaller did not produce {binary}")
        binary.chmod(binary.stat().st_mode | 0o755)
        return binary
    finally:
        shutil.rmtree(work, ignore_errors=True)


def install_icon(game_dir: Path) -> None:
    """Convert favicon.ico → icon.png if possible, else copy ico."""
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    ico = game_dir / "assets" / "favicon.ico"
    # Prefer a sprite as PNG icon if available
    bird = game_dir / "assets" / "sprites" / "yellowbird-midflap.png"
    if bird.is_file():
        shutil.copy2(bird, ICON_PATH)
        ok(f"Icon: {ICON_PATH}")
        return
    if ico.is_file():
        shutil.copy2(ico, INSTALL_ROOT / "icon.ico")
        ok("Icon: favicon.ico copied")
        return
    info("No icon found (optional).")


def write_desktop_entry() -> None:
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    icon = str(ICON_PATH) if ICON_PATH.is_file() else "applications-games"
    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=Flappy Bird clone
Exec={BIN_PATH}
Icon={icon}
Terminal=false
Categories=Game;ArcadeGame;
StartupNotify=true
Keywords=flappy;bird;game;
"""
    DESKTOP_FILE.write_text(content, encoding="utf-8")
    DESKTOP_FILE.chmod(DESKTOP_FILE.stat().st_mode | 0o644)
    # Update desktop database if tools exist
    for tool in ("update-desktop-database",):
        if shutil.which(tool):
            try:
                subprocess.call([tool, str(DESKTOP_DIR)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass
    ok(f"Desktop entry: {DESKTOP_FILE}")


def install_binary(built: Path) -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, BIN_PATH)
    BIN_PATH.chmod(BIN_PATH.stat().st_mode | 0o755)
    ok(f"Binary: {BIN_PATH}")


def path_hint() -> None:
    path_env = os.environ.get("PATH", "")
    if str(BIN_DIR) not in path_env.split(os.pathsep):
        print()
        info(f"Add to PATH (put in ~/.bashrc or ~/.zshrc):")
        print(f'    export PATH="$HOME/.local/bin:$PATH"')
        print()


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def do_install(update: bool = False) -> None:
    clear()
    print("╔══════════════════════════════════════╗")
    print(f"║  {'Updating' if update else 'Installing'} Flappy Bird...          ║")
    print("╚══════════════════════════════════════╝")
    print()

    if not update and is_installed():
        info("Already installed. Use Update, or Uninstall first.")
        pause()
        return

    python = sys.executable
    info(f"Python: {python}")

    try:
        info("Preparing build environment (venv)...")
        build_python = ensure_build_env(python)

        info("Locating game source...")
        game_dir = find_game_dir()
        ok(f"Source: {game_dir}")

        install_icon(game_dir)

        build_out = INSTALL_ROOT / "build_out"
        info("Building single binary (this can take a minute)...")
        binary = build_binary(game_dir, build_out, build_python)
        install_binary(binary)

        write_desktop_entry()
        path_hint()

        print()
        ok(f"{APP_NAME} is ready.")
        print(f"  Run from terminal:  {BIN_NAME}")
        print(f"  Or search in your app menu / rofi:  {APP_NAME}")
        print()
    except subprocess.CalledProcessError as e:
        error(f"Command failed (exit {e.returncode}).")
    except Exception as e:
        error(str(e))
    pause()


def do_uninstall() -> None:
    clear()
    print("╔══════════════════════════════════════╗")
    print("║  Uninstall Flappy Bird               ║")
    print("╚══════════════════════════════════════╝")
    print()
    if not is_installed() and not INSTALL_ROOT.exists():
        info("Nothing to uninstall.")
        pause()
        return

    confirm = input("  Type YES to uninstall: ").strip()
    if confirm != "YES":
        info("Cancelled.")
        pause()
        return

    for path in (BIN_PATH, DESKTOP_FILE):
        if path.is_file():
            path.unlink()
            ok(f"Removed {path}")
    if INSTALL_ROOT.exists():
        shutil.rmtree(INSTALL_ROOT)
        ok(f"Removed {INSTALL_ROOT}")

    if shutil.which("update-desktop-database"):
        try:
            subprocess.call(
                ["update-desktop-database", str(DESKTOP_DIR)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass

    print()
    ok("Uninstall complete.")
    pause()


def main() -> None:
    if sys.platform == "win32":
        print("This is the Linux installer. On Windows use install_windows.py / install.bat")
        sys.exit(1)

    while True:
        choice = menu()
        if choice == "1":
            do_install(update=False)
        elif choice == "2":
            do_install(update=True)
        elif choice == "3":
            do_uninstall()
        else:
            clear()
            print("Bye.")
            break


if __name__ == "__main__":
    main()

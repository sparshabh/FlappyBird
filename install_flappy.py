#!/usr/bin/env python3
"""
Flappy Bird installer (cross-platform).
Downloads the game (optional URL) and installs pygame.

Usage:
  python install_flappy.py
  python install_flappy.py --url https://example.com/Flappy_Bird_Fixed.zip
  python install_flappy.py --dir ~/Games/FlappyBird
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

# Default download URL — replace with your hosted zip if you publish one
DEFAULT_GAME_URL = os.environ.get("GAME_URL", "")

REQUIREMENTS = ["pygame>=2.5.0"]


def run(cmd: list[str]) -> None:
    print("  $", " ".join(cmd))
    subprocess.check_call(cmd)


def find_python() -> str:
    return sys.executable


def install_requirements(python: str) -> None:
    print("\n[3/4] Installing requirements...")
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    run([python, "-m", "pip", "install", *REQUIREMENTS])


def download_and_extract(url: str, dest: Path) -> Path:
    print(f"\n[2/4] Downloading game from:\n  {url}")
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        urlretrieve(url, tmp_path)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(dest)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Find main.py inside extract tree
    mains = list(dest.rglob("main.py"))
    if not mains:
        raise SystemExit("Download/extract OK but main.py was not found in the zip.")
    return mains[0].parent


def make_launchers(game_dir: Path, python: str) -> None:
    print("\n[4/4] Creating launchers...")
    if os.name == "nt":
        bat = game_dir / "run.bat"
        bat.write_text(
            f'@echo off\ncd /d "{game_dir}"\n"{python}" main.py\nif errorlevel 1 pause\n',
            encoding="utf-8",
        )
        print(f"  Created {bat}")
    else:
        sh = game_dir / "run.sh"
        sh.write_text(
            f'#!/usr/bin/env bash\ncd "{game_dir}"\nexec "{python}" main.py\n',
            encoding="utf-8",
        )
        sh.chmod(sh.stat().st_mode | 0o111)
        print(f"  Created {sh}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Flappy Bird + dependencies")
    parser.add_argument(
        "--url",
        default=DEFAULT_GAME_URL,
        help="URL of Flappy_Bird_Fixed.zip (or set GAME_URL env)",
    )
    parser.add_argument(
        "--dir",
        default="",
        help="Install directory (default: ./FlappyBird next to this script)",
    )
    parser.add_argument(
        "--local-zip",
        default="",
        help="Path to a local Flappy_Bird_Fixed.zip instead of downloading",
    )
    args = parser.parse_args()

    print("==================================")
    print("  Flappy Bird — Installer")
    print("==================================")

    python = find_python()
    print(f"\n[1/4] Using {python}")
    print(f"       {sys.version.split()[0]}")

    script_dir = Path(__file__).resolve().parent
    install_root = Path(args.dir).expanduser() if args.dir else script_dir / "FlappyBird"

    game_dir: Path | None = None

    # Prefer local zip, then URL, then existing folder next to script
    local_zip = Path(args.local_zip) if args.local_zip else script_dir / "Flappy_Bird_Fixed.zip"
    if local_zip.is_file():
        print(f"\n[2/4] Using local zip: {local_zip}")
        install_root.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(local_zip, "r") as zf:
            zf.extractall(install_root)
        mains = list(install_root.rglob("main.py"))
        if not mains:
            raise SystemExit("Zip extracted but main.py not found.")
        game_dir = mains[0].parent
    elif args.url:
        game_dir = download_and_extract(args.url, install_root)
    else:
        # Already extracted game?
        candidates = list(script_dir.rglob("main.py"))
        if candidates:
            game_dir = candidates[0].parent
            print(f"\n[2/4] Found existing game at {game_dir}")
        else:
            print(
                "\nError: no game sources found.\n"
                "  • Put Flappy_Bird_Fixed.zip next to this installer, or\n"
                "  • Pass --local-zip path/to/zip, or\n"
                "  • Pass --url https://.../Flappy_Bird_Fixed.zip\n"
            )
            raise SystemExit(1)

    assert game_dir is not None
    os.chdir(game_dir)

    # Prefer game requirements.txt if present
    req = game_dir / "requirements.txt"
    print("\n[3/4] Installing requirements...")
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    if req.is_file():
        run([python, "-m", "pip", "install", "-r", str(req)])
    else:
        run([python, "-m", "pip", "install", *REQUIREMENTS])

    make_launchers(game_dir, python)

    print("\nDone.")
    if os.name == "nt":
        print(f'  Start:  "{game_dir / "run.bat"}"')
    else:
        print(f'  Start:  "{game_dir / "run.sh"}"')
    print(f'  Or:     cd "{game_dir}" && python main.py')
    print()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)

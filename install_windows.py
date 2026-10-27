#!/usr/bin/env python3
"""
Flappy Bird — Windows GUI installer
Installs a single-file .exe, Start Menu entry, optional Desktop shortcut.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    print("tkinter is required for the GUI installer.")
    sys.exit(1)

APP_NAME = "Flappy Bird"
APP_ID = "FlappyBird"
EXE_NAME = "FlappyBird.exe"

SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_ZIP = SCRIPT_DIR / "Installer" / "Flappy_Bird_Fixed.zip"
GAME_DIR = SCRIPT_DIR / "Game"

# Per-user install (no admin required)
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
INSTALL_ROOT = LOCALAPPDATA / "Programs" / APP_ID
EXE_PATH = INSTALL_ROOT / EXE_NAME
START_MENU = (
    Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    / "Microsoft"
    / "Windows"
    / "Start Menu"
    / "Programs"
)
START_MENU_LNK = START_MENU / f"{APP_NAME}.lnk"
DESKTOP = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
DESKTOP_LNK = DESKTOP / f"{APP_NAME}.lnk"


def is_installed() -> bool:
    return EXE_PATH.is_file()


def find_game_dir() -> Path:
    if (GAME_DIR / "main.py").is_file():
        return GAME_DIR
    candidates = [
        LOCAL_ZIP,
        SCRIPT_DIR / "Flappy_Bird_Fixed.zip",
        SCRIPT_DIR / "Installer" / "Flappy_Bird_Fixed.zip",
        Path.cwd() / "Flappy_Bird_Fixed.zip",
    ]
    zip_path = next((p for p in candidates if p.is_file()), None)
    if zip_path is None:
        raise FileNotFoundError(
            "Game source not found. Expected Game/main.py or a zip in Installer/."
        )
    dest = INSTALL_ROOT / "src"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    mains = list(dest.rglob("main.py"))
    if not mains:
        raise RuntimeError("main.py not found in zip.")
    return mains[0].parent


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None, shell=False)


def ensure_tools() -> None:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "pyinstaller", "pygame"])


def build_exe(game_dir: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="flappy_win_build_"))
    try:
        sep = ";"  # Windows PyInstaller add-data separator
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconfirm",
            "--clean",
            "--windowed",  # no console flash
            "--name", "FlappyBird",
            "--distpath", str(out_dir),
            "--workpath", str(work / "build"),
            "--specpath", str(work),
            "--paths", str(game_dir),
            "--add-data", f"{game_dir / 'assets'}{sep}assets",
        ]
        icon = game_dir / "assets" / "favicon.ico"
        if icon.is_file():
            cmd.extend(["--icon", str(icon)])
        for mod in ("window", "bird", "pipe", "background", "score", "message", "input", "colors", "settings"):
            if (game_dir / f"{mod}.py").is_file():
                cmd.extend(["--hidden-import", mod])
        cmd.append(str(game_dir / "main.py"))
        run(cmd, cwd=game_dir)
        exe = out_dir / EXE_NAME
        if not exe.is_file():
            # PyInstaller may use name without forcing .exe in list_dir on some setups
            candidates = list(out_dir.glob("FlappyBird*"))
            if not candidates:
                raise RuntimeError("PyInstaller did not produce the exe.")
            exe = candidates[0]
        return exe
    finally:
        shutil.rmtree(work, ignore_errors=True)


def create_shortcut(lnk_path: Path, target: Path, icon: Path | None = None) -> None:
    """Create a .lnk via PowerShell (no extra packages)."""
    lnk_path.parent.mkdir(parents=True, exist_ok=True)
    icon_arg = str(icon) if icon and icon.is_file() else str(target)
    ps = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{lnk_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.WorkingDirectory = "{target.parent}"
$Shortcut.IconLocation = "{icon_arg}"
$Shortcut.Description = "{APP_NAME}"
$Shortcut.Save()
'''
    subprocess.check_call(
        ["powershell", "-NoProfile", "-Command", ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def uninstall_files() -> None:
    for p in (EXE_PATH, START_MENU_LNK, DESKTOP_LNK):
        if p.is_file():
            p.unlink()
    if INSTALL_ROOT.exists():
        shutil.rmtree(INSTALL_ROOT, ignore_errors=True)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class InstallerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} Setup")
        self.geometry("480x360")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        self.desktop_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Welcome to Flappy Bird Setup")
        self.busy = False

        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg="#4a90d9", height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=f"  {APP_NAME}",
            font=("Segoe UI", 18, "bold"),
            bg="#4a90d9",
            fg="white",
            anchor="w",
        ).pack(fill="both", expand=True, padx=16)

        body = tk.Frame(self, bg="#f0f0f0", padx=24, pady=16)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="This will install Flappy Bird as a standalone app\n"
                 "under your user Programs folder.",
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        self.chk = tk.Checkbutton(
            body,
            text="Create a Desktop shortcut",
            variable=self.desktop_var,
            bg="#f0f0f0",
            font=("Segoe UI", 10),
        )
        self.chk.pack(anchor="w", pady=(0, 16))

        self.progress = ttk.Progressbar(body, mode="indeterminate", length=400)
        self.progress.pack(pady=(0, 8))

        tk.Label(
            body,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#333",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        btn_row = tk.Frame(body, bg="#f0f0f0")
        btn_row.pack(fill="x", side="bottom")

        self.btn_install = tk.Button(
            btn_row, text="Install", width=12, command=self.on_install, font=("Segoe UI", 10)
        )
        self.btn_install.pack(side="left", padx=(0, 8))

        self.btn_update = tk.Button(
            btn_row, text="Update", width=12, command=self.on_update, font=("Segoe UI", 10)
        )
        self.btn_update.pack(side="left", padx=(0, 8))

        self.btn_uninstall = tk.Button(
            btn_row, text="Uninstall", width=12, command=self.on_uninstall, font=("Segoe UI", 10)
        )
        self.btn_uninstall.pack(side="left", padx=(0, 8))

        tk.Button(
            btn_row, text="Close", width=10, command=self.destroy, font=("Segoe UI", 10)
        ).pack(side="right")

    def _refresh_status(self) -> None:
        if is_installed():
            self.status_var.set(f"Installed at:\n{EXE_PATH}")
            self.btn_install.config(state="disabled")
            self.btn_update.config(state="normal")
            self.btn_uninstall.config(state="normal")
        else:
            self.status_var.set("Not installed. Click Install to begin.")
            self.btn_install.config(state="normal")
            self.btn_update.config(state="disabled")
            self.btn_uninstall.config(state="disabled")

    def _set_busy(self, busy: bool, msg: str = "") -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for b in (self.btn_install, self.btn_update, self.btn_uninstall):
            b.config(state=state)
        if busy:
            self.progress.start(12)
            if msg:
                self.status_var.set(msg)
        else:
            self.progress.stop()
            self._refresh_status()

    def on_install(self) -> None:
        if self.busy:
            return
        self._run_task(update=False)

    def on_update(self) -> None:
        if self.busy:
            return
        self._run_task(update=True)

    def on_uninstall(self) -> None:
        if self.busy:
            return
        if not messagebox.askyesno("Uninstall", f"Remove {APP_NAME} from this PC?"):
            return
        try:
            uninstall_files()
            messagebox.showinfo("Uninstall", f"{APP_NAME} was removed.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self._refresh_status()

    def _run_task(self, update: bool) -> None:
        self._set_busy(True, "Preparing... (building the game can take a minute)")

        def worker() -> None:
            err: str | None = None
            try:
                self._install_core(update=update)
            except Exception as e:
                err = str(e)

            def done() -> None:
                self._set_busy(False)
                if err:
                    messagebox.showerror("Install failed", err)
                else:
                    messagebox.showinfo(
                        "Done",
                        f"{APP_NAME} is installed.\n\n"
                        f"Location:\n{EXE_PATH}\n\n"
                        "Find it in the Start Menu"
                        + (" and on the Desktop." if self.desktop_var.get() else "."),
                    )
                self._refresh_status()

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _install_core(self, update: bool) -> None:
        def status(msg: str) -> None:
            self.after(0, lambda: self.status_var.set(msg))

        status("Installing build tools (pip, PyInstaller, pygame)...")
        ensure_tools()

        status("Locating game source...")
        game_dir = find_game_dir()

        status("Building standalone .exe (please wait)...")
        build_out = INSTALL_ROOT / "build_out"
        built = build_exe(game_dir, build_out)

        status("Installing...")
        INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
        # Normalize to EXE_PATH
        if built.resolve() != EXE_PATH.resolve():
            shutil.copy2(built, EXE_PATH)

        # Copy icon next to exe for shortcuts
        icon_src = game_dir / "assets" / "favicon.ico"
        icon_dst = INSTALL_ROOT / "icon.ico"
        if icon_src.is_file():
            shutil.copy2(icon_src, icon_dst)

        status("Creating Start Menu shortcut...")
        create_shortcut(START_MENU_LNK, EXE_PATH, icon_dst if icon_dst.is_file() else None)

        if self.desktop_var.get():
            status("Creating Desktop shortcut...")
            create_shortcut(DESKTOP_LNK, EXE_PATH, icon_dst if icon_dst.is_file() else None)
        elif DESKTOP_LNK.is_file():
            DESKTOP_LNK.unlink()

        status("Done.")


def main() -> None:
    if sys.platform != "win32":
        print("This is the Windows GUI installer. On Linux use install_linux.py / install.sh")
        # Still allow opening GUI for testing on non-Windows if needed
    app = InstallerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

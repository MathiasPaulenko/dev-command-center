"""Manual E2E walkthrough for DevCommandCenter (pywinauto/UIA).

Launches the real GUI with an isolated database (DCC_DATABASE_URL) and drives
it like a user: run/stop commands, open log windows, dialogs, filters, menus.
Saves screenshots to e2e_artifacts/.

Usage:
    .venv/Scripts/python scripts/manual_e2e.py
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from pywinauto import Desktop, mouse

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "e2e_artifacts"
APP_TITLE = "DevCommandCenter"

tmp = tempfile.mkdtemp(prefix="dcc_e2e_")
env = os.environ.copy()
env["DCC_DATABASE_URL"] = f"sqlite:///{tmp}/e2e.db"
env["QT_ACCESSIBILITY"] = "1"

proc = subprocess.Popen([sys.executable, "main.py"], env=env, cwd=ROOT)
desktop = Desktop(backend="uia")


def shot(name: str, win=None) -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    (win or main).capture_as_image().save(ARTIFACTS / f"{name}.png")
    print(f"  [shot] {name}.png")


def bring_to_front() -> None:
    """SetForegroundWindow via AttachThreadInput (raw call is restricted)."""
    u = ctypes.windll.user32
    fg = u.GetForegroundWindow()
    cur = ctypes.windll.kernel32.GetCurrentThreadId()
    tgt = u.GetWindowThreadProcessId(fg, None)
    u.AttachThreadInput(cur, tgt, True)
    u.BringWindowToTop(main.handle)
    u.SetForegroundWindow(main.handle)
    u.AttachThreadInput(cur, tgt, False)


def click(el) -> None:
    """UIA Invoke first (works unfocused); mouse click as fallback."""
    try:
        el.invoke()
    except Exception:
        bring_to_front()
        time.sleep(0.3)
        el.click_input()


# Vertical offsets of each item in the card ⋮ menu, measured from the
# bottom edge of the ⋮ button (the popup opens at its bottom-left corner).
CARD_MENU_OFFSETS = {
    "Logs": 22, "History": 59, "Edit": 101, "Duplicate": 133, "Delete": 178,
}


def card_click(card_name: str, btn_title: str) -> None:
    """Physical click on a card button (invoke() is flaky on fresh cards)."""
    btn = card_button(card_name, btn_title)
    r = btn.rectangle()
    bring_to_front()
    time.sleep(0.2)
    mouse.click(button="left", coords=((r.left + r.right) // 2, (r.top + r.bottom) // 2))


def open_card_menu(card_name: str) -> None:
    """Open the ⋮ menu of a card (popup is not exposed to UIA — use mouse)."""
    btn = card_button(card_name, "⋮")
    r = btn.rectangle()
    bring_to_front()
    time.sleep(0.2)
    mouse.click(button="left", coords=((r.left + r.right) // 2, (r.top + r.bottom) // 2))
    time.sleep(0.4)


def click_menu_item(item_title: str, card_name: str = "Hello World") -> bool:
    """Click an item of the open card ⋮ menu by coordinates."""
    btn = card_button(card_name, "⋮")
    r = btn.rectangle()
    mouse.click(button="left", coords=(r.left + 65, r.bottom + CARD_MENU_OFFSETS[item_title]))
    time.sleep(0.4)
    return True


def find_top_window(title_re: str, timeout: float = 10):
    """Find a dialog/log window — Qt child windows appear as Window-type
    descendants of the main window, not as top-level UIA windows."""
    import re
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            for e in main.descendants(control_type="Window"):
                if e.window_text() and re.search(title_re, e.window_text()):
                    return e
        except Exception:
            pass
        try:
            w = desktop.window(title_re=title_re)
            if w.exists() and w.is_visible():
                return w
        except Exception:
            pass
        time.sleep(0.3)
    raise TimeoutError(f"window {title_re!r} not found")


def close_child_window(win) -> None:
    """Close a Qt child window (WindowPattern or its title-bar X button)."""
    try:
        win.close()
        return
    except Exception:
        pass
    for b in win.descendants(control_type="Button"):
        if b.window_text() in ("Cerrar", "Close", "×", "X"):
            try:
                b.invoke()
            except Exception:
                b.click_input()
            return


def _child_windows() -> list:
    """Qt child windows (log windows, dialogs) appear as Window descendants."""
    return [e for e in main.descendants(control_type="Window") if e.window_text()]


def card_button(card_name: str, btn_title: str):
    """Locate a card's button by proximity to the card's name label."""
    kids = [w.rectangle() for w in _child_windows()]
    names = []
    for e in main.descendants(control_type="Text"):
        if e.window_text() != card_name:
            continue
        r = e.rectangle()
        # skip matches that live inside a child window (e.g. log header)
        if any(k.left <= r.left <= k.right and k.top <= r.top <= k.bottom for k in kids):
            continue
        names.append(e)
    assert names, f"card {card_name!r} not found"
    nr = names[0].rectangle()
    # The card's own buttons are the ones with the smallest left edge that is
    # still to the right of the name label — the next card's buttons also fall
    # inside a generous bounding box, so we take the nearest match.
    candidates = []
    for e in main.descendants(control_type="Button"):
        if e.window_text() == btn_title:
            r = e.rectangle()
            if r.left > nr.left - 30 and nr.top - 10 < r.top < nr.top + 280:
                candidates.append(e)
    assert candidates, f"button {btn_title!r} for card {card_name!r} not found"
    return min(candidates, key=lambda e: e.rectangle().left)


def card_badge(card_name: str) -> str:
    names = [
        e for e in main.descendants(control_type="Text")
        if e.window_text() == card_name
    ]
    nr = names[0].rectangle()
    for e in main.descendants(control_type="Text"):
        if e.window_text() in ("Running", "Stopped", "Failed"):
            r = e.rectangle()
            if r.left > nr.left and abs(r.top - nr.top) < 10:
                return e.window_text()
    return "?"


def wait_badge(card_name: str, want: str, timeout: float = 15) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = card_badge(card_name)
        if state == want:
            return state
        time.sleep(0.4)
    raise AssertionError(f"{card_name}: expected {want}, still {card_badge(card_name)}")


def running_count() -> str:
    for e in main.descendants(control_type="Text"):
        if "running" in (e.window_text() or ""):
            return e.window_text()
    return "?"


try:
    main = find_top_window(f"^{APP_TITLE}$")
    main.set_focus()
    print(f"app up (pid {proc.pid}), db={tmp}")

    # ── 1. Main window: two seed commands ────────────────────────────
    assert card_badge("Hello World") == "Stopped"
    assert card_badge("List Files") == "Stopped"
    assert running_count() == "0 running"
    shot("01_main")

    # ── 2. Run "Hello World" ─────────────────────────────────────────
    card_click("Hello World", "Run")
    wait_badge("Hello World", "Running")
    print("  Hello World -> Running |", running_count())
    shot("02_running")
    wait_badge("Hello World", "Stopped", timeout=20)
    print("  Hello World -> Stopped (finished ok)")
    shot("03_finished")

    # ── 3. Card menu -> Logs ─────────────────────────────────────────
    open_card_menu("Hello World")
    assert click_menu_item("Logs", "Hello World"), "card menu Logs item not found"
    log_win = find_top_window(r".*Logs: Hello World")
    time.sleep(0.8)
    print("  log window open")
    shot("04_logs", log_win)

    # Close and reopen — the window must come back with signals connected
    close_child_window(log_win)
    time.sleep(0.5)
    open_card_menu("Hello World")
    assert click_menu_item("Logs", "Hello World"), "card menu Logs item not found on reopen"
    log_win2 = find_top_window(r".*Logs: Hello World")
    time.sleep(0.5)
    print("  log window reopened ok")
    close_child_window(log_win2)

    # ── 4. New Command dialog ────────────────────────────────────────
    click(main.child_window(title="+ New Command", control_type="Button").wrapper_object())
    dlg = find_top_window("^New Command$")
    time.sleep(0.5)
    edits = dlg.descendants(control_type="Edit")
    # Order: name, desc(Text), wd, command, args, env(Text)
    edits[0].set_edit_text("E2E Slow")
    edits[2].set_edit_text(str(ROOT))
    edits[3].set_edit_text("python")
    edits[4].set_edit_text('["-c", "import time; print(\'start\'); time.sleep(60); print(\'done\')"]')
    shot("05_new_command", dlg)
    for b in dlg.descendants(control_type="Button"):
        if b.window_text() == "Save":
            click(b)
            break
    time.sleep(1.0)
    assert card_badge("E2E Slow") == "Stopped"
    print("  E2E Slow card created")

    # ── 5. Run + manual Stop -> must show Stopped, NOT Failed ────────
    card_click("E2E Slow", "Run")
    wait_badge("E2E Slow", "Running")
    assert running_count() == "1 running"
    shot("06_slow_running")
    card_click("E2E Slow", "Stop")
    final = wait_badge("E2E Slow", "Stopped", timeout=12)
    assert final == "Stopped", f"manual stop marked as {final} (bug not fixed)"
    print("  manual stop -> Stopped (not Failed) |", running_count())

    # ── 6. Filters ───────────────────────────────────────────────────
    click(main.child_window(title="Failed", control_type="Button").wrapper_object())
    time.sleep(0.5)
    failed_visible = [
        e for e in main.descendants(control_type="Text")
        if e.window_text() in ("Hello World", "List Files", "E2E Slow")
        and e.is_visible()
    ]
    assert not failed_visible, f"cards still visible under Failed filter: {failed_visible}"
    click(main.child_window(title="All", control_type="Button").wrapper_object())
    time.sleep(0.5)
    print("  filters ok")

    # ── 7. Search ────────────────────────────────────────────────────
    search = main.child_window(control_type="Edit").wrapper_object()
    search.set_edit_text("hello")
    time.sleep(0.6)
    visible_names = {
        e.window_text() for e in main.descendants(control_type="Text")
        if e.window_text() in ("Hello World", "List Files", "E2E Slow")
    }
    assert visible_names == {"Hello World"}, f"search broken: {visible_names}"
    search.set_edit_text("")
    time.sleep(0.5)
    print("  search ok")

    # ── 8. History dialog ────────────────────────────────────────────
    open_card_menu("Hello World")
    assert click_menu_item("History", "Hello World"), "card menu History item not found"
    hist = find_top_window(r".*Execution History: Hello World")
    time.sleep(0.5)
    shot("07_history", hist)
    for b in hist.descendants(control_type="Button"):
        if b.window_text() == "Close":
            click(b)
            break
    print("  history dialog ok")

    # ── 9. About dialog via Help menu ────────────────────────────────
    hb = main.child_window(title="Help", control_type="MenuItem").wrapper_object()
    hr = hb.rectangle()
    bring_to_front(); time.sleep(0.2)
    mouse.click(button="left", coords=((hr.left + hr.right) // 2, (hr.top + hr.bottom) // 2))
    time.sleep(0.4)
    # About is the only item in the Help popup (also a non-UIA QMenu)
    mouse.click(button="left", coords=(hr.left + 30, hr.bottom + 20))
    time.sleep(0.4)
    about = find_top_window(r"^About DevCommandCenter$")
    time.sleep(0.5)
    shot("08_about", about)
    for b in about.descendants(control_type="Button"):
        if b.window_text() == "Close":
            click(b)
            break
    print("  about dialog ok")

    # ── 10. Delete "E2E Slow" ────────────────────────────────────────
    open_card_menu("E2E Slow")
    assert click_menu_item("Delete", "E2E Slow"), "card menu Delete item not found"
    confirm = find_top_window(r"^Confirm$")
    for b in confirm.descendants(control_type="Button"):
        if b.window_text() in ("Yes", "&Yes", "Sí", "&Sí"):
            click(b)
            break
    time.sleep(0.8)
    remaining = [
        e for e in main.descendants(control_type="Text")
        if e.window_text() == "E2E Slow"
    ]
    assert not remaining, "E2E Slow card still present after delete"
    print("  delete ok")

    shot("09_final")
    print("\nALL MANUAL CHECKS PASSED")

finally:
    try:
        main.close()
        proc.wait(timeout=8)
    except Exception:
        proc.kill()

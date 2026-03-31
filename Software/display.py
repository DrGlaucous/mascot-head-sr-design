"""
display.py – Gaze Position Display

Draws a black circle at the position provided by a shared [x, y] list,
updated externally by the eye-tracker thread. Runs fullscreen at 60 FPS.

Usage:
    gaze_pos = [0.0, 0.0]                  # shared with eye-tracker thread
    display = GazeDisplay(gaze_pos)
    display.run()                           # blocks – call from main thread
"""

import time
import tkinter as tk
from collections import deque
from typing import List


# ── Configuration ────────────────────────────────────────────────────────────
CIRCLE_RADIUS = 150
BG_COLOR      = "white"
CIRCLE_COLOR  = "black"
WINDOW_TITLE  = "Gaze Position Display"
TARGET_FPS    = 60
UPDATE_INTERVAL_MS = 1000 // TARGET_FPS


class GazeDisplay:
    def __init__(self, gaze_pos: List[float]):
        """
        :param gaze_pos: A two-element list [x, y] written to by the eye-tracker
                         thread.  The display reads it every frame – no locking
                         needed for two floats on CPython (GIL protects scalar
                         assignments).
        """
        self._gaze_pos = gaze_pos

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)

        # ── Fullscreen setup ──────────────────────────────────────────────────
        self.root.attributes("-fullscreen", True)
        self.root.update_idletasks()                  # let Tk resolve geometry
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # Allow Escape to exit fullscreen
        self.root.bind("<Escape>", lambda _: self.root.destroy())

        # ── Canvas ────────────────────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_w,
            height=self.screen_h,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Initial circle position at screen centre
        cx, cy = self.screen_w // 2, self.screen_h // 2
        self.circle = self.canvas.create_oval(
            cx - CIRCLE_RADIUS, cy - CIRCLE_RADIUS,
            cx + CIRCLE_RADIUS, cy + CIRCLE_RADIUS,
            fill=CIRCLE_COLOR, outline=CIRCLE_COLOR,
        )

        # Gaze coordinate readout (bottom-left)
        self.status = self.canvas.create_text(
            10, self.screen_h - 10,
            anchor="sw",
            text=f"Gaze: ({cx}, {cy})",
            font=("Consolas", 11),
            fill="gray",
        )

        # FPS readout (top-right)
        self.fps_label = self.canvas.create_text(
            self.screen_w - 10, 10,
            anchor="ne",
            text="FPS: --",
            font=("Consolas", 11),
            fill="gray",
        )

        # FPS tracking – rolling window of frame timestamps
        self.frame_times: deque[float] = deque(maxlen=TARGET_FPS)

        # Kick off the render loop
        self._update()

    # ── Public ───────────────────────────────────────────────────────────────
    def run(self):
        """Start the Tk main loop (blocks until the window is closed)."""
        self.root.mainloop()

    # ── Private ──────────────────────────────────────────────────────────────
    def _update(self):
        """Render loop: read shared gaze position, move circle, compute FPS."""
        now = time.perf_counter()
        self.frame_times.append(now)

        # Read the latest gaze coordinates from the shared list.
        # Input is normalised: 0 = centre, -1 = left/down, +1 = right/up.
        # Map to screen pixels; Y is flipped because screen-Y grows downward.
        nx, ny = float(self._gaze_pos[0]), float(self._gaze_pos[1])
        x = ( nx + 1) / 2 * self.screen_w
        y = (-ny + 1) / 2 * self.screen_h

        self.canvas.coords(
            self.circle,
            x - CIRCLE_RADIUS, y - CIRCLE_RADIUS,
            x + CIRCLE_RADIUS, y + CIRCLE_RADIUS,
        )
        self.canvas.itemconfig(self.status, text=f"Gaze: ({x:.1f}, {y:.1f})")

        # Rolling FPS calculation
        if len(self.frame_times) >= 2:
            elapsed = self.frame_times[-1] - self.frame_times[0]
            if elapsed > 0:
                fps = (len(self.frame_times) - 1) / elapsed
                self.canvas.itemconfig(self.fps_label, text=f"FPS: {fps:.1f}")

        # Schedule next frame
        self.root.after(UPDATE_INTERVAL_MS, self._update)


# ── Standalone smoke-test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import threading, math

    # Simulate the eye-tracker writing a slow sine-wave path
    gaze_pos = [0.0, 0.0]

    def fake_tracker():
        t = 0.0
        time.sleep(0.5)
        while True:
            gaze_pos[0] =       math.cos(t)        # x: -1 … +1
            gaze_pos[1] = 0.5 * math.sin(t)        # y: -0.5 … +0.5
            t += 0.02
            time.sleep(1 / 60)

    threading.Thread(target=fake_tracker, daemon=True).start()

    display = GazeDisplay(gaze_pos)
    display.run()

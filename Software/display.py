"""
display.py – Gaze Position Display Demo

Creates a window that draws a black circle tracking the mouse cursor position.
Displays the current frame rate (FPS) on screen.

Usage:
    python display.py
"""

import time
import tkinter as tk
from collections import deque


# ── Configuration ────────────────────────────────────────────────────────────
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
CIRCLE_RADIUS = 100
BG_COLOR = "white"
CIRCLE_COLOR = "black"
WINDOW_TITLE = "Gaze Position Display"
TARGET_FPS = 60
UPDATE_INTERVAL_MS = 1000 // TARGET_FPS


class GazeDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        # Current mouse position
        self.mouse_x = WINDOW_WIDTH // 2
        self.mouse_y = WINDOW_HEIGHT // 2

        # Draw initial circle at center
        cx, cy = self.mouse_x, self.mouse_y
        self.circle = self.canvas.create_oval(
            cx - CIRCLE_RADIUS,
            cy - CIRCLE_RADIUS,
            cx + CIRCLE_RADIUS,
            cy + CIRCLE_RADIUS,
            fill=CIRCLE_COLOR,
            outline=CIRCLE_COLOR,
        )

        # Gaze position label (bottom-left)
        self.status = self.canvas.create_text(
            10,
            WINDOW_HEIGHT - 10,
            anchor="sw",
            text=f"Gaze: ({cx}, {cy})",
            font=("Consolas", 11),
            fill="gray",
        )

        # FPS label (top-right)
        self.fps_label = self.canvas.create_text(
            WINDOW_WIDTH - 10,
            10,
            anchor="ne",
            text="FPS: --",
            font=("Consolas", 11),
            fill="gray",
        )

        # FPS tracking – store timestamps of recent frames
        self.frame_times: deque[float] = deque(maxlen=TARGET_FPS)

        # Bind mouse movement
        self.canvas.bind("<Motion>", self._on_mouse_move)

        # Start the render loop
        self._update()

    # ── Public ───────────────────────────────────────────────────────────────
    def run(self):
        """Start the Tk main loop."""
        self.root.mainloop()

    # ── Private ──────────────────────────────────────────────────────────────
    def _on_mouse_move(self, event: tk.Event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def _update(self):
        """Render loop: move circle, compute FPS, schedule next frame."""
        now = time.perf_counter()
        self.frame_times.append(now)

        # Move circle to current mouse position
        x, y = self.mouse_x, self.mouse_y
        self.canvas.coords(
            self.circle,
            x - CIRCLE_RADIUS,
            y - CIRCLE_RADIUS,
            x + CIRCLE_RADIUS,
            y + CIRCLE_RADIUS,
        )
        self.canvas.itemconfig(self.status, text=f"Gaze: ({x}, {y})")

        # Calculate FPS from the rolling window of frame timestamps
        if len(self.frame_times) >= 2:
            elapsed = self.frame_times[-1] - self.frame_times[0]
            if elapsed > 0:
                fps = (len(self.frame_times) - 1) / elapsed
                self.canvas.itemconfig(self.fps_label, text=f"FPS: {fps:.1f}")

        # Schedule next frame
        self.root.after(UPDATE_INTERVAL_MS, self._update)


if __name__ == "__main__":
    display = GazeDisplay()
    display.run()

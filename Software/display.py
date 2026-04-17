"""
display.py – Gaze Position Display (pygame, single screen split L|R)

Draws a black circle in each half of the screen for left and right eyes.
Positions come from a shared multiprocessing.Array updated by the eye-tracker.

    shared_array[0], [1]  →  left  eye  x, y
    shared_array[2], [3]  →  right eye  x, y

Normalised coords: 0 = centre, ±1 = edge.
  X: -1 = left,  +1 = right
  Y: -1 = bottom, +1 = top  (flipped to screen coords)

Usage:
    import multiprocessing
    arr = multiprocessing.Array('d', [0.0, 0.0, 0.0, 0.0])
    display = GazeDisplay(arr)
    display.run()          # blocks – call from main thread
"""

import os
import time
import math
import threading
from collections import deque

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pygame.freetype

# ── Configuration ─────────────────────────────────────────────────────────────
CIRCLE_RADIUS = 120
BG_COLOR      = (255, 255, 255)   # white
CIRCLE_COLOR  = (0,   0,   0)    # black
STATUS_COLOR  = (160, 160, 160)  # gray
WINDOW_TITLE  = "Gaze Position Display"
TARGET_FPS    = 60


class GazeDisplay:
    """
    Renders both eyes on a single screen split vertically in half.

    Left  half → shared_array[0], shared_array[1]  (left  eye x, y)
    Right half → shared_array[2], shared_array[3]  (right eye x, y)
    """

    def __init__(self, shared_array):
        """
        :param shared_array: multiprocessing.Array of typecode 'd', length >= 4.
        """
        self._shared_array = shared_array

        pygame.init()
        pygame.freetype.init()
        pygame.mouse.set_visible(False)

        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h

        self.screen = pygame.display.set_mode(
            (self.screen_w, self.screen_h),
            pygame.FULLSCREEN | pygame.NOFRAME,
        )
        pygame.display.set_caption(f"{WINDOW_TITLE} [L | R]")

        self.font = pygame.freetype.SysFont("monospace", 18)
        self.clock = pygame.time.Clock()
        self.frame_times: deque[float] = deque(maxlen=TARGET_FPS)

    def run(self):
        """Blocking render loop. Press Escape or Q to quit."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False

            self._render()
            self.clock.tick(TARGET_FPS)

        pygame.quit()

    def _render(self):
        self.screen.fill(BG_COLOR)

        half_w = self.screen_w // 2

        for label, arr_off, panel_x in (("L", 0, 0), ("R", 2, half_w)):
            nx = float(self._shared_array[arr_off])
            ny = float(self._shared_array[arr_off + 1])
            px = panel_x + int((nx + 1) / 2 * half_w)
            py = int((-ny + 1) / 2 * self.screen_h)

            panel_rect = pygame.Rect(panel_x, 0, half_w, self.screen_h)
            self.screen.set_clip(panel_rect)
            pygame.draw.circle(self.screen, CIRCLE_COLOR, (px, py), CIRCLE_RADIUS)
            self.screen.set_clip(None)

            status_surf, status_rect = self.font.render(
                f"Gaze[{label}]: ({px - panel_x}, {py})", STATUS_COLOR
            )
            self.screen.blit(
                status_surf,
                (panel_x + 5, self.screen_h - status_rect.height - 5),
            )

        # Centre dividing line
        pygame.draw.line(
            self.screen, STATUS_COLOR,
            (half_w, 0), (half_w, self.screen_h), 2,
        )

        # Rolling FPS (top-right)
        now = time.perf_counter()
        self.frame_times.append(now)
        fps_text = "--"
        if len(self.frame_times) >= 2:
            elapsed = self.frame_times[-1] - self.frame_times[0]
            if elapsed > 0:
                fps_text = f"{(len(self.frame_times) - 1) / elapsed:.1f}"
        fps_surf, fps_rect = self.font.render(f"FPS: {fps_text}", STATUS_COLOR)
        self.screen.blit(fps_surf, (self.screen_w - fps_rect.width - 10, 10))

        pygame.display.flip()


# ── Standalone smoke-test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import multiprocessing as _mp

    shared = _mp.Array('d', [0.0, 0.0, 0.0, 0.0])

    def fake_tracker():
        t = 0.0
        time.sleep(0.5)
        while True:
            shared[0] =       math.cos(t)          # left eye x
            shared[1] = 0.5 * math.sin(t)          # left eye y
            shared[2] =       math.cos(t + 1.0)    # right eye x
            shared[3] = 0.5 * math.sin(t + 1.0)   # right eye y
            t += 0.02
            time.sleep(1 / 60)

    threading.Thread(target=fake_tracker, daemon=True).start()

    display = GazeDisplay(shared)
    display.run()

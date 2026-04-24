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
import pygame._freetype

# ── Configuration ─────────────────────────────────────────────────────────────
# Each mode: image path + max dimension in pixels (longest side) — adjust per mode visually.
DISPLAY_MODES = [
    {"image_path": "pete_eyes.png",  "eye_radius": 300},
    {"image_path": "anime_eyes.png", "eye_radius": 300},
    {"image_path": "creepy_overlay.png", "overlay": True, "gaze_circle_radius": 30},
]

BG_COLOR     = (255, 255, 255)    # white
STATUS_COLOR = (160, 160, 160)    # gray
WINDOW_TITLE = "Gaze Position Display"
TARGET_FPS   = 60

# Per-eye center offsets in pixels (x, y).  Positive x → right, positive y → down.
# Adjust these to align each eye image with the physical mask openings.
LEFT_EYE_OFFSET  = (-30, 30)   # (x, y) offset for left  eye panel
RIGHT_EYE_OFFSET = (30, 30)   # (x, y) offset for right eye panel


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
        pygame._freetype.init()
        pygame.mouse.set_visible(False)

        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h

        self.screen = pygame.display.set_mode(
            (self.screen_w, self.screen_h),
            pygame.FULLSCREEN | pygame.NOFRAME,
        )
        pygame.display.set_caption(f"{WINDOW_TITLE} [L | R]")

        self.font = pygame._freetype.Font(None, 18)
        self.clock = pygame.time.Clock()
        self.frame_times: deque[float] = deque(maxlen=TARGET_FPS)

        # Load and scale each mode's eye image.
        # Normal modes: scale to fit within eye_radius square.
        # Overlay modes: scale to fill the panel (half_w × screen_h).
        self._mode_images = []
        half_w = self.screen_w // 2
        for mode in DISPLAY_MODES:
            raw = pygame.image.load(mode["image_path"]).convert_alpha()
            orig_w, orig_h = raw.get_size()
            if mode.get("overlay"):
                scale = max(half_w / orig_w, self.screen_h / orig_h)
            else:
                r = mode["eye_radius"]
                scale = min(r / orig_w, r / orig_h)
            new_size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
            self._mode_images.append(pygame.transform.smoothscale(raw, new_size))
        self._mode_index = 0

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
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    self._mode_index = (self._mode_index + 1) % len(DISPLAY_MODES)

            self._render()
            self.clock.tick(TARGET_FPS)

        pygame.quit()

    def _render(self):
        self.screen.fill(BG_COLOR)

        half_w = self.screen_w // 2

        eye_offsets = {"L": LEFT_EYE_OFFSET, "R": RIGHT_EYE_OFFSET}
        for label, arr_off, panel_x in (("L", 0, 0), ("R", 2, half_w)):
            nx = float(self._shared_array[arr_off])
            ny = float(self._shared_array[arr_off + 1])
            px = panel_x + int((-nx + 1) / 2 * half_w)
            py = int((ny + 1) / 2 * self.screen_h)

            off_x, off_y = eye_offsets[label]
            panel_rect = pygame.Rect(panel_x, 0, half_w, self.screen_h)
            self.screen.set_clip(panel_rect)
            img = self._mode_images[self._mode_index]
            img_w, img_h = img.get_size()
            mode = DISPLAY_MODES[self._mode_index]
            if mode.get("overlay"):
                # Draw gaze circle first (underneath the overlay)
                circle_r = mode.get("gaze_circle_radius", 30)
                pygame.draw.circle(self.screen, (0, 0, 0), (px + off_x, py + off_y), circle_r)
                # Blit overlay centered in the panel
                blit_x = panel_x + (half_w - img_w) // 2
                blit_y = (self.screen_h - img_h) // 2
                self.screen.blit(img, (blit_x, blit_y))
            else:
                blit_x = px - img_w // 2 + off_x
                blit_y = py - img_h // 2 + off_y
                self.screen.blit(img, (blit_x, blit_y))
            self.screen.set_clip(None)

            status_surf, status_rect = self.font.render(
                f"Gaze[{label}]: ({px - panel_x}, {py})", fgcolor=STATUS_COLOR
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
        fps_surf, fps_rect = self.font.render(f"FPS: {fps_text}", fgcolor=STATUS_COLOR)
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

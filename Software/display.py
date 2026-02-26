import threading
import tkinter as tk
import sys

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
CIRCLE_RADIUS = 100
BG_COLOR = "white"
CIRCLE_COLOR = "black"
WINDOW_TITLE = "Gaze Position Display"


class Display:
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

        # Draw initial circle at the center
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        self.circle = self.canvas.create_oval(
            cx - CIRCLE_RADIUS,
            cy - CIRCLE_RADIUS,
            cx + CIRCLE_RADIUS,
            cy + CIRCLE_RADIUS,
            fill=CIRCLE_COLOR,
            outline=CIRCLE_COLOR,
        )

        # Status label
        self.status = self.canvas.create_text(
            10,
            WINDOW_HEIGHT - 10,
            anchor="sw",
            text=f"Gaze: ({cx}, {cy})",
            font=("Consolas", 11),
            fill="gray",
        )

        # Start a background thread that reads from stdin
        self.input_thread = threading.Thread(target=self._read_input, daemon=True)
        self.input_thread.start()

    def run(self):
        """Start the Tk main loop."""
        self.root.mainloop()

    def _move_circle(self, x: float, y: float):
        """Move the circle so its center is at (x, y)."""
        self.canvas.coords(
            self.circle,
            x - CIRCLE_RADIUS,
            y - CIRCLE_RADIUS,
            x + CIRCLE_RADIUS,
            y + CIRCLE_RADIUS,
        )
        self.canvas.itemconfig(self.status, text=f"Gaze: ({x:.1f}, {y:.1f})")

    def _read_input(self):
        """Continuously read 'x y' lines from stdin and update the circle."""
        print(
            f"[display] Window ready ({WINDOW_WIDTH}x{WINDOW_HEIGHT}). "
            "Enter gaze position as 'x y':"
        )
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.replace(",", " ").split()
                x, y = float(parts[0]), float(parts[1])
                # Schedule the update on the Tk main thread
                self.root.after(0, self._move_circle, x, y)
            except (ValueError, IndexError):
                print(
                    f"[display] Invalid input '{line}'. Expected two numbers: x y",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    display = Display()
    display.run()

from textual.widgets import Static, Sparkline
from textual.app import ComposeResult
from textual.containers import Vertical
from rich.text import Text
import queue
import random

class Constellation(Static):
    """The Star Chart Visualization."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stars = [] # List of [x, y, age]

    def update_stars(self, new_stars, rms):
        # 1. Add new stars
        for (f1, delta) in new_stars:
            y = min(11, int(f1 / 300))
            x = 59
            self.stars.append([x, y, 1.0])

        # 2. Animate
        kept_stars = []
        for star in self.stars:
            star[0] -= 1
            star[2] -= 0.05
            if star[0] > 0 and star[2] > 0:
                kept_stars.append(star)
        self.stars = kept_stars

        # 3. Render
        grid = [[' ' for _ in range(60)] for _ in range(12)]
        for x, y, age in self.stars:
            if 0 <= y < 12 and 0 <= x < 60:
                char = '.' if age < 0.5 else '*'
                if age > 0.8: char = '+'
                grid[y][int(x)] = char

        lines = ["".join(row) for row in grid]
        
        # RMS Bar (Optional, since we have sparklines now, but looks cool in ASCII too)
        # rms_len = int(rms * 60)
        # lines.append("[" + "=" * rms_len + " " * (58 - rms_len) + "]")

        text = Text("\n".join(lines), style="green")
        self.update(text)

class Scope(Static):
    """Panel A: Combined Visualization."""
    
    def __init__(self, dsp_queue: queue.Queue, **kwargs):
        super().__init__(**kwargs)
        self.dsp_queue = dsp_queue
        self.history = [0.0] * 60

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Constellation(id="constellation", classes="box")
            yield Static("RMS Energy", classes="label")
            yield Sparkline(self.history, summary_function=max, id="rms-sparkline")
            yield Static("Spectral Flatness", classes="label")
            yield Sparkline(self.history, summary_function=max, id="flatness-sparkline")

    def on_mount(self):
        self.constellation = self.query_one("#constellation", Constellation)
        self.rms_sparkline = self.query_one("#rms-sparkline", Sparkline)
        self.flatness_sparkline = self.query_one("#flatness-sparkline", Sparkline)
        self.set_interval(1/20, self.update_scope)

    def update_scope(self):
        try:
            if self.dsp_queue.empty(): return

            batch_stars = []
            last_rms = 0.0
            last_flatness = 0.0

            # Drain queue but KEEP the transient data
            while not self.dsp_queue.empty():
                item = self.dsp_queue.get_nowait()
                batch_stars.extend(item.get('stars', [])) # Accumulate stars
                last_rms = item.get('rms', 0)             # RMS is continuous, taking last is fine
                last_flatness = item.get('spectral_centroid', 0)

            # Update Constellation with ALL stars found since last frame
            self.constellation.update_stars(batch_stars, last_rms)

            # Update Sparklines with latest values
            self.rms_sparkline.data = (self.rms_sparkline.data[1:] + [last_rms])
            self.flatness_sparkline.data = (self.flatness_sparkline.data[1:] + [last_flatness])

        except Exception:
            pass

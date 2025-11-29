from textual.widgets import Static, Sparkline, Input
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.containers import Vertical
import queue

class Scope(Static):
    """Panel A: Real-time spectral visualization."""
    
    def __init__(self, dsp_queue: queue.Queue, **kwargs):
        super().__init__(**kwargs)
        self.dsp_queue = dsp_queue
        self.history = [0.0] * 60 # 1 second of history at 60Hz

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("RMS Energy", classes="label")
            yield Sparkline(self.history, summary_function=max, id="rms-sparkline")
            yield Static("Spectral Flatness", classes="label")
            yield Sparkline(self.history, summary_function=max, id="flatness-sparkline")

    def on_mount(self):
        self.rms_sparkline = self.query_one("#rms-sparkline", Sparkline)
        self.flatness_sparkline = self.query_one("#flatness-sparkline", Sparkline)
        self.set_interval(1/20, self.update_scope)

    def update_scope(self):
        # Optimization: Pause visualization if user is typing
        if isinstance(self.app.focused, Input):
            return

        try:
            # Drain queue to get latest
            latest = None
            while not self.dsp_queue.empty():
                latest = self.dsp_queue.get_nowait()
            
            if latest:
                rms = latest['rms']
                flatness = latest['spectral_centroid']
                
                # Update Sparklines
                self.rms_sparkline.data = (self.rms_sparkline.data[1:] + [rms])
                self.flatness_sparkline.data = (self.flatness_sparkline.data[1:] + [flatness])
                
        except Exception:
            pass

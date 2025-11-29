from textual.widgets import Static, ProgressBar, Label, Input
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message

class VectorMonitor(Static):
    """Panel B: Vector State Monitor."""
    
    can_focus = True
    
    BINDINGS = [
        Binding("up", "select_prev", "Up"),
        Binding("down", "select_next", "Down"),
        Binding("left", "decrease", "Decrease"),
        Binding("right", "increase", "Increase"),
    ]

    # Reactive state for the 5 dimensions
    energy = reactive(0.5)
    valence = reactive(0.5)
    danceability = reactive(0.5)
    acousticness = reactive(0.5)
    instrumentalness = reactive(0.0)

    selected_index = reactive(0)
    dimensions = ["energy", "valence", "danceability", "acousticness", "instrumentalness"]
    colors = ["red", "blue", "green", "yellow", "cyan"]

    class VectorChanged(Message):
        """Emitted when the vector changes."""
        def __init__(self, vector: dict):
            self.vector = vector
            super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Target Vector", classes="header")
            for i, dim in enumerate(self.dimensions):
                yield Label(f"{dim.title()}", id=f"label-{dim}")
                yield ProgressBar(total=1.0, show_eta=False, id=f"bar-{dim}", classes=f"bar-{self.colors[i]}")
            yield Label("↑↓ Select | ←→ Adjust (Auto-Search) | / Search", classes="help-text")

    def watch_energy(self, value): self.update_bar("energy", value)
    def watch_valence(self, value): self.update_bar("valence", value)
    def watch_danceability(self, value): self.update_bar("danceability", value)
    def watch_acousticness(self, value): self.update_bar("acousticness", value)
    def watch_instrumentalness(self, value): self.update_bar("instrumentalness", value)

    def update_bar(self, dim, value):
        try:
            bar = self.query_one(f"#bar-{dim}", ProgressBar)
            bar.progress = value
            self.post_message(self.VectorChanged(self.get_vector()))
        except:
            pass

    def watch_selected_index(self, value):
        # Highlight the selected label
        for i, dim in enumerate(self.dimensions):
            try:
                label = self.query_one(f"#label-{dim}", Label)
                if i == value:
                    label.add_class("selected")
                else:
                    label.remove_class("selected")
            except:
                pass

    def action_select_prev(self):
        self.selected_index = (self.selected_index - 1) % len(self.dimensions)

    def action_select_next(self):
        self.selected_index = (self.selected_index + 1) % len(self.dimensions)

    def action_decrease(self):
        dim = self.dimensions[self.selected_index]
        current = getattr(self, dim)
        setattr(self, dim, max(0.0, current - 0.05))

    def action_increase(self):
        dim = self.dimensions[self.selected_index]
        current = getattr(self, dim)
        setattr(self, dim, min(1.0, current + 0.05))

    def get_vector(self):
        return {
            "energy": self.energy,
            "valence": self.valence,
            "danceability": self.danceability,
            "acousticness": self.acousticness,
            "instrumentalness": self.instrumentalness
        }

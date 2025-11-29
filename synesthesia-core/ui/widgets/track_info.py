from textual.widgets import Static, Label
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive

class TrackInfo(Static):
    """Panel D: Metadata Display."""
    
    track_title = reactive("Waiting for Input...")
    artist = reactive("---")
    source = reactive("SYSTEM READY")
    distance = reactive("0.0000")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.track_title, id="track-title")
            yield Label(self.artist, id="track-artist")
            yield Label(f"Source: {self.source}", id="track-source")
            yield Label(f"Dist: {self.distance}", id="track-distance")

    def watch_track_title(self, value):
        try:
            self.query_one("#track-title", Label).update(value)
        except: pass

    def watch_artist(self, value):
        try:
            self.query_one("#track-artist", Label).update(value)
        except: pass

    def watch_source(self, value):
        try:
            self.query_one("#track-source", Label).update(f"Source: {value}")
        except: pass

    def watch_distance(self, value):
        try:
            self.query_one("#track-distance", Label).update(f"Dist: {value}")
        except: pass

    def update_track(self, track: dict, dist: float = 0.0):
        self.track_title = track.get('title', 'Unknown')
        self.artist = track.get('artist', 'Unknown')
        self.source = "LIBRARY (ARK)" # Or Discovery
        self.distance = f"{dist:.4f}"

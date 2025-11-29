import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical

from textual.widgets import Header, Footer, Input
import threading
import asyncio

from ui.widgets.scope import Scope
from ui.widgets.vector_monitor import VectorMonitor
from ui.widgets.log import Log
from ui.widgets.track_info import TrackInfo

from services.dsp import DSP
from services.vector import VectorEngine
from services.spotify import SpotifyClient
from services.ark import Ark
from services.navigation import Navigation

from textual import work

class SynesthesiaApp(App):
    """Synesthesia Terminal Edition."""
    
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "toggle_mic", "Toggle Mic"),
        ("/", "focus_search", "Focus Search"),
        ("enter", "search", "Search"),
        ("tab", "focus_next", "Next Panel"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize Services
        self.dsp = DSP()
        self.ve = VectorEngine()
        self.sp = SpotifyClient()
        self.ark = Ark(self.ve)
        self.nav = Navigation(self.ve, self.sp)
        
        self.dsp.start()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        # Top Row
        with Container(id="top-row"):
            yield Scope(self.dsp.queue, id="scope")
            with Vertical(id="monitor-column"):
                yield Input(placeholder="Search Spotify...", id="search-input")
                yield VectorMonitor(id="vector-monitor")
            
        # Bottom Row
        with Container(id="bottom-row"):
            yield Log(id="log")
            yield TrackInfo(id="track-info")
            
        yield Footer()

    def on_descendant_focus(self, event):
        # Pause DSP and Game Loop when typing
        if event.control.id == "search-input":
            self.dsp.pause()
            
    def on_descendant_blur(self, event):
        # Resume DSP and Game Loop when done typing
        if event.control.id == "search-input":
            self.dsp.resume()

    def on_mount(self):
        # Start Ark Ingestion in background
        self.log_widget = self.query_one("#log", Log)
        self.log_widget.log_info("Initializing Synesthesia Core...")
        
        self.ingesting = True # Flag to prevent lock contention
        threading.Thread(target=self.run_ingest, daemon=True).start()
        
        # Start Game Loop (10Hz)
        self.set_interval(0.1, self.game_loop)

    def run_ingest(self):
        # Check if ingestion needed
        self.call_from_thread(self.log_widget.log_info, "Checking Ark Status...")
        
        # DIAGNOSTIC: List all collections
        try:
            collections = self.ve.qdrant.get_collections().collections
            for col in collections:
                info = self.ve.qdrant.get_collection(col.name)
                count = info.points_count
                config = info.config.params.vectors
                self.call_from_thread(self.log_widget.log_info, f"Col: {col.name} | Cnt: {count} | Cfg: {config}")
        except Exception as e:
            self.call_from_thread(self.log_widget.log_info, f"Diagnostic Error: {e}")

        # Check count first to avoid unnecessary lock contention
        count = self.ve.get_count()
        if count > 0:
            self.call_from_thread(self.log_widget.log_info, f"Ark Online. {count} vectors loaded.")
            self.ingesting = False
            return

        # Define callback to update log from thread
        def log_callback(msg):
            self.call_from_thread(self.log_widget.log_info, msg)
            
        self.ark.ingest("data/tracks_features.csv", callback=log_callback)
        self.ingesting = False

    def game_loop(self):
        # Prevent lock contention during ingestion
        if getattr(self, 'ingesting', False):
            return

        # Pause game loop if user is typing
        try:
            if self.query_one("#search-input", Input).has_focus:
                return
        except:
            pass

        # Get current vector from Monitor
        vm = self.query_one("#vector-monitor", VectorMonitor)
        current_vector = vm.get_vector()
        
        # Offload logic to worker
        self.run_game_tick(current_vector)

    @work(exclusive=True, thread=True)
    def run_game_tick(self, current_vector):
        # Tick Navigation (Blocking)
        result = self.nav.tick(current_vector)
        
        if result:
            self.call_from_thread(self._handle_nav_result, result)
        # else:
            # self.call_from_thread(self.log_widget.log_info, "Tick: No Result")

    def _handle_nav_result(self, result):
        try:
            with open("debug_ui.log", "a") as f:
                f.write(f"Handling Result: {result}\n")
                
            if result['type'] == 'found':
                track = result['track']
                with open("debug_ui.log", "a") as f:
                    f.write(f"Track: {track}\n")
                    
                self.log_widget.log_found(f"{track.get('artist')} - {track.get('title')}")
                self.query_one("#track-info", TrackInfo).update_track(track, result.get('distance', 0.0))
            elif result['type'] == 'void':
                self.log_widget.log_void()
        except Exception as e:
            with open("debug_ui.log", "a") as f:
                f.write(f"UI Error: {e}\n")

    def on_unmount(self):
        self.dsp.stop()

    def action_toggle_mic(self):
        if self.dsp.running:
            self.dsp.stop()
            self.notify("Mic Stopped")
        else:
            self.dsp.start()
            self.notify("Mic Started")

    def on_input_submitted(self, event: Input.Submitted):
        # Handle text search from VectorMonitor
        query = event.value
        if query:
            self.run_text_search(query)
            # Clear input
            event.input.value = ""

    @work(exclusive=True, thread=True)
    def run_text_search(self, query: str):
        self.call_from_thread(self.log_widget.log_info, f"Searching Spotify: {query}...")
        
        # Search Spotify
        track = self.sp.search(query)
        
        if track and track.get('title') == "Error":
            self.call_from_thread(self.log_widget.log_info, "Spotify Error / Timeout")
        elif track and track.get('id'):
            track_id = track['id']
            # Play Track
            self.sp.play_track(track_id)
            
            # Try to get vector from Ark
            vector_data = self.ve.get_track_data(track_id)
            
            if vector_data:
                vector, payload = vector_data
                # Update Monitor
                self.call_from_thread(self.update_monitor, vector)
                self.call_from_thread(self.log_widget.log_found, f"{track.get('artist')} - {track.get('title')}")
                self.call_from_thread(self.query_one("#track-info", TrackInfo).update_track, track, 0.0)
            else:
                # Track found in Spotify but not in Ark
                self.call_from_thread(self.log_widget.log_info, f"Playing: {track.get('title')} (Not in Ark)")
                self.call_from_thread(self.query_one("#track-info", TrackInfo).update_track, track, -1.0)
        else:
            self.call_from_thread(self.log_widget.log_void)

    def update_monitor(self, vector):
        vm = self.query_one("#vector-monitor", VectorMonitor)
        # Update reactive values
        # vector is numpy array [energy, valence, dance, acoustic, instrumental]
        vm.energy = float(vector[0])
        vm.valence = float(vector[1])
        vm.danceability = float(vector[2])
        vm.acousticness = float(vector[3])
        vm.instrumentalness = float(vector[4])

    def action_focus_search(self):
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def action_search(self):
        # Manual search trigger (Enter key)
        vm = self.query_one("#vector-monitor", VectorMonitor)
        current_vector = vm.get_vector()
        
        self.run_force_search(current_vector)

    @work(exclusive=True, thread=True)
    def run_force_search(self, current_vector):
        result = self.nav.force_search(current_vector)
        if result:
            self.call_from_thread(self._handle_nav_result, result)
        else:
            self.call_from_thread(self.notify, "Search Failed (Void)")

if __name__ == "__main__":
    app = SynesthesiaApp()
    app.run()

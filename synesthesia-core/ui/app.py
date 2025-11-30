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

from services.controller import SystemController

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
        
        # Initialize System Controller
        self.controller = SystemController()
        self.controller.start()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        # Top Row
        with Container(id="top-row"):
            # Access DSP queue via controller
            yield Scope(self.controller.dsp.queue, id="scope")
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
            self.controller.dsp.pause()
            
    def on_descendant_blur(self, event):
        # Resume DSP and Game Loop when done typing
        if event.control.id == "search-input":
            self.controller.dsp.resume()

    def on_mount(self):
        # Start Ark Ingestion in background
        self.log_widget = self.query_one("#log", Log)
        self.log_widget.log_info("Initializing Synesthesia Core...")
        
        # Define callback to update log from thread
        def log_callback(msg):
            self.call_from_thread(self.log_widget.log_info, msg)

        # Start Ingestion via Controller
        self.controller.handle_ingest(callback=log_callback)
        
        # Start Game Loop (10Hz)
        self.set_interval(0.1, self.game_loop)

    def game_loop(self):
        # Prevent lock contention during ingestion
        if self.controller.ingesting:
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
        # Tick Controller (Blocking)
        result = self.controller.tick(current_vector)
        
        if result:
            self.call_from_thread(self._handle_nav_result, result)

    def _handle_nav_result(self, result):
        try:
            if result['type'] == 'found':
                track = result['track']
                self.log_widget.log_found(f"{track.get('artist')} - {track.get('title')}")
                self.query_one("#track-info", TrackInfo).update_track(track, result.get('distance', 0.0))
            elif result['type'] == 'void':
                self.log_widget.log_void()
        except Exception as e:
            self.log_widget.log_error(f"UI Error: {e}")

    def on_unmount(self):
        self.controller.stop()

    def action_toggle_mic(self):
        if self.controller.dsp.running:
            self.controller.dsp.stop()
            self.notify("Mic Stopped")
        else:
            self.controller.dsp.start()
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
        
        # Search via Controller
        result = self.controller.handle_search(query)
        
        if "error" in result:
            self.call_from_thread(self.log_widget.log_info, result["error"])
            return

        # Handle Success
        song_id = result['song_id']
        metadata = result['metadata']
        vector = result['vector']
        
        # Play Track (Controller handles playback in handle_search? No, handle_search just returns data. 
        # Wait, handle_search in controller DOES NOT play the track. api.py didn't play it, it just returned it.
        # But ui/app.py's run_text_search DID play it.
        # I should probably add playback to handle_search or do it here.
        # Let's do it here for now, or add play_track to controller.
        
        # Controller doesn't expose play_track directly. 
        # I'll access sp via controller for now to keep it simple, or add a method.
        # Actually, let's add play_track to controller? No, let's just use self.controller.sp.play_track
        
        self.controller.sp.play_track(metadata['id']) # Use Spotify ID, not UUID
        
        # Update Monitor
        self.call_from_thread(self.update_monitor, vector)
        self.call_from_thread(self.log_widget.log_found, f"{metadata.get('artist')} - {metadata.get('title')}")
        self.call_from_thread(self.query_one("#track-info", TrackInfo).update_track, metadata, 0.0)

    def update_monitor(self, vector):
        vm = self.query_one("#vector-monitor", VectorMonitor)
        # Update reactive values
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
        result = self.controller.force_search(current_vector)
        if result:
            self.call_from_thread(self._handle_nav_result, result)
        else:
            self.call_from_thread(self.notify, "Search Failed (Void)")

if __name__ == "__main__":
    app = SynesthesiaApp()
    app.run()

from textual.widgets import RichLog
from rich.text import Text

class Log(RichLog):
    """Panel C: System Event Log."""
    
    def __init__(self, **kwargs):
        super().__init__(markup=True, wrap=True, **kwargs)

    def log_search(self, query: str):
        self.write(f"[cyan][SEARCH][/] {query}")

    def log_found(self, track: str):
        self.write(f"[green][FOUND][/] {track}")

    def log_void(self):
        self.write("[purple][VOID][/] Global Discovery Triggered")

    def log_error(self, msg: str):
        self.write(f"[red][ERR][/] {msg}")

    def log_info(self, msg: str):
        self.write(f"[white]{msg}[/]")

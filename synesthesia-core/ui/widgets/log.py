from textual.widgets import RichLog

class Log(RichLog):
    """Panel C: System Event Log."""
    
    def __init__(self, **kwargs):
        super().__init__(markup=True, wrap=True, highlight=True, **kwargs)

    def log_search(self, query: str):
        self.write(f"[bold cyan]SEARCH[/] [white]{query}[/]")

    def log_found(self, track: str):
        self.write(f"[bold green]FOUND[/]  [white]{track}[/]")

    def log_void(self):
        self.write("[bold purple]VOID[/]   [dim]Global Discovery Triggered[/]")

    def log_error(self, msg: str):
        self.write(f"[bold red]ERR[/]    {msg}")

    def log_info(self, msg: str):
        self.write(f"[dim]{msg}[/]")
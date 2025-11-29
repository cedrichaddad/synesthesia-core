import pytest
from ui.app import SynesthesiaApp

@pytest.mark.asyncio
async def test_app_startup():
    app = SynesthesiaApp()
    async with app.run_test() as pilot:
        # Verify widgets are present
        assert app.query_one("#scope")
        assert app.query_one("#vector-monitor")
        assert app.query_one("#log")
        assert app.query_one("#track-info")
        
        # Verify initial state
        log = app.query_one("#log")
        # Log might be empty initially or have startup msg
        # We can check if it exists
        assert log
        
        # Test Mic Toggle
        await pilot.press("space")
        # Should see notification or log
        # Notifications are hard to test in pilot without inspecting internal state
        # But we can check if dsp running state changed
        # Initial state: running (start() called in __init__)
        # Toggle -> stop
        assert not app.dsp.running
        
        await pilot.press("space")
        assert app.dsp.running

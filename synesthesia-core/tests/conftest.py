import sys
from unittest.mock import MagicMock, patch
import pytest

# Mock pydub and its dependencies BEFORE importing app
pydub_mock = MagicMock()
sys.modules["pydub"] = pydub_mock
sys.modules["pydub.audio_segment"] = pydub_mock

# Mock rust_core since we can't build it easily here
rust_core_mock = MagicMock()
sys.modules["synesthesia.core"] = rust_core_mock

# Mock qdrant_client
qdrant_mock = MagicMock()
sys.modules["qdrant_client"] = qdrant_mock
sys.modules["qdrant_client.http"] = MagicMock()
sys.modules["qdrant_client.http.models"] = MagicMock()

# Mock spotipy
spotipy_mock = MagicMock()
sys.modules["spotipy"] = spotipy_mock
sys.modules["spotipy.oauth2"] = MagicMock()

# NOW we can import the app
from synesthesia.api import app

@pytest.fixture(autouse=True)
def mock_engines():
    with patch("synesthesia.api.SpotifyClient") as MockSpotifyClient, \
         patch("synesthesia.api.VectorEngine") as MockVectorEngine:
        
        # Setup instances
        mock_spotify_instance = MockSpotifyClient.return_value
        mock_vector_instance = MockVectorEngine.return_value
        
        # Manually set state for TestClient (if lifespan doesn't run)
        app.state.spotify_client = mock_spotify_instance
        app.state.vector_engine = mock_vector_instance
        
        yield mock_spotify_instance, mock_vector_instance

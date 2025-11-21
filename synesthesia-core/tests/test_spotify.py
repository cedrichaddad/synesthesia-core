import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.synesthesia.spotify import SpotifyClient

class TestSpotifyClient:
    @pytest.fixture
    def spotify_client(self):
        with patch('spotipy.Spotify') as mock_spotify:
            client = SpotifyClient()
            client.sp = mock_spotify
            return client

    def test_search_success(self, spotify_client):
        # Mock response structure from Spotipy
        spotify_client.sp.search.return_value = {
            'tracks': {
                'items': [{
                    'id': '123',
                    'name': 'Test Song',
                    'artists': [{'name': 'Test Artist'}],
                    'album': {'images': [{'url': 'http://image.url'}]}
                }]
            }
        }
        # Mock audio features
        spotify_client.sp.audio_features.return_value = [{
            'tempo': 120,
            'key': 5,
            'energy': 0.8
        }]
        
        result = spotify_client.search("Test Song")
        
        assert result is not None
        assert result['title'] == 'Test Song'
        assert result['artist'] == 'Test Artist'
        assert result['artist'] == 'Test Artist'

    def test_search_no_results(self, spotify_client):
        spotify_client.sp.search.return_value = {'tracks': {'items': []}}
        
        result = spotify_client.search("NonExistent")
        
        assert result['title'] == 'NonExistent'
        assert result['artist'] == 'Unknown'

    def test_get_track_details_success(self, spotify_client):
        spotify_client.sp.track.return_value = {
            'id': '123',
            'name': 'Test Song',
            'artists': [{'name': 'Test Artist'}],
            'album': {'images': [{'url': 'http://image.url'}]}
        }
        spotify_client.sp.audio_features.return_value = [{
            'tempo': 120,
            'key': 5,
            'energy': 0.8
        }]
        
        result = spotify_client.get_track_details("123")
        
        assert result['id'] == '123'
        assert result['title'] == 'Test Song'

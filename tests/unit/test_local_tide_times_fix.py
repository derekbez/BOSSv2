"""Test for local_tide_times API parameter fix."""
import pytest
from unittest.mock import Mock, patch
import urllib.parse


def test_tide_api_parameters():
    """Test that the extremes parameter is set correctly for WorldTides API."""
    # Import the module to test
    import boss.apps.local_tide_times.main as tide_app
    
    # Mock requests
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "extremes": [
            {"date": "2024-01-01T12:00:00Z", "type": "High"},
            {"date": "2024-01-01T18:00:00Z", "type": "Low"}
        ]
    }
    
    with patch('boss.apps.local_tide_times.main.requests') as mock_requests:
        mock_requests.get.return_value = mock_response
        
        # Test the fetch_tides function
        result = tide_app.fetch_tides(api_key="test_key", lat=51.5074, lon=-0.1278)
        
        # Verify the request was made
        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        
        # Check the URL and parameters
        assert call_args[0][0] == "https://www.worldtides.info/api"
        params = call_args[1]['params']
        
        # The key assertion: extremes should not be empty string
        # It should either be a proper value or not present
        if 'extremes' in params:
            assert params['extremes'] != ""  # Should not be empty string
            assert params['extremes'] in ["true", "1", True]  # Should be proper boolean value
        
        # Other parameters should be correct
        assert params['lat'] == 51.5074
        assert params['lon'] == -0.1278
        assert params['key'] == "test_key"


def test_url_generation_with_proper_extremes():
    """Test URL generation to ensure proper extremes parameter."""
    # Test different approaches to the extremes parameter
    
    # Current problematic approach
    params_bad = {"lat": 51.5074, "lon": -0.1278, "extremes": ""}
    url_bad = "https://www.worldtides.info/api?" + urllib.parse.urlencode(params_bad)
    assert "extremes=" in url_bad  # This is the problem - empty value
    
    # Better approaches
    params_good1 = {"lat": 51.5074, "lon": -0.1278, "extremes": "true"}
    url_good1 = "https://www.worldtides.info/api?" + urllib.parse.urlencode(params_good1)
    assert "extremes=true" in url_good1
    
    params_good2 = {"lat": 51.5074, "lon": -0.1278}
    # No extremes parameter at all
    url_good2 = "https://www.worldtides.info/api?" + urllib.parse.urlencode(params_good2)
    assert "extremes" not in url_good2
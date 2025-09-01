"""Unit tests for improved error handling in flight apps."""
import pytest
from unittest.mock import Mock, patch
import requests

# Import the flight app functions
from boss.apps.flights_leaving_heathrow.main import fetch_flights
from boss.apps.flight_status_favorite_airline.main import fetch_status


class TestFlightAppsErrorHandling:
    """Test enhanced error handling for flight applications."""
    
    def test_fetch_flights_no_requests_library(self):
        """Test fetch_flights when requests library is not available."""
        with patch('boss.apps.flights_leaving_heathrow.main.requests', None):
            result = fetch_flights("fake_key")
            assert isinstance(result, dict)
            assert "error" in result
            assert "requests library not available" in result["error"]
    
    def test_fetch_status_no_requests_library(self):
        """Test fetch_status when requests library is not available."""
        with patch('boss.apps.flight_status_favorite_airline.main.requests', None):
            result = fetch_status("fake_key", "BA")
            assert isinstance(result, dict)
            assert "error" in result
            assert "requests library not available" in result["error"]
    
    @patch('requests.get')
    def test_fetch_flights_connection_error(self, mock_get):
        """Test fetch_flights with network connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = fetch_flights("fake_key")
        assert isinstance(result, dict)
        assert "error" in result
        assert "network connection failed" in result["error"]
    
    @patch('requests.get')
    def test_fetch_status_connection_error(self, mock_get):
        """Test fetch_status with network connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = fetch_status("fake_key", "BA")
        assert isinstance(result, dict)
        assert "error" in result
        assert "network connection failed" in result["error"]
    
    @patch('requests.get')
    def test_fetch_flights_timeout_error(self, mock_get):
        """Test fetch_flights with timeout error."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = fetch_flights("fake_key")
        assert isinstance(result, dict)
        assert "error" in result
        assert "request timeout" in result["error"]
    
    @patch('requests.get')
    def test_fetch_flights_401_auth_error(self, mock_get):
        """Test fetch_flights with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = fetch_flights("bad_key")
        assert isinstance(result, dict)
        assert "error" in result
        assert "authentication failed" in result["error"]
    
    @patch('requests.get')
    def test_fetch_flights_429_rate_limit(self, mock_get):
        """Test fetch_flights with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        result = fetch_flights("key")
        assert isinstance(result, dict)
        assert "error" in result
        assert "rate limit exceeded" in result["error"]
    
    @patch('requests.get')
    def test_fetch_flights_successful_response(self, mock_get):
        """Test fetch_flights with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "airline": {"name": "British Airways"},
                    "flight": {"iata": "BA100"},
                    "departure": {"scheduled": "2023-01-01T10:30:00+00:00"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = fetch_flights("valid_key")
        assert isinstance(result, list)
        assert len(result) == 1
        assert "BA100" in result[0]
        assert "10:30" in result[0]
        assert "British Airways" in result[0]
    
    @patch('requests.get')
    def test_fetch_flights_empty_response(self, mock_get):
        """Test fetch_flights with empty data response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response
        
        result = fetch_flights("valid_key")
        assert isinstance(result, dict)
        assert "error" in result
        assert "no flights found" in result["error"]
    
    @patch('requests.get')
    def test_fetch_status_successful_response(self, mock_get):
        """Test fetch_status with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "flight": {"iata": "BA100"},
                    "departure": {"scheduled": "2023-01-01T10:30:00+00:00"},
                    "flight_status": "scheduled"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = fetch_status("valid_key", "BA")
        assert isinstance(result, list)
        assert len(result) == 1
        assert "BA100" in result[0]
        assert "10:30" in result[0]
        assert "scheduled" in result[0]
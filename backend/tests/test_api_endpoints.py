"""
API Endpoint Tests

Tests for FastAPI endpoints including /api/data.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "AutoDeFi.AI Backend"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()


class TestDataEndpoint:
    """Test /api/data endpoint"""
    
    @pytest.fixture
    def mock_protocol_data(self):
        """Mock protocol data"""
        return {
            "timestamp": 1730850000,
            "data": [
                {
                    "id": "aave",
                    "chain": "ethereum",
                    "apy": 4.12,
                    "tvl_usd": 1900000000,
                    "risk": "low",
                    "metadata": {"symbol": "AAVE", "url": "https://aave.com"}
                },
                {
                    "id": "lido",
                    "chain": "ethereum",
                    "apy": 5.24,
                    "tvl_usd": 17000000000,
                    "risk": "low",
                    "metadata": {"symbol": "stETH", "url": "https://lido.fi"}
                }
            ]
        }
    
    def test_get_data_success(self, mock_protocol_data):
        """Test successful data retrieval"""
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = mock_protocol_data
            
            response = client.get("/api/data/")
            
            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "protocols" in data
            assert "count" in data
            assert data["count"] == 2
            assert len(data["protocols"]) == 2
    
    def test_get_data_with_fresh_param(self, mock_protocol_data):
        """Test data retrieval with fresh=true"""
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = mock_protocol_data
            
            response = client.get("/api/data/?fresh=true")
            
            assert response.status_code == 200
            # Verify force_refresh was called with True
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["force_refresh"] == True
    
    def test_get_data_with_protocol_filter(self, mock_protocol_data):
        """Test data retrieval with protocol filter"""
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = mock_protocol_data
            
            response = client.get("/api/data/?protocols=aave")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert data["protocols"][0]["id"] == "aave"
    
    def test_get_data_with_multiple_protocol_filter(self, mock_protocol_data):
        """Test data retrieval with multiple protocol filter"""
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = mock_protocol_data
            
            response = client.get("/api/data/?protocols=aave,lido")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
    
    def test_get_data_without_metadata(self, mock_protocol_data):
        """Test data retrieval without metadata"""
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = mock_protocol_data
            
            response = client.get("/api/data/")
            
            assert response.status_code == 200
            data = response.json()
            # Should not include metadata by default
            assert "metadata" not in data["protocols"][0]
            assert "id" in data["protocols"][0]
            assert "apy" in data["protocols"][0]
    
    def test_get_data_with_metadata(self, mock_protocol_data):
        """Test data retrieval with metadata"""
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = mock_protocol_data
            
            response = client.get("/api/data/?include_metadata=true")
            
            assert response.status_code == 200
            data = response.json()
            # Should include metadata when requested
            assert "metadata" in data["protocols"][0]
    
    def test_get_data_rate_limit(self):
        """Test rate limiting on data endpoint"""
        # Clear rate limit storage
        from backend.core.security import _rate_limit_storage
        _rate_limit_storage.clear()
        
        with patch('backend.services.data_fetcher.get_cached_data') as mock_get:
            mock_get.return_value = {"timestamp": 1730850000, "data": []}
            
            # Make requests up to the limit
            for i in range(60):
                response = client.get("/api/data/")
                assert response.status_code == 200
            
            # Next request should be rate limited
            response = client.get("/api/data/")
            assert response.status_code == 429
            assert "error" in response.json()["detail"]


class TestMetricsEndpoint:
    """Test /api/data/metrics endpoint"""
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        response = client.get("/api/data/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "description" in data
        assert "defillama_fetch_total" in data["metrics"]
        assert "cache_hits" in data["metrics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

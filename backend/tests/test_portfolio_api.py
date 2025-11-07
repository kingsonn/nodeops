"""
API Endpoint Tests for Portfolio Routes

Tests for portfolio API endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestPortfolioEndpoints:
    """Test portfolio API endpoints"""
    
    @pytest.fixture
    def mock_portfolio_response(self):
        """Mock portfolio data"""
        return {
            "user_id": 1,
            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "risk_preference": "medium",
            "total_value_usd": 2050.52,
            "holdings": [
                {
                    "protocol": "Aave",
                    "symbol": "AAVE",
                    "amount": 2.0,
                    "value_usd": 191.00,
                    "apy": 4.12
                },
                {
                    "protocol": "Lido",
                    "symbol": "stETH",
                    "amount": 0.8,
                    "value_usd": 1840.00,
                    "apy": 5.24
                }
            ]
        }
    
    def test_get_portfolio_success(self, mock_portfolio_response):
        """Test successful portfolio retrieval"""
        with patch('backend.services.portfolio.portfolio_service.get_user_portfolio') as mock_get:
            mock_get.return_value = mock_portfolio_response
            
            response = client.get("/api/portfolio/?wallet=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert response.status_code == 200
            data = response.json()
            assert data["wallet_address"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            assert data["total_value_usd"] == 2050.52
            assert len(data["holdings"]) == 2
    
    def test_get_portfolio_not_found(self):
        """Test portfolio retrieval for non-existent user"""
        with patch('backend.services.portfolio.portfolio_service.get_user_portfolio') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/portfolio/?wallet=0xnonexistent")
            
            assert response.status_code == 404
            assert "error" in response.json()["detail"]
    
    def test_get_portfolio_missing_wallet(self):
        """Test portfolio retrieval without wallet parameter"""
        response = client.get("/api/portfolio/")
        
        assert response.status_code == 422  # Validation error
    
    def test_update_holding_success(self, mock_portfolio_response):
        """Test successful holding update"""
        with patch('backend.services.portfolio.portfolio_service.update_holding') as mock_update:
            mock_update.return_value = mock_portfolio_response
            
            response = client.post(
                "/api/portfolio/update",
                json={
                    "wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "protocol": "Aave",
                    "symbol": "AAVE",
                    "amount": 2.0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["wallet_address"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    
    def test_update_holding_invalid_data(self):
        """Test holding update with invalid data"""
        response = client.post(
            "/api/portfolio/update",
            json={
                "wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "protocol": "Aave"
                # Missing symbol and amount
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_refresh_portfolio_success(self, mock_portfolio_response):
        """Test successful portfolio refresh"""
        with patch('backend.services.portfolio.portfolio_service.refresh_portfolio_values') as mock_refresh:
            mock_refresh.return_value = mock_portfolio_response
            
            response = client.post("/api/portfolio/refresh?wallet=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert response.status_code == 200
            data = response.json()
            assert data["wallet_address"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    
    def test_seed_demo_portfolio(self, mock_portfolio_response):
        """Test demo portfolio seeding"""
        with patch('backend.services.portfolio.portfolio_service.seed_demo_data') as mock_seed:
            mock_seed.return_value = mock_portfolio_response
            
            response = client.get("/api/portfolio/demo")
            
            assert response.status_code == 200
            data = response.json()
            assert "wallet_address" in data
            assert "holdings" in data


class TestAIAnalysisEndpoint:
    """Test AI analysis endpoint"""
    
    def test_analyze_portfolio_stub(self):
        """Test AI analysis stub response"""
        response = client.get("/api/portfolio/analyze?wallet=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "Gemini AI reasoning engine placeholder active."
        assert data["wallet"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        assert "ai_model" in data
        assert "capabilities" in data
    
    def test_analyze_portfolio_missing_wallet(self):
        """Test AI analysis without wallet parameter"""
        response = client.get("/api/portfolio/analyze")
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

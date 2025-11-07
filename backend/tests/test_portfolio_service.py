"""
Unit Tests for Portfolio Service

Tests for portfolio management, holdings, CoinGecko integration, and AI stub.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.portfolio import PortfolioService, COINGECKO_TOKEN_MAP


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    client = MagicMock()
    return client


@pytest.fixture
def mock_coingecko_prices():
    """Mock CoinGecko price response"""
    return {
        "aave": {"usd": 95.50},
        "lido-dao": {"usd": 2.15},
        "ethereum": {"usd": 2300.00}
    }


@pytest.fixture
def mock_user_data():
    """Mock user data"""
    return {
        "id": 1,
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "risk_preference": "medium",
        "created_at": "2025-11-05T10:00:00",
        "updated_at": "2025-11-05T10:00:00"
    }


@pytest.fixture
def mock_portfolio_data():
    """Mock portfolio data"""
    return {
        "id": 1,
        "user_id": 1,
        "total_value": 2050.52,
        "created_at": "2025-11-05T10:00:00",
        "updated_at": "2025-11-05T10:00:00"
    }


@pytest.fixture
def mock_holdings_data():
    """Mock holdings data"""
    return [
        {
            "id": 1,
            "portfolio_id": 1,
            "protocol_name": "Aave",
            "token_symbol": "AAVE",
            "amount": 2.0,
            "value_usd": 191.00,
            "apy": 4.12,
            "created_at": "2025-11-05T10:00:00",
            "updated_at": "2025-11-05T10:00:00"
        },
        {
            "id": 2,
            "portfolio_id": 1,
            "protocol_name": "Lido",
            "token_symbol": "stETH",
            "amount": 0.8,
            "value_usd": 1840.00,
            "apy": 5.24,
            "created_at": "2025-11-05T10:00:00",
            "updated_at": "2025-11-05T10:00:00"
        }
    ]


class TestCoinGeckoIntegration:
    """Test CoinGecko price fetching"""
    
    @pytest.mark.asyncio
    async def test_get_token_prices_success(self, mock_coingecko_prices):
        """Test successful price fetching from CoinGecko"""
        service = PortfolioService()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_coingecko_prices)
            
            mock_get.return_value.__aenter__.return_value = mock_response
            
            prices = await service.get_token_prices(["AAVE", "stETH"])
            
            assert "AAVE" in prices
            assert "stETH" in prices
            assert prices["AAVE"] == 95.50
            assert prices["stETH"] == 2.15
    
    @pytest.mark.asyncio
    async def test_get_token_prices_api_error(self):
        """Test price fetching with API error"""
        service = PortfolioService()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_get.return_value.__aenter__.return_value = mock_response
            
            prices = await service.get_token_prices(["AAVE"])
            
            assert prices == {}
    
    @pytest.mark.asyncio
    async def test_get_token_prices_unknown_symbol(self):
        """Test price fetching with unknown symbol"""
        service = PortfolioService()
        
        prices = await service.get_token_prices(["UNKNOWN_TOKEN"])
        
        # Should return empty dict for unknown tokens
        assert prices == {}


class TestPortfolioRetrieval:
    """Test portfolio retrieval"""
    
    @pytest.mark.asyncio
    async def test_get_user_portfolio_success(
        self,
        mock_user_data,
        mock_portfolio_data,
        mock_holdings_data
    ):
        """Test successful portfolio retrieval"""
        service = PortfolioService()
        
        with patch.object(service, '_get_supabase_client') as mock_client:
            # Mock user response
            mock_user_response = MagicMock()
            mock_user_response.data = [mock_user_data]
            
            # Mock portfolio response
            mock_portfolio_response = MagicMock()
            mock_portfolio_response.data = [mock_portfolio_data]
            
            # Mock holdings response
            mock_holdings_response = MagicMock()
            mock_holdings_response.data = mock_holdings_data
            
            # Setup mock client
            mock_table = MagicMock()
            mock_client.return_value.table.return_value = mock_table
            
            # Chain mock calls
            mock_table.select.return_value.eq.return_value.execute.side_effect = [
                mock_user_response,
                mock_portfolio_response,
                mock_holdings_response
            ]
            
            result = await service.get_user_portfolio("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result is not None
            assert result["wallet_address"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            assert result["risk_preference"] == "medium"
            assert len(result["holdings"]) == 2
            assert result["holdings"][0]["protocol"] == "Aave"
            assert result["holdings"][0]["symbol"] == "AAVE"
            assert result["holdings"][0]["amount"] == 2.0
    
    @pytest.mark.asyncio
    async def test_get_user_portfolio_not_found(self):
        """Test portfolio retrieval for non-existent user"""
        service = PortfolioService()
        
        with patch.object(service, '_get_supabase_client') as mock_client:
            mock_response = MagicMock()
            mock_response.data = []
            
            mock_table = MagicMock()
            mock_client.return_value.table.return_value = mock_table
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            result = await service.get_user_portfolio("0xnonexistent")
            
            assert result is None


class TestHoldingUpdate:
    """Test holding update functionality"""
    
    @pytest.mark.asyncio
    async def test_update_holding_success(
        self,
        mock_user_data,
        mock_portfolio_data,
        mock_coingecko_prices
    ):
        """Test successful holding update"""
        service = PortfolioService()
        
        with patch.object(service, '_get_supabase_client') as mock_client:
            with patch.object(service, 'get_token_prices') as mock_prices:
                with patch.object(service, 'get_user_portfolio') as mock_get_portfolio:
                    # Mock price fetch
                    mock_prices.return_value = {"AAVE": 95.50}
                    
                    # Mock user response
                    mock_user_response = MagicMock()
                    mock_user_response.data = [mock_user_data]
                    
                    # Mock portfolio response
                    mock_portfolio_response = MagicMock()
                    mock_portfolio_response.data = [mock_portfolio_data]
                    
                    # Mock protocol data response
                    mock_protocol_response = MagicMock()
                    mock_protocol_response.data = [{"apy": 4.12}]
                    
                    # Mock existing holding
                    mock_holding_response = MagicMock()
                    mock_holding_response.data = [{"id": 1}]
                    
                    # Mock final portfolio
                    mock_get_portfolio.return_value = {
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "total_value_usd": 191.00,
                        "holdings": [{"protocol": "Aave", "symbol": "AAVE", "amount": 2.0}]
                    }
                    
                    # Setup mock client
                    mock_table = MagicMock()
                    mock_client.return_value.table.return_value = mock_table
                    
                    # Chain responses
                    mock_table.select.return_value.eq.return_value.execute.side_effect = [
                        mock_user_response,
                        mock_portfolio_response,
                        mock_protocol_response,
                        mock_holding_response
                    ]
                    
                    # Mock update
                    mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
                    
                    result = await service.update_holding(
                        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        protocol="Aave",
                        symbol="AAVE",
                        new_amount=2.0
                    )
                    
                    assert result is not None
                    assert result["wallet_address"] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"


class TestPortfolioRefresh:
    """Test portfolio value refresh"""
    
    @pytest.mark.asyncio
    async def test_refresh_portfolio_values(
        self,
        mock_user_data,
        mock_portfolio_data,
        mock_holdings_data
    ):
        """Test refreshing all holdings' USD values"""
        service = PortfolioService()
        
        with patch.object(service, '_get_supabase_client') as mock_client:
            with patch.object(service, 'get_token_prices') as mock_prices:
                with patch.object(service, 'get_user_portfolio') as mock_get_portfolio:
                    # Mock prices
                    mock_prices.return_value = {"AAVE": 100.0, "stETH": 2400.0}
                    
                    # Mock responses
                    mock_user_response = MagicMock()
                    mock_user_response.data = [mock_user_data]
                    
                    mock_portfolio_response = MagicMock()
                    mock_portfolio_response.data = [mock_portfolio_data]
                    
                    mock_holdings_response = MagicMock()
                    mock_holdings_response.data = mock_holdings_data
                    
                    # Mock final portfolio
                    mock_get_portfolio.return_value = {
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "total_value_usd": 2120.00,
                        "holdings": []
                    }
                    
                    # Setup mock client
                    mock_table = MagicMock()
                    mock_client.return_value.table.return_value = mock_table
                    
                    mock_table.select.return_value.eq.return_value.execute.side_effect = [
                        mock_user_response,
                        mock_portfolio_response,
                        mock_holdings_response
                    ]
                    
                    mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
                    
                    result = await service.refresh_portfolio_values("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
                    
                    assert result is not None
                    # Prices should have been fetched
                    mock_prices.assert_called_once()


class TestDemoData:
    """Test demo data seeding"""
    
    @pytest.mark.asyncio
    async def test_seed_demo_data(self, mock_user_data, mock_portfolio_data):
        """Test creating demo portfolio"""
        service = PortfolioService()
        
        with patch.object(service, '_get_supabase_client') as mock_client:
            with patch.object(service, 'get_token_prices') as mock_prices:
                with patch.object(service, 'get_user_portfolio') as mock_get_portfolio:
                    # Mock prices
                    mock_prices.return_value = {"AAVE": 95.50, "stETH": 2300.0}
                    
                    # Mock user exists
                    mock_user_response = MagicMock()
                    mock_user_response.data = [mock_user_data]
                    
                    # Mock portfolio exists
                    mock_portfolio_response = MagicMock()
                    mock_portfolio_response.data = [mock_portfolio_data]
                    
                    # Mock no holdings
                    mock_holdings_response = MagicMock()
                    mock_holdings_response.data = []
                    
                    # Mock final portfolio
                    mock_get_portfolio.return_value = {
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "total_value_usd": 2031.00,
                        "holdings": [
                            {"protocol": "Aave", "symbol": "AAVE", "amount": 2.0},
                            {"protocol": "Lido", "symbol": "stETH", "amount": 0.8}
                        ]
                    }
                    
                    # Setup mock client
                    mock_table = MagicMock()
                    mock_client.return_value.table.return_value = mock_table
                    
                    mock_table.select.return_value.eq.return_value.execute.side_effect = [
                        mock_user_response,
                        mock_portfolio_response,
                        mock_holdings_response
                    ]
                    
                    mock_table.insert.return_value.execute.return_value = MagicMock()
                    
                    result = await service.seed_demo_data()
                    
                    assert result is not None
                    assert len(result["holdings"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

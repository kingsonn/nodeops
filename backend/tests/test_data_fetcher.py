"""
Unit Tests for Data Fetcher Service

Tests for DeFiLlama/CoinGecko integration, normalization, caching, and Supabase storage.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from backend.services import data_fetcher


@pytest.fixture
def mock_defillama_response():
    """Mock DeFiLlama API response"""
    return [
        {
            "project": "aave",
            "chain": "ethereum",
            "apy": 4.12,
            "tvlUsd": 1900000000,
            "symbol": "AAVE",
            "url": "https://aave.com",
            "category": "lending",
            "pool": "aave-v3-eth"
        },
        {
            "project": "lido",
            "chain": "ethereum",
            "apy": 5.24,
            "tvlUsd": 17000000000,
            "symbol": "stETH",
            "url": "https://lido.fi",
            "category": "staking",
            "pool": "lido-eth"
        },
        {
            "project": "curve",
            "chain": "ethereum",
            "apy": 8.5,
            "tvlUsd": 50000,
            "symbol": "CRV",
            "url": "https://curve.fi",
            "category": "dex",
            "pool": "curve-3pool"
        }
    ]


@pytest.fixture
def mock_coingecko_response():
    """Mock CoinGecko API response"""
    return [
        {
            "id": "aave",
            "name": "Aave",
            "symbol": "aave",
            "current_price": 95.50,
            "market_cap": 1400000000
        },
        {
            "id": "lido-dao",
            "name": "Lido DAO",
            "symbol": "ldo",
            "current_price": 2.15,
            "market_cap": 1900000000
        }
    ]


class TestNormalization:
    """Test data normalization functions"""
    
    def test_normalize_defillama_data(self, mock_defillama_response):
        """Test DeFiLlama data normalization"""
        normalized = data_fetcher.normalize_defillama_data(mock_defillama_response)
        
        assert len(normalized) == 3
        
        # Check Aave (medium risk - TVL > 100k but < 1M)
        aave = next(p for p in normalized if p["id"] == "aave")
        assert aave["chain"] == "ethereum"
        assert aave["apy"] == 4.12
        assert aave["tvl_usd"] == 1900000000
        assert aave["risk"] == "low"  # TVL > 1M
        assert aave["metadata"]["symbol"] == "AAVE"
        assert "fetched_at" in aave
        
        # Check Lido (low risk - TVL > 1M)
        lido = next(p for p in normalized if p["id"] == "lido")
        assert lido["risk"] == "low"
        assert lido["tvl_usd"] == 17000000000
        
        # Check Curve (high risk - TVL < 100k)
        curve = next(p for p in normalized if p["id"] == "curve")
        assert curve["risk"] == "high"
        assert curve["tvl_usd"] == 50000
    
    def test_normalize_coingecko_data(self, mock_coingecko_response):
        """Test CoinGecko data normalization"""
        normalized = data_fetcher.normalize_coingecko_data(mock_coingecko_response)
        
        assert len(normalized) == 2
        
        # Check Aave
        aave = next(p for p in normalized if p["id"] == "aave")
        assert aave["chain"] == "ethereum"
        assert aave["metadata"]["symbol"] == "AAVE"
        assert aave["metadata"]["price_usd"] == 95.50
        assert aave["risk"] == "medium"
        
        # Check Lido
        lido = next(p for p in normalized if p["id"] == "lido")
        assert lido["metadata"]["symbol"] == "LDO"


@pytest.mark.asyncio
class TestAPIFetching:
    """Test API fetching functions"""
    
    async def test_fetch_from_defillama_success(self, mock_defillama_response):
        """Test successful DeFiLlama fetch"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the async context manager
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_defillama_response)
            
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await data_fetcher.fetch_from_defillama()
            
            assert len(result) == 3
            assert result[0]["project"] == "aave"
    
    async def test_fetch_from_defillama_error(self):
        """Test DeFiLlama fetch with API error"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await data_fetcher.fetch_from_defillama()
            
            assert result == []
    
    async def test_fetch_from_coingecko_success(self, mock_coingecko_response):
        """Test successful CoinGecko fetch"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_coingecko_response)
            
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await data_fetcher.fetch_from_coingecko()
            
            assert len(result) == 2
            assert result[0]["id"] == "aave"


@pytest.mark.asyncio
class TestCaching:
    """Test caching functionality"""
    
    async def test_cache_miss_then_hit(self, mock_defillama_response):
        """Test cache miss followed by cache hit"""
        # Clear cache
        data_fetcher._cache.clear()
        data_fetcher.metrics["cache_hits"] = 0
        data_fetcher.metrics["cache_misses"] = 0
        
        with patch('backend.services.data_fetcher.fetch_from_defillama') as mock_fetch:
            mock_fetch.return_value = mock_defillama_response
            
            with patch('backend.services.data_fetcher.save_to_supabase') as mock_save:
                mock_save.return_value = len(mock_defillama_response)
                
                # First call - cache miss
                result1 = await data_fetcher.get_cached_data()
                assert data_fetcher.metrics["cache_misses"] == 1
                assert data_fetcher.metrics["cache_hits"] == 0
                assert len(result1["data"]) > 0
                
                # Second call - cache hit
                result2 = await data_fetcher.get_cached_data()
                assert data_fetcher.metrics["cache_hits"] == 1
                assert result1["timestamp"] == result2["timestamp"]
    
    async def test_force_refresh_bypasses_cache(self, mock_defillama_response):
        """Test that fresh=true bypasses cache"""
        data_fetcher._cache.clear()
        data_fetcher.metrics["cache_misses"] = 0
        
        with patch('backend.services.data_fetcher.fetch_from_defillama') as mock_fetch:
            mock_fetch.return_value = mock_defillama_response
            
            with patch('backend.services.data_fetcher.save_to_supabase') as mock_save:
                mock_save.return_value = len(mock_defillama_response)
                
                # First call
                await data_fetcher.get_cached_data()
                
                # Force refresh
                await data_fetcher.get_cached_data(force_refresh=True)
                
                # Should have 2 cache misses (both fetched fresh)
                assert data_fetcher.metrics["cache_misses"] == 2


@pytest.mark.asyncio
class TestSupabaseIntegration:
    """Test Supabase integration"""
    
    async def test_save_to_supabase(self, mock_defillama_response):
        """Test saving data to Supabase"""
        normalized = data_fetcher.normalize_defillama_data(mock_defillama_response)
        
        with patch('backend.services.data_fetcher.get_supabase_client') as mock_client:
            mock_table = MagicMock()
            mock_upsert = MagicMock()
            mock_execute = MagicMock()
            
            mock_client.return_value.table.return_value = mock_table
            mock_table.upsert.return_value = mock_upsert
            mock_upsert.execute.return_value = mock_execute
            
            result = await data_fetcher.save_to_supabase(normalized)
            
            assert result == 3
            assert mock_table.upsert.called


class TestMetrics:
    """Test metrics tracking"""
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        metrics = data_fetcher.get_metrics()
        
        assert "defillama_fetch_total" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "coingecko_fetch_total" in metrics
        assert "supabase_upserts" in metrics
        
        assert isinstance(metrics["cache_hits"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

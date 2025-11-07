"""
AI Agent Tests

Tests for AI agent, Gemini integration, and rebalancing simulation.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.ai_agent import AIAgent


@pytest.fixture
def mock_portfolio_data():
    """Mock portfolio data"""
    return {
        "user_id": 1,
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "risk_preference": "medium",
        "total_value_usd": 2230.64,
        "holdings": [
            {
                "protocol": "Aave",
                "symbol": "AAVE",
                "amount": 2.0,
                "value_usd": 386.64,
                "apy": 4.12
            },
            {
                "protocol": "Lido",
                "symbol": "stETH",
                "amount": 0.8,
                "value_usd": 1844.0,
                "apy": 5.24
            }
        ]
    }


@pytest.fixture
def mock_protocol_data():
    """Mock protocol data"""
    return [
        {
            "name": "Aave",
            "apy": 4.12,
            "tvl": 5000000000,
            "chain": "ethereum",
            "category": "lending"
        },
        {
            "name": "Lido",
            "apy": 5.24,
            "tvl": 20000000000,
            "chain": "ethereum",
            "category": "staking"
        },
        {
            "name": "Curve",
            "apy": 8.5,
            "tvl": 6000000000,
            "chain": "ethereum",
            "category": "dex"
        }
    ]


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return {
        "action": "rebalance",
        "recommendations": [
            {
                "from": "Aave",
                "to": "Curve",
                "percent": 30,
                "reason": "Higher APY with acceptable risk"
            }
        ],
        "expected_yield_increase": 0.75,
        "confidence": 0.82,
        "explanation": "Moving 30% from Aave to Curve will increase portfolio APY while maintaining medium risk profile."
    }


class TestAIAgentInitialization:
    """Test AI agent initialization"""
    
    def test_agent_initialization(self):
        """Test AI agent initializes correctly"""
        agent = AIAgent()
        assert agent is not None


class TestSimulation:
    """Test rebalancing simulation"""
    
    def test_calculate_weighted_apy(self):
        """Test weighted APY calculation"""
        agent = AIAgent()
        
        holdings = [
            {"value_usd": 1000, "apy": 5.0},
            {"value_usd": 1000, "apy": 3.0}
        ]
        
        weighted_apy = agent._calculate_weighted_apy(holdings, 2000)
        
        assert weighted_apy == 4.0  # (1000*5 + 1000*3) / 2000


class TestPromptBuilding:
    """Test prompt construction"""
    
    def test_build_reasoning_prompt(
        self,
        mock_portfolio_data,
        mock_protocol_data
    ):
        """Test prompt building for Gemini"""
        agent = AIAgent()
        
        prompt = agent._build_reasoning_prompt(
            mock_portfolio_data,
            mock_protocol_data,
            "medium"
        )
        
        assert "DeFi portfolio strategist" in prompt
        assert "medium" in prompt
        assert "Aave" in prompt
        assert "Lido" in prompt
        assert "JSON" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

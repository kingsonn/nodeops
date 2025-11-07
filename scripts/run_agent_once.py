#!/usr/bin/env python3
"""
CLI Agent Trigger

Manually trigger the AI agent to analyze a portfolio and generate recommendations.

Usage:
    python scripts/run_agent_once.py --wallet 0x123...
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.reasoning_engine import initialize_agent, analyze_portfolio

def main():
    parser = argparse.ArgumentParser(description='Run AI agent analysis')
    parser.add_argument('--wallet', type=str, help='Wallet address to analyze')
    args = parser.parse_args()
    
    print("=== AutoDeFi.AI Agent CLI ===")
    
    # Initialize agent
    result = initialize_agent()
    print(f"Agent status: {result['status']}")
    
    # Run analysis
    if args.wallet:
        print(f"\nAnalyzing portfolio for wallet: {args.wallet}")
        portfolio_data = {"wallet": args.wallet, "holdings": []}
        recommendations = analyze_portfolio(portfolio_data)
        print(f"\nRecommendations: {recommendations}")
    else:
        print("\n⚠️  No wallet address provided. Use --wallet flag.")

if __name__ == "__main__":
    main()

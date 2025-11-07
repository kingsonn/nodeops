-- =====================================================
-- Seed Protocol Market Data Table
-- =====================================================
-- This script populates the protocol_market_data table with
-- realistic DeFi protocol data including prices and APYs.
-- Run this in Supabase SQL Editor.
-- =====================================================

-- Create table if it doesn't exist
CREATE TABLE IF NOT EXISTS protocol_market_data (
    id SERIAL PRIMARY KEY,
    protocol_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price_usd DECIMAL(20, 8) NOT NULL DEFAULT 0,
    apy DECIMAL(8, 4) NOT NULL DEFAULT 0,
    tvl_usd DECIMAL(20, 2) DEFAULT 0,
    category VARCHAR(50),
    chain VARCHAR(50) DEFAULT 'Ethereum',
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(protocol_name, symbol)
);

-- Clear existing data
TRUNCATE TABLE protocol_market_data;

-- Insert Top 20 DeFi Protocols with realistic data
INSERT INTO protocol_market_data (protocol_name, symbol, price_usd, apy, tvl_usd, category, chain) VALUES
-- Aave
('Aave', 'AAVE', 95.50, 4.2, 5800000000, 'Lending', 'Ethereum'),
('Aave', 'USDC', 1.00, 3.8, 5800000000, 'Lending', 'Ethereum'),
('Aave', 'USDT', 1.00, 3.5, 5800000000, 'Lending', 'Ethereum'),
('Aave', 'DAI', 1.00, 4.1, 5800000000, 'Lending', 'Ethereum'),
('Aave', 'WETH', 2450.00, 2.9, 5800000000, 'Lending', 'Ethereum'),
('Aave', 'WBTC', 43500.00, 2.5, 5800000000, 'Lending', 'Ethereum'),

-- Lido
('Lido', 'stETH', 2450.00, 3.8, 14200000000, 'Liquid Staking', 'Ethereum'),
('Lido', 'wstETH', 2680.00, 3.8, 14200000000, 'Liquid Staking', 'Ethereum'),
('Lido', 'LDO', 1.85, 0, 14200000000, 'Liquid Staking', 'Ethereum'),

-- Compound
('Compound', 'COMP', 52.30, 5.5, 3200000000, 'Lending', 'Ethereum'),
('Compound', 'USDC', 1.00, 4.2, 3200000000, 'Lending', 'Ethereum'),
('Compound', 'USDT', 1.00, 3.9, 3200000000, 'Lending', 'Ethereum'),
('Compound', 'DAI', 1.00, 4.5, 3200000000, 'Lending', 'Ethereum'),
('Compound', 'ETH', 2450.00, 3.1, 3200000000, 'Lending', 'Ethereum'),

-- Curve
('Curve', 'CRV', 0.68, 8.5, 4100000000, 'DEX', 'Ethereum'),
('Curve', '3CRV', 1.00, 6.2, 4100000000, 'DEX', 'Ethereum'),
('Curve', 'USDC', 1.00, 5.8, 4100000000, 'DEX', 'Ethereum'),
('Curve', 'USDT', 1.00, 5.5, 4100000000, 'DEX', 'Ethereum'),
('Curve', 'DAI', 1.00, 6.0, 4100000000, 'DEX', 'Ethereum'),

-- Uniswap
('Uniswap', 'UNI', 6.25, 12.3, 3800000000, 'DEX', 'Ethereum'),
('Uniswap', 'USDC', 1.00, 8.5, 3800000000, 'DEX', 'Ethereum'),
('Uniswap', 'WETH', 2450.00, 9.2, 3800000000, 'DEX', 'Ethereum'),
('Uniswap', 'USDT', 1.00, 7.8, 3800000000, 'DEX', 'Ethereum'),

-- Yearn
('Yearn', 'YFI', 7850.00, 15.2, 450000000, 'Yield Aggregator', 'Ethereum'),
('Yearn', 'yvUSDC', 1.02, 12.5, 450000000, 'Yield Aggregator', 'Ethereum'),
('Yearn', 'yvDAI', 1.01, 11.8, 450000000, 'Yield Aggregator', 'Ethereum'),

-- MakerDAO
('MakerDAO', 'MKR', 1450.00, 0, 5600000000, 'Lending', 'Ethereum'),
('MakerDAO', 'DAI', 1.00, 5.0, 5600000000, 'Lending', 'Ethereum'),

-- Balancer
('Balancer', 'BAL', 3.15, 18.5, 1200000000, 'DEX', 'Ethereum'),
('Balancer', 'USDC', 1.00, 10.2, 1200000000, 'DEX', 'Ethereum'),
('Balancer', 'WETH', 2450.00, 11.5, 1200000000, 'DEX', 'Ethereum'),

-- Sushiswap
('Sushiswap', 'SUSHI', 0.95, 14.8, 850000000, 'DEX', 'Ethereum'),
('Sushiswap', 'USDC', 1.00, 9.5, 850000000, 'DEX', 'Ethereum'),
('Sushiswap', 'WETH', 2450.00, 10.2, 850000000, 'DEX', 'Ethereum'),

-- PancakeSwap
('PancakeSwap', 'CAKE', 2.35, 22.5, 1800000000, 'DEX', 'BSC'),
('PancakeSwap', 'BUSD', 1.00, 15.2, 1800000000, 'DEX', 'BSC'),
('PancakeSwap', 'BNB', 315.00, 18.5, 1800000000, 'DEX', 'BSC'),

-- RocketPool
('RocketPool', 'rETH', 2680.00, 4.2, 2100000000, 'Liquid Staking', 'Ethereum'),
('RocketPool', 'RPL', 28.50, 5.5, 2100000000, 'Liquid Staking', 'Ethereum'),

-- Frax
('Frax', 'FRAX', 1.00, 6.5, 1500000000, 'Stablecoin', 'Ethereum'),
('Frax', 'FXS', 8.20, 12.8, 1500000000, 'Stablecoin', 'Ethereum'),
('Frax', 'sfrxETH', 2680.00, 5.2, 1500000000, 'Liquid Staking', 'Ethereum'),

-- Convex
('Convex', 'CVX', 2.85, 25.5, 3500000000, 'Yield Aggregator', 'Ethereum'),
('Convex', 'cvxCRV', 0.75, 20.2, 3500000000, 'Yield Aggregator', 'Ethereum'),

-- dYdX
('dYdX', 'DYDX', 1.95, 8.5, 950000000, 'Derivatives', 'Ethereum'),
('dYdX', 'USDC', 1.00, 5.2, 950000000, 'Derivatives', 'Ethereum'),

-- GMX
('GMX', 'GMX', 42.50, 28.5, 650000000, 'Derivatives', 'Arbitrum'),
('GMX', 'GLP', 1.05, 22.8, 650000000, 'Derivatives', 'Arbitrum'),

-- Ethena
('Ethena', 'ENA', 0.52, 35.5, 1200000000, 'Synthetic Assets', 'Ethereum'),
('Ethena', 'USDe', 1.00, 28.2, 1200000000, 'Synthetic Assets', 'Ethereum'),
('Ethena', 'sUSDe', 1.08, 32.5, 1200000000, 'Synthetic Assets', 'Ethereum'),

-- Synthetix
('Synthetix', 'SNX', 2.45, 18.5, 550000000, 'Derivatives', 'Ethereum'),
('Synthetix', 'sUSD', 1.00, 12.2, 550000000, 'Derivatives', 'Ethereum'),

-- Morpho
('Morpho', 'MORPHO', 1.85, 15.8, 850000000, 'Lending', 'Ethereum'),
('Morpho', 'USDC', 1.00, 8.5, 850000000, 'Lending', 'Ethereum'),
('Morpho', 'WETH', 2450.00, 7.2, 850000000, 'Lending', 'Ethereum'),

-- Stargate
('Stargate', 'STG', 0.48, 18.5, 750000000, 'Bridge', 'Ethereum'),
('Stargate', 'USDC', 1.00, 12.5, 750000000, 'Bridge', 'Ethereum'),
('Stargate', 'USDT', 1.00, 11.8, 750000000, 'Bridge', 'Ethereum'),

-- Venus
('Venus', 'XVS', 8.50, 22.5, 650000000, 'Lending', 'BSC'),
('Venus', 'BUSD', 1.00, 15.2, 650000000, 'Lending', 'BSC'),
('Venus', 'BNB', 315.00, 12.8, 650000000, 'Lending', 'BSC'),

-- Additional popular tokens
('Ethereum', 'ETH', 2450.00, 0, 0, 'Native', 'Ethereum'),
('Ethereum', 'WETH', 2450.00, 0, 0, 'Wrapped', 'Ethereum'),
('Bitcoin', 'WBTC', 43500.00, 0, 0, 'Wrapped', 'Ethereum'),
('Tether', 'USDT', 1.00, 0, 0, 'Stablecoin', 'Ethereum'),
('USD Coin', 'USDC', 1.00, 0, 0, 'Stablecoin', 'Ethereum'),
('Dai', 'DAI', 1.00, 0, 0, 'Stablecoin', 'Ethereum'),
('Chainlink', 'LINK', 14.25, 0, 0, 'Oracle', 'Ethereum');

-- Update last_updated timestamp
UPDATE protocol_market_data SET last_updated = NOW();

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_protocol_market_data_symbol ON protocol_market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_protocol_market_data_protocol ON protocol_market_data(protocol_name);
CREATE INDEX IF NOT EXISTS idx_protocol_market_data_category ON protocol_market_data(category);

-- Verify data
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT protocol_name) as unique_protocols,
    COUNT(DISTINCT symbol) as unique_symbols
FROM protocol_market_data;

-- Show sample data
SELECT 
    protocol_name,
    symbol,
    price_usd,
    apy,
    category
FROM protocol_market_data
ORDER BY tvl_usd DESC NULLS LAST
LIMIT 20;

-- =====================================================
-- Success! Protocol market data seeded.
-- =====================================================

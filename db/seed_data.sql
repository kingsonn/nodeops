-- Seed data for development and testing

-- Sample protocols
INSERT INTO protocol_data (protocol_name, tvl, apy, chain, category, data) VALUES
('Aave', 5000000000, 3.5, 'ethereum', 'lending', '{"url": "https://aave.com"}'),
('Compound', 3000000000, 2.8, 'ethereum', 'lending', '{"url": "https://compound.finance"}'),
('Uniswap V3', 4000000000, 15.2, 'ethereum', 'dex', '{"url": "https://uniswap.org"}'),
('Curve', 6000000000, 8.5, 'ethereum', 'dex', '{"url": "https://curve.fi"}'),
('Lido', 20000000000, 4.2, 'ethereum', 'staking', '{"url": "https://lido.fi"}')
ON CONFLICT (protocol_name) DO NOTHING;

-- Sample user (for testing)
INSERT INTO users (wallet_address, risk_preference) VALUES
('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', 'medium')
ON CONFLICT (wallet_address) DO NOTHING;

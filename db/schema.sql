-- AutoDeFi.AI Database Schema
-- PostgreSQL 15+

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    risk_preference VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_value DECIMAL(20, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio holdings
CREATE TABLE IF NOT EXISTS holdings (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    protocol_name VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    value_usd DECIMAL(20, 2) NOT NULL,
    apy DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Protocol data cache
CREATE TABLE IF NOT EXISTS protocol_data (
    id SERIAL PRIMARY KEY,
    protocol_name VARCHAR(100) UNIQUE NOT NULL,
    tvl DECIMAL(20, 2),
    apy DECIMAL(10, 4),
    chain VARCHAR(50),
    category VARCHAR(50),
    data JSONB,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction logs
CREATE TABLE IF NOT EXISTS transaction_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL,
    from_protocol VARCHAR(100),
    to_protocol VARCHAR(100),
    amount DECIMAL(20, 8),
    status VARCHAR(20) DEFAULT 'pending',
    tx_hash VARCHAR(66),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI decision logs
CREATE TABLE IF NOT EXISTS ai_decision_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recommendation JSONB NOT NULL,
    explanation TEXT,
    confidence DECIMAL(5, 4),
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_portfolios_user ON portfolios(user_id);
CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);
CREATE INDEX idx_transaction_logs_user ON transaction_logs(user_id);
CREATE INDEX idx_ai_decision_logs_user ON ai_decision_logs(user_id);
CREATE INDEX idx_protocol_data_name ON protocol_data(protocol_name);

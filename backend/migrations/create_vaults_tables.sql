-- ============================================
-- AI Vaults Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Create vaults table (if not exists / alter if exists)
CREATE TABLE IF NOT EXISTS vaults (
  id SERIAL PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  description TEXT,
  risk_level VARCHAR(20) DEFAULT 'medium',
  expected_apy DECIMAL(10,4) DEFAULT 0.0,
  allocations JSONB NOT NULL, -- [{"protocol_name":"lido","percent":50}, ...]
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ai_description TEXT, -- raw text/explanation from AI
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ensure columns exist if vaults was created previously without them
ALTER TABLE vaults
  ADD COLUMN IF NOT EXISTS expected_apy DECIMAL(10,4),
  ADD COLUMN IF NOT EXISTS allocations JSONB,
  ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP,
  ADD COLUMN IF NOT EXISTS ai_description TEXT;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_vaults_risk_level ON vaults(risk_level);
CREATE INDEX IF NOT EXISTS idx_vaults_last_updated ON vaults(last_updated DESC);

-- 2. Create vault_subscriptions (demo persistence of simulated deposits)
CREATE TABLE IF NOT EXISTS vault_subscriptions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  vault_id INTEGER REFERENCES vaults(id) ON DELETE CASCADE,
  deposit_amount DECIMAL(20,2) NOT NULL,
  simulated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vault_subscriptions_user ON vault_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_vault_subscriptions_vault ON vault_subscriptions(vault_id);

-- 3. Create vault_ai_logs — structured log of AI decisions for vault generation/updates
CREATE TABLE IF NOT EXISTS vault_ai_logs (
  id SERIAL PRIMARY KEY,
  vault_id INTEGER REFERENCES vaults(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL, -- 'generate' | 'update' | 'error'
  payload JSONB, -- raw AI output and metadata
  summary TEXT,  -- short human-friendly summary ("Moved 10% Aave -> Curve")
  confidence DECIMAL(5,4),
  ai_model VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vault_ai_logs_vault ON vault_ai_logs(vault_id);
CREATE INDEX IF NOT EXISTS idx_vault_ai_logs_created ON vault_ai_logs(created_at DESC);

-- 4. Add trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_vaults_updated_at ON vaults;
CREATE TRIGGER update_vaults_updated_at
    BEFORE UPDATE ON vaults
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Verification Queries (run these to check)
-- ============================================

-- Check vaults table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'vaults'
ORDER BY ordinal_position;

-- Check vault_ai_logs table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'vault_ai_logs'
ORDER BY ordinal_position;

-- Check vault_subscriptions table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'vault_subscriptions'
ORDER BY ordinal_position;

-- ============================================
-- Sample Data (optional - for testing)
-- ============================================

-- Insert a sample vault
INSERT INTO vaults (name, description, risk_level, expected_apy, allocations, ai_description)
VALUES (
  'AI Balanced Yield v1',
  'Optimized for steady growth using staking and lending pools',
  'medium',
  4.35,
  '[
    {"protocol_name": "lido", "percent": 50},
    {"protocol_name": "aave-v3", "percent": 30},
    {"protocol_name": "curve", "percent": 20}
  ]'::jsonb,
  'This vault balances liquid staking with lending protocols for stable returns'
)
ON CONFLICT DO NOTHING;

-- Insert a sample log entry
INSERT INTO vault_ai_logs (vault_id, event_type, payload, summary, confidence, ai_model)
SELECT 
  id,
  'generate',
  '{"allocations": [{"protocol_name": "lido", "percent": 50}], "reasoning": "Diversified allocation"}'::jsonb,
  'Initial vault generation with balanced allocation',
  0.85,
  'llama-3.3-70b-versatile'
FROM vaults
WHERE name = 'AI Balanced Yield v1'
LIMIT 1
ON CONFLICT DO NOTHING;

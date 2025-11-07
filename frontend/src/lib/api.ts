/**
 * API Client for AutoDeFi.AI Backend
 * 
 * Centralized API communication with type-safe methods.
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,  // 2 minutes for AI analysis with full Gemini reasoning
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Get the wallet address to use for API calls based on current mode
 */
export function getActiveWallet(): string {
  if (typeof window === 'undefined') {
    return '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'; // Demo wallet for SSR
  }
  
  // Import dynamically to avoid SSR issues
  const { useStore } = require('@/lib/store');
  const { mode, walletAddress, demoWallet } = useStore.getState();
  
  return mode === 'wallet' ? (walletAddress || demoWallet) : demoWallet;
}

/**
 * Get the current mode
 */
export function getMode(): 'demo' | 'wallet' {
  if (typeof window === 'undefined') {
    return 'demo';
  }
  
  const { useStore } = require('@/lib/store');
  const { mode } = useStore.getState();
  
  return mode;
}

/**
 * Get portfolio data based on current mode
 * Ensures clean separation between demo and wallet data
 */
export async function getPortfolio(): Promise<Portfolio> {
  if (typeof window === 'undefined') {
    throw new Error('Cannot fetch portfolio on server side');
  }
  
  const { useStore } = require('@/lib/store');
  const { mode, walletAddress, demoWallet } = useStore.getState();
  
  if (mode === 'demo') {
    // Always use demo endpoint in demo mode
    const { data } = await client.get('/api/portfolio/demo');
    return data;
  } else {
    // Use wallet-specific endpoint in wallet mode
    const wallet = walletAddress || demoWallet;
    const { data } = await client.get(`/api/portfolio?wallet=${wallet}`);
    return data;
  }
}

// Type definitions
export interface Portfolio {
  user_id: number;
  wallet_address: string;
  risk_preference: string;
  total_value_usd: number;
  holdings: Holding[];
}

export interface Holding {
  protocol: string;
  symbol: string;
  amount: number;
  value_usd: number;
  apy: number;
}

export interface AIAnalysis {
  wallet: string;
  timestamp: string;
  ai_model: string;
  action: string;
  recommendations: Recommendation[];
  expected_yield_increase: number;
  confidence: number;
  explanation: string;
  ai_reasoning?: {
    category_analysis: string;
    optimization_directions: string[];
    risk_assessment: string;
  };
}

export interface Recommendation {
  from: string;
  to: string;
  percent: number;
  reason: string;
}

export interface Simulation {
  wallet: string;
  timestamp: string;
  before_total_apy: number;
  after_total_apy: number;
  apy_increase: number;
  expected_gain_usd: number;
  simulated_changes: Recommendation[];
  confidence: number;
  explanation: string;
}

// API methods
export const api = {
  // Portfolio endpoints
  portfolio: {
    get: async (wallet: string): Promise<Portfolio> => {
      const { data } = await client.get(`/api/portfolio?wallet=${wallet}`);
      return data;
    },
    
    update: async (wallet: string, protocol: string, symbol: string, amount: number): Promise<Portfolio> => {
      const { data } = await client.post('/api/portfolio/update', {
        wallet,
        protocol,
        symbol,
        amount,
      });
      return data;
    },
    
    refresh: async (wallet: string): Promise<Portfolio> => {
      const { data } = await client.post(`/api/portfolio/refresh?wallet=${wallet}`);
      return data;
    },
    
    demo: async (): Promise<Portfolio> => {
      const { data } = await client.get('/api/portfolio/demo');
      return data;
    },
    
    loadDemo: async (wallet: string): Promise<Portfolio> => {
      const { data } = await client.get(`/api/portfolio/demo?wallet=${wallet}`);
      return data;
    },
  },
  
  // AI endpoints
  ai: {
    analyze: async (wallet: string): Promise<AIAnalysis> => {
      const { data } = await client.get(`/api/ai/analyze?wallet=${wallet}`);
      return data;
    },
    
    simulate: async (wallet: string): Promise<Simulation> => {
      const { data } = await client.get(`/api/ai/simulate?wallet=${wallet}`);
      return data;
    },
    
    execute: async (wallet: string, decisionId: number): Promise<any> => {
      const { data } = await client.post('/api/ai/execute', {
        wallet,
        decision_id: decisionId,
      });
      return data;
    },
  },
  
  // Data endpoints
  data: {
    getProtocols: async (): Promise<any> => {
      const { data } = await client.get('/api/data');
      return data;
    },
  },
  
  // Vaults endpoints
  vaults: {
    list: async (): Promise<any[]> => {
      const { data } = await client.get('/api/vaults');
      return data;
    },
    
    get: async (vaultId: number): Promise<any> => {
      const { data } = await client.get(`/api/vaults/${vaultId}`);
      return data;
    },
    
    generate: async (riskPreference: 'low' | 'medium' | 'high'): Promise<any> => {
      const { data } = await client.post('/api/vaults/generate', {
        risk_preference: riskPreference
      });
      return data;
    },
    
    simulate: async (payload: {
      wallet: string;
      vault_id: number;
      deposit_amount: number;
      subscribe?: boolean;
    }): Promise<any> => {
      const { data } = await client.post('/api/vaults/simulate', payload);
      return data;
    },
    
    refresh: async (vaultId: number): Promise<any> => {
      const { data } = await client.post(`/api/vaults/${vaultId}/refresh`);
      return data;
    },
    
    getLogs: async (vaultId: number, limit: number = 10): Promise<any[]> => {
      const { data } = await client.get(`/api/vaults/${vaultId}/logs?limit=${limit}`);
      return data;
    },
  },
};

// SWR fetcher
export const fetcher = (url: string) => client.get(url).then(res => res.data);

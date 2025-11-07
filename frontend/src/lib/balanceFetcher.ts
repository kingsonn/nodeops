/**
 * On-Chain Balance Fetcher
 * 
 * Fetches real token balances from blockchain using ethers.js
 * Read-only operations - no transactions or approvals
 */

import { ethers } from 'ethers';
import ERC20_ABI from './erc20_abi.json';

export interface TokenBalances {
  [symbol: string]: number;
}

export interface NetworkInfo {
  chainId: number;
  name: string;
}

// Common ERC-20 token addresses on Ethereum Mainnet
export const MAINNET_TOKENS: Record<string, string> = {
  USDC: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
  DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F',
  WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
  USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
  AAVE: '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
};

/**
 * Get token balances for a wallet address
 * 
 * @param address - Wallet address to fetch balances for
 * @param tokens - Map of token symbols to contract addresses
 * @returns Object with token symbols as keys and balances as values
 */
export async function getTokenBalances(
  address: string,
  tokens: Record<string, string> = MAINNET_TOKENS
): Promise<TokenBalances> {
  try {
    // Check if MetaMask is available
    if (typeof window === 'undefined' || !(window as any).ethereum) {
      console.warn('MetaMask not available');
      return {};
    }

    const provider = new ethers.BrowserProvider((window as any).ethereum);
    const balances: TokenBalances = {};

    // Fetch ETH balance first
    try {
      const ethBalance = await provider.getBalance(address);
      balances['ETH'] = Number(ethers.formatEther(ethBalance));
    } catch (error) {
      console.warn('Failed to fetch ETH balance:', error);
      balances['ETH'] = 0;
    }

    // Fetch ERC-20 token balances in parallel
    const tokenPromises = Object.entries(tokens).map(async ([symbol, contractAddress]) => {
      try {
        const token = new ethers.Contract(contractAddress, ERC20_ABI, provider);
        
        // Fetch balance and decimals in parallel
        const [balance, decimals] = await Promise.all([
          token.balanceOf(address),
          token.decimals(),
        ]);

        return {
          symbol,
          balance: Number(ethers.formatUnits(balance, decimals)),
        };
      } catch (error) {
        console.warn(`Failed to fetch balance for ${symbol}:`, error);
        return { symbol, balance: 0 };
      }
    });

    const tokenResults = await Promise.all(tokenPromises);
    
    // Add token balances to result
    tokenResults.forEach(({ symbol, balance }) => {
      balances[symbol] = balance;
    });

    return balances;
  } catch (error) {
    console.error('Error fetching token balances:', error);
    return {};
  }
}

/**
 * Get current network information
 * 
 * @returns Network info including chain ID and name
 */
export async function getNetworkInfo(): Promise<NetworkInfo | null> {
  try {
    if (typeof window === 'undefined' || !(window as any).ethereum) {
      return null;
    }

    const provider = new ethers.BrowserProvider((window as any).ethereum);
    const network = await provider.getNetwork();

    return {
      chainId: Number(network.chainId),
      name: getNetworkName(Number(network.chainId)),
    };
  } catch (error) {
    console.error('Error fetching network info:', error);
    return null;
  }
}

/**
 * Get human-readable network name from chain ID
 * 
 * @param chainId - Chain ID number
 * @returns Network name
 */
export function getNetworkName(chainId: number): string {
  const networks: Record<number, string> = {
    1: 'Ethereum Mainnet',
    5: 'Goerli Testnet',
    11155111: 'Sepolia Testnet',
    137: 'Polygon Mainnet',
    80001: 'Mumbai Testnet',
    42161: 'Arbitrum One',
    10: 'Optimism',
    8453: 'Base',
  };

  return networks[chainId] || `Unknown Network (${chainId})`;
}

/**
 * Cache key for localStorage
 */
const BALANCE_CACHE_KEY = 'wallet_balances_cache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface BalanceCache {
  address: string;
  balances: TokenBalances;
  timestamp: number;
}

/**
 * Get cached balances if available and not expired
 * 
 * @param address - Wallet address
 * @returns Cached balances or null
 */
export function getCachedBalances(address: string): TokenBalances | null {
  try {
    const cached = localStorage.getItem(BALANCE_CACHE_KEY);
    if (!cached) return null;

    const data: BalanceCache = JSON.parse(cached);
    
    // Check if cache is for the same address and not expired
    if (
      data.address.toLowerCase() === address.toLowerCase() &&
      Date.now() - data.timestamp < CACHE_DURATION
    ) {
      return data.balances;
    }

    return null;
  } catch (error) {
    console.warn('Error reading balance cache:', error);
    return null;
  }
}

/**
 * Cache balances in localStorage
 * 
 * @param address - Wallet address
 * @param balances - Token balances to cache
 */
export function cacheBalances(address: string, balances: TokenBalances): void {
  try {
    const data: BalanceCache = {
      address,
      balances,
      timestamp: Date.now(),
    };
    localStorage.setItem(BALANCE_CACHE_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn('Error caching balances:', error);
  }
}

/**
 * Clear balance cache
 */
export function clearBalanceCache(): void {
  try {
    localStorage.removeItem(BALANCE_CACHE_KEY);
  } catch (error) {
    console.warn('Error clearing balance cache:', error);
  }
}

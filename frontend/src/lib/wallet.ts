/**
 * Wallet Configuration with Wagmi
 * 
 * Configures MetaMask connector using Injected Connector (no SDK dependencies)
 */

import { createConfig, http } from 'wagmi';
import { mainnet, polygon } from 'wagmi/chains';
import { injected } from 'wagmi/connectors';

// Configure supported chains
export const chains = [mainnet, polygon] as const;

// Create wagmi configuration with Injected Connector
// This uses window.ethereum directly - no React Native or SDK dependencies
export const config = createConfig({
  chains,
  connectors: [
    injected({
      shimDisconnect: true,
      target: 'metaMask',
    }),
  ],
  transports: {
    [mainnet.id]: http(),
    [polygon.id]: http(),
  },
});

// Demo wallet address for fallback mode
export const DEMO_WALLET = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb';

// Check if MetaMask is available
export const isMetaMaskAvailable = (): boolean => {
  if (typeof window === 'undefined') return false;
  return typeof window.ethereum !== 'undefined';
};

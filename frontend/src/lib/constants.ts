/**
 * Application Constants
 * 
 * Centralized constants for the application.
 */

export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const

export const SUPPORTED_CHAINS = {
  ETHEREUM: 1,
  POLYGON: 137,
  ARBITRUM: 42161,
} as const

export const REFRESH_INTERVAL = 60000 // 1 minute in milliseconds

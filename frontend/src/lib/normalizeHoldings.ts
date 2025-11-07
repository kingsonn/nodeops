/**
 * Holdings Normalization Helper
 * 
 * Standardizes holding field names across the app to prevent crashes
 * and ensure consistency between backend and frontend.
 */

export interface NormalizedHolding {
  id: number;
  protocol_name: string;
  token_symbol: string;
  amount: number;
  apy: number;
  value_usd: number;
  last_updated: string | null;
}

/**
 * Normalize holdings data from various sources
 * Handles both backend responses and wallet data
 * 
 * @param holdings - Array of holdings from any source
 * @returns Normalized holdings array with consistent field names
 */
export function normalizeHoldings(holdings: any[] = []): NormalizedHolding[] {
  if (!Array.isArray(holdings)) {
    console.warn('[normalizeHoldings] Invalid holdings data, expected array:', holdings);
    return [];
  }

  return holdings.map((h, index) => ({
    id: h.id !== undefined ? h.id : index,  // ✅ Use h.id even if it's 0
    protocol_name: h.protocol_name || h.protocol || h.provider || 'Unknown',
    token_symbol: (h.token_symbol || h.symbol || '').toUpperCase(),
    amount: Number(h.amount ?? h.balance ?? 0),
    apy: Number(h.apy ?? 0),
    value_usd: Number(h.value_usd ?? 0),
    last_updated: h.updated_at || h.last_updated || null,
  }));
}

/**
 * Safe number formatting with fallback
 * Prevents .toFixed() crashes on undefined/null values
 */
export function safeToFixed(value: any, decimals: number = 2): string {
  const num = Number(value ?? 0);
  if (isNaN(num)) return '0.' + '0'.repeat(decimals);
  return num.toFixed(decimals);
}

/**
 * Safe currency formatting
 */
export function safeCurrency(value: any): string {
  const num = Number(value ?? 0);
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

/**
 * Safe percentage formatting
 */
export function safePercent(value: any, decimals: number = 2): string {
  const num = Number(value ?? 0);
  if (isNaN(num)) return '0.' + '0'.repeat(decimals) + '%';
  return num.toFixed(decimals) + '%';
}

/**
 * Utility functions for working with QWebChannel backend bridge
 */

/**
 * Calls a backend function with JSON parameters and returns parsed result
 * @param backend The backend object from QWebChannel
 * @param functionName The name of the function to call
 * @param params Parameters to pass to the function (will be converted to JSON)
 * @returns Promise with parsed result
 */
export async function callBackend<T>(
  backend: Backend | null, 
  functionName: keyof Backend,
  ...params: any[]
): Promise<T> {
  if (!backend) {
    throw new Error('Backend not available');
  }

  try {
    // Call the function - depending on how many parameters we have
    let result: string;
    if (params.length === 0) {
      // Zero parameter call
      result = await (backend[functionName] as any)();
    } else if (params.length === 1 && typeof params[0] === 'object') {
      // Single object parameter - convert to JSON
      result = await (backend[functionName] as any)(JSON.stringify(params[0]));
    } else {
      // Multiple parameters - pass as is
      result = await (backend[functionName] as any)(...params);
    }

    // Parse the result if it's a string
    if (typeof result === 'string') {
      try {
        return JSON.parse(result) as T;
      } catch (e) {
        // Not JSON, return as is
        return result as unknown as T;
      }
    }
    
    return result as T;
  } catch (error) {
    console.error(`Error calling ${functionName}:`, error);
    throw error;
  }
}

/**
 * Helper for common get operations with no parameters
 */
export async function getFromBackend<T>(
  backend: Backend | null,
  functionName: keyof Backend
): Promise<T> {
  return callBackend<T>(backend, functionName);
}

/**
 * Helper for network status information
 */
export async function getNetworkStatus(backend: Backend | null): Promise<{
  connected: boolean;
  network: string;
  peers: number;
  height: number;
  error?: string;
}> {
  return getFromBackend(backend, 'get_network_status');
}

/**
 * Helper for wallet balances
 */
export async function getWalletBalances(backend: Backend | null): Promise<{
  total_evr: number;
  evr: Record<string, number>;
  assets: Record<string, Record<string, number>>;
  error?: string;
}> {
  return getFromBackend(backend, 'get_wallet_balances');
}

/**
 * Helper for wallet addresses
 */
export async function getWalletAddresses(backend: Backend | null): Promise<Array<{
  index: number;
  address: string;
  path: string;
  label: string;
  wallet: string;
  public_key: string;
}>
> {
  return getFromBackend(backend, 'get_wallet_addresses');
}

/**
 * Helper for messages
 */
export async function getMessages(backend: Backend | null): Promise<Array<{
  id: string;
  sender: string;
  timestamp: number;
  subject: string;
  content: string;
  read: boolean;
}>> {
  return getFromBackend(backend, 'get_messages');
} 
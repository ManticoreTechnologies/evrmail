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

/**
 * Helper for contacts
 */
export async function getContacts(backend: Backend | null): Promise<Record<string, any>> {
  return getFromBackend(backend, 'get_contacts');
}

/**
 * Helper for contact requests
 */
export async function getContactRequests(backend: Backend | null): Promise<Record<string, any>> {
  return getFromBackend(backend, 'get_contact_requests');
}

/**
 * Helper for sending contact requests
 */
export async function sendContactRequest(
  backend: Backend | null,
  address: string,
  name?: string,
  addressMode: string = "random",
  fromAddress?: string,
  dryRun: boolean = false
): Promise<{success: boolean, error?: string}> {
  return callBackend(
    backend, 
    'send_contact_request', 
    address, 
    name, 
    addressMode,
    fromAddress,
    dryRun
  );
}

/**
 * Helper for removing contacts
 */
export async function removeContact(
  backend: Backend | null,
  address: string
): Promise<{success: boolean, error?: string}> {
  return callBackend(backend, 'remove_contact', address);
}

/**
 * Helper for accepting contact requests
 */
export async function acceptContactRequest(
  backend: Backend | null,
  address: string
): Promise<{success: boolean, error?: string}> {
  return callBackend(backend, 'accept_contact_request', address);
}

/**
 * Helper for rejecting contact requests
 */
export async function rejectContactRequest(
  backend: Backend | null,
  address: string
): Promise<{success: boolean, error?: string}> {
  return callBackend(backend, 'reject_contact_request', address);
}

/**
 * Helper for wallet list
 */
export async function getWalletList(backend: Backend | null): Promise<string[]> {
  return getFromBackend(backend, 'get_wallet_list');
}

/**
 * Helper for UTXOs
 */
export async function getUTXOs(backend: Backend | null): Promise<any[]> {
  return getFromBackend(backend, 'get_utxos');
}

/**
 * Helper for sending EVR
 */
export async function sendEVR(
  backend: Backend | null,
  address: string,
  amount: number,
  dryRun = false
): Promise<{success: boolean; txid?: string; error?: string; message?: string}> {
  return callBackend(backend, 'send_evr', address, amount, dryRun);
}

/**
 * Helper for generating a new receive address
 */
export async function generateReceiveAddress(
  backend: Backend | null,
  walletName: string = 'default',
  friendlyName?: string
): Promise<{success: boolean; address?: string; error?: string}> {
  return callBackend(backend, 'generate_receive_address', walletName, friendlyName);
}

/**
 * Helper for creating a new wallet
 */
export async function createNewWallet(
  backend: Backend | null,
  name: string = '',
  passphrase: string = ''
): Promise<{success: boolean; name?: string; mnemonic?: string; error?: string; message?: string}> {
  return callBackend(backend, 'create_new_wallet', name, passphrase);
}

/**
 * Helper for signing messages with a wallet address
 */
export async function signMessage(
  backend: Backend | null,
  address: string,
  message: string
): Promise<{success: boolean; signature?: string; error?: string}> {
  return callBackend<{success: boolean; signature?: string; error?: string}>(
    backend as any, 
    'sign_message' as any, 
    address, 
    message
  );
}

/**
 * Helper for verifying message signatures
 */
export async function verifyMessage(
  backend: Backend | null,
  address: string,
  signature: string,
  message: string
): Promise<{valid: boolean; error?: string}> {
  return callBackend<{valid: boolean; error?: string}>(
    backend as any, 
    'verify_message' as any, 
    address, 
    signature,
    message
  );
} 
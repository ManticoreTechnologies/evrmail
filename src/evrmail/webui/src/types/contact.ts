// Interface for contacts
export interface Contact {
  address: string;
  name: string;
  verified: boolean;
  pubkey?: string;
  status?: string;
}

// Interface for contact requests
export interface ContactRequest {
  address: string;
  name: string;
  pubkey?: string;
  status: string;
}

// Interface for outbox assets
export interface OutboxAsset {
  asset_name: string;
  balance: number;
  verified: boolean;
} 
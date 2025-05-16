// Interface for contacts
export interface Contact {
  address: string;
  name: string;
  verified: boolean;
  pubkey?: string;
}

// Interface for outbox assets
export interface OutboxAsset {
  name: string;
  balance: number;
  address: string;
} 
// Message interface for inbox messages
export interface Message {
  id: string;
  sender: string;
  timestamp: number;
  subject: string;
  content: string;
  read: boolean;
}

// Interface for outgoing messages
export interface OutgoingMessage {
  recipient: string;
  subject: string;
  content: string;
  outbox?: string;
  dry_run?: boolean;
}

// Interface for message sending result
export interface MessageSendResult {
  success: boolean;
  txid?: string;
  error?: string;
  message?: string;
} 
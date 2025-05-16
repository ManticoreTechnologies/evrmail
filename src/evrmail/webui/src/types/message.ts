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
} 
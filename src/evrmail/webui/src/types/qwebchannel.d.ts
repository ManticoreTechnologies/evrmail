declare namespace qt {
  const webChannelTransport: any;
}

declare class QWebChannel {
  constructor(transport: any, callback: (channel: QWebChannelInstance) => void);
}

interface QWebChannelInstance {
  objects: {
    backend: Backend;
    uicontrol: UIControl;
  };
}

interface UIControl {
  openTab: (tab: string) => void;
  set_browser_geometry: (x: number, y: number, w: number, h: number) => void;
  load_url: (url: string) => void;
  log: (message: string) => void;
}

interface Backend {
  // Navigation and UI functions
  openTab: (tab: string) => void;
  set_browser_geometry: (x: number, y: number, w: number, h: number) => void;
  load_url: (url: string) => void;
  log: (message: string) => void;
  
  // Core functionality (migrated from functions.py)
  get_log_entries: (level?: string, categories?: string[], filter_text?: string) => Promise<any[]>;
  get_settings: () => Promise<any>;
  save_settings: (settings: any) => Promise<{success: boolean, error?: string}>;
  get_wallet_balances: () => Promise<any>;
  get_wallet_addresses: () => Promise<any[]>;
  get_wallet_list: () => Promise<string[]>;
  get_utxos: () => Promise<any[]>;
  get_inbox_messages: () => Promise<any[]>;
  get_sent_messages: () => Promise<any[]>;
  send_message: (recipient: string, subject: string, message: string, outbox?: string, dry_run?: boolean) => Promise<any>;
  send_evr: (address: string, amount: number, dry_run?: boolean) => Promise<any>;
  generate_receive_address: (wallet_name?: string, friendly_name?: string) => Promise<any>;
  create_new_wallet: (name?: string, passphrase?: string) => Promise<any>;
  navigate_browser: (url: string) => Promise<any>;
  check_daemon_status: () => Promise<any>;
  preload_app_data: () => Promise<any>;
  get_messages: () => Promise<any[]>;
  mark_message_read: (message_id: string) => Promise<any>;
  delete_message: (message_id: string) => Promise<any>;
  get_message_stats: () => Promise<any>;
  get_network_status: () => Promise<any>;
  get_app_version: () => Promise<string>;
  get_wallet_info: () => Promise<any>;
  open_in_system_browser: (url: string) => Promise<any>;
  get_contacts: () => Promise<any>;
  get_contact_requests: () => Promise<any>;
  send_contact_request: (address: string, name?: string, address_mode?: string, from_address?: string, dry_run?: boolean) => Promise<any>;
  remove_contact: (address: string) => Promise<any>;
  accept_contact_request: (address: string) => Promise<any>;
  reject_contact_request: (address: string) => Promise<any>;
} 
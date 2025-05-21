import { useState, useEffect } from 'react'
import './App.css'
import Browser from './components/Browser'
import EvrMail from './components/EvrMail'

// Import QWebChannel types
declare global {
  interface Window {
    QWebChannel: typeof QWebChannel
    qt: {
      webChannelTransport: any
    }
    updateBrowserLoadingState: (isLoading: boolean, url: string, success: boolean) => void
  }
}

// Define development environment check
const isDevelopment = () => {
  // Check if we're in a development environment
  // In a proper setup, this would use process.env.NODE_ENV
  // but we'll use a simple check for now
  return !window.qt || !window.qt.webChannelTransport;
};

function App() {
  const [activeTab, setActiveTab] = useState<'mail' | 'browser'>('mail')
  const [backend, setBackend] = useState<Backend | null>(null)
  const [uicontrol, setUIControl] = useState<UIControl | null>(null)
  const [initialized, setInitialized] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Add the global browser loading state update function
  useEffect(() => {
    // Create a global function to receive loading state updates from Python
    window.updateBrowserLoadingState = (isLoading, url, success) => {
      console.log(`[Python→JS] Browser loading state: ${isLoading ? 'loading' : 'done'} for ${url} (success: ${success})`);
      
      // Dispatch a custom event that can be listened to by the Browser component
      const event = new CustomEvent('browserLoadingStateChanged', { 
        detail: { isLoading, url, success } 
      });
      window.dispatchEvent(event);
    };
    
    // Clean up the function when component unmounts
    return () => {
      window.updateBrowserLoadingState = () => {}; // Empty function
    };
  }, []);
  
  useEffect(() => {
    // Make sure we only try to initialize once
    let attemptsMade = 0;
    const maxAttempts = 3;
    
    const initializeQWebChannel = () => {
      attemptsMade++;
      console.log(`Attempting to initialize QWebChannel... (Attempt ${attemptsMade}/${maxAttempts})`);
      
      // Create mock backend for development if needed
      if (isDevelopment()) {
        console.log("Creating mock backend for development");
        setupDevEnvironment();
        return;
      }
      
      // First, check if the script needs to be loaded
      if (typeof window.QWebChannel === 'undefined') {
        console.warn("QWebChannel not defined, loading script...");
        
        // Try to load it dynamically
        const script = document.createElement('script');
        script.src = 'qrc:///qtwebchannel/qwebchannel.js';
        script.async = true;
        script.onerror = () => {
          console.error("Failed to load QWebChannel script");
          if (attemptsMade < maxAttempts) {
            setTimeout(initializeQWebChannel, 1000); // Retry after a delay
          } else {
            console.warn("Max attempts reached, falling back to development mode");
            setupDevEnvironment();
          }
        };
        script.onload = () => {
          console.log("QWebChannel script loaded, initializing channel");
          setupWebChannel();
        };
        document.head.appendChild(script);
        return;
      }
      
      // If the script is already loaded, initialize the channel
      setupWebChannel();
    };
    
    const setupWebChannel = () => {
      if (typeof window.qt === 'undefined' || !window.qt.webChannelTransport) {
        console.warn("Qt webChannelTransport not available, using development mode");
        setupDevEnvironment();
        return;
      }
      
      try {
        console.log("QWebChannel and transport available, initializing...");
        new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
          console.log("QWebChannel initialized", channel);
          
          // Check if objects are available
          if (!channel.objects) {
            console.error("No objects available in QWebChannel");
            setError("Failed to connect to backend: No objects available");
            setInitialized(true);
            return;
          }
          
          // Get the backend object if available
          if (channel.objects.backend) {
            console.log("Backend object available", channel.objects.backend);
            setBackend(channel.objects.backend);
          } else {
            console.warn("Backend object not available");
          }
          
          // Get the uicontrol object if available
          if (channel.objects.uicontrol) {
            console.log("UIControl object available", channel.objects.uicontrol);
            setUIControl(channel.objects.uicontrol);
          } else {
            console.warn("UIControl object not available");
          }
          
          setInitialized(true);
          console.log("QWebChannel initialization complete");
        });
      } catch (error) {
        console.error("Error initializing QWebChannel:", error);
        setError(`Failed to initialize QWebChannel: ${error instanceof Error ? error.message : 'Unknown error'}`);
        
        if (attemptsMade < maxAttempts) {
          setTimeout(initializeQWebChannel, 1000); // Retry after a delay
        } else {
          console.warn("Max attempts reached, falling back to development mode");
          setupDevEnvironment();
        }
      }
    };
    
    const setupDevEnvironment = () => {
      console.log("Setting up development environment");
      
      const mockBackend = {
        openTab: (tab: string) => console.log(`[MOCK] Opening tab: ${tab}`),
        log: (message: string) => console.log(`[MOCK] ${message}`),
        get_app_version: () => Promise.resolve("0.1.0-dev"),
        get_network_status: () => Promise.resolve({
          connected: true,
          network: "testnet",
          peers: 5
        }),
        get_messages: () => Promise.resolve([
          {
            id: "mock-1",
            sender: "EX1MockAddress123",
            timestamp: Date.now() / 1000,
            subject: "Welcome to EvrMail Dev Mode",
            content: "This is a mock message for development.",
            read: false
          }
        ])
      } as any;
      
      const mockUIControl = {
        openTab: (tab: string) => console.log(`[MOCK] Opening UI tab: ${tab}`),
        set_browser_geometry: (x: number, y: number, w: number, h: number) => 
          console.log(`[MOCK] Setting browser geometry: ${x}, ${y}, ${w}x${h}`),
        load_url: (url: string) => console.log(`[MOCK] Loading URL: ${url}`),
        log: (message: string) => console.log(`[MOCK] ${message}`)
      } as UIControl;
      
      setBackend(mockBackend);
      setUIControl(mockUIControl);
      setInitialized(true);
    };
    
    // Start initialization process
    initializeQWebChannel();
    
  }, []);

  const handleTabSwitch = (tab: 'mail' | 'browser') => {
    setActiveTab(tab);
    console.log(`Switching to tab: ${tab}`);
    
    try {
      // Try uicontrol first
      if (uicontrol && typeof uicontrol.openTab === 'function') {
        uicontrol.openTab(tab);
        return;
      }
      
      // Fall back to backend if available
      if (backend && typeof backend.openTab === 'function') {
        backend.openTab(tab);
        return;
      }
      
      console.warn("No available method to switch tabs");
    } catch (error) {
      console.error("Error switching tabs:", error);
    }
  };

  // If not initialized yet, show a loading screen
  if (!initialized) {
    return (
      <div className="loading-container">
        <div className="loading-message">
          <div className="loading-icon">📬</div>
          <h1>EvrMail</h1>
          <p>Loading application...</p>
        </div>
      </div>
    );
  }

  // If we have an initialization error, show that
  if (error) {
    return (
      <div className="loading-container">
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <h1>EvrMail - Error</h1>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="tabs">
        <div 
          className={`tab ${activeTab === 'mail' ? 'active' : ''}`} 
          onClick={() => handleTabSwitch('mail')}
        >
          📬 EvrMail
        </div>
        <div 
          className={`tab ${activeTab === 'browser' ? 'active' : ''}`}
          onClick={() => handleTabSwitch('browser')}
        >
          🌐 Browser
        </div>
      </div>

      {activeTab === 'mail' ? (
        <EvrMail 
          backend={backend}
          onSwitchToBrowser={() => handleTabSwitch('browser')}
        />
      ) : (
        <Browser backend={backend} uicontrol={uicontrol} />
      )}
    </div>
  )
}

export default App

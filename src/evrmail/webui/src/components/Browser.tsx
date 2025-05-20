import { useState, useRef, useEffect } from 'react';
import './EvrMail.css';
import { callBackend } from '../utils/bridge';

interface BrowserProps {
  backend: Backend | null;
  uicontrol: UIControl | null;
}

const Browser: React.FC<BrowserProps> = ({ backend, uicontrol }) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingUrl, setLoadingUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const browserFrameRef = useRef<HTMLDivElement>(null);

  const updateFramePosition = () => {
    if (!browserFrameRef.current) return;
    
    try {
      // Choose the appropriate control object
      const control = uicontrol || backend;
      if (!control) {
        console.warn('No browser geometry control available');
        return;
      }
      
      // Check if the function exists
      if (typeof control.set_browser_geometry !== 'function') {
        console.warn('set_browser_geometry function not available');
        return;
      }
      
      const rect = browserFrameRef.current.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      const x = Math.round(rect.left * dpr);
      const y = Math.round(rect.top * dpr);
      const w = Math.round(rect.width * dpr);
      const h = Math.round(rect.height * dpr);

      control.set_browser_geometry(x, y, w, h);
    } catch (error) {
      console.error('Error updating frame position:', error);
      setError('Failed to update browser position');
    }
  };

  useEffect(() => {
    // Clear any previous errors
    setError(null);
    
    try {
      // Choose the appropriate control object
      const control = uicontrol || backend;
      if (!control) {
        console.warn('No browser control available');
        setError('Browser control not available');
        return;
      }
      
      // Update frame position when component mounts (tab becomes active)
      setTimeout(updateFramePosition, 150);
      
      const handleResize = () => {
        setTimeout(updateFramePosition, 100);
      };
      
      window.addEventListener('resize', handleResize);
      
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    } catch (error) {
      console.error('Error in browser setup:', error);
      setError('Failed to initialize browser');
    }
  }, [backend, uicontrol]);

  // Create a function to listen for loading state events from Python
  useEffect(() => {
    // Define the event handler function
    const handleLoadingStateChange = (event: CustomEvent) => {
      const { isLoading, url, success } = event.detail;
      console.log(`Browser component received loading state: ${isLoading ? 'loading' : 'done'} for ${url}`);
      
      if (isLoading) {
        setLoading(true);
        setLoadingUrl(url);
      } else {
        setLoading(false);
        if (!success) {
          setError(`Failed to load: ${url}`);
        }
      }
    };
    
    // Add event listener for our custom browser loading state event
    window.addEventListener('browserLoadingStateChanged', handleLoadingStateChange as EventListener);
    
    // Clean up event listener when component unmounts
    return () => {
      window.removeEventListener('browserLoadingStateChanged', handleLoadingStateChange as EventListener);
    };
  }, []);

  // Create a function to listen for page load events
  const setupPageLoadListeners = () => {
    if (!uicontrol) return;

    // Attach a listener to browser load events
    const handleLoadStart = () => {
      setLoading(true);
    };

    const handleLoadEnd = (success: boolean) => {
      setLoading(false);
      if (!success) {
        setError(`Failed to load: ${loadingUrl}`);
      }
    };

    // TODO: If there's a way to listen to browser load events from Python
    // we would implement that here
  };

  // Call the setup function when the component mounts
  useEffect(() => {
    setupPageLoadListeners();
  }, [uicontrol]);

  // Handle URL navigation
  const handleGoClick = async () => {
    if (!url) return;
    
    // Clear any previous errors
    setError(null);
    setLoading(true);
    setLoadingUrl(url);
    
    try {
      // Choose the appropriate control object for UI interactions
      const control = uicontrol || backend;
      if (!control) {
        throw new Error('Browser navigation control not available');
      }
      
      // Check if the function exists
      if (typeof control.load_url !== 'function') {
        throw new Error('load_url function not available');
      }
      
      // First update the browser position
      updateFramePosition();
      
      // Then navigate to the URL
      control.load_url(url);
      
      // If we have the backend, also log the navigation 
      if (backend) {
        try {
          if (typeof backend.navigate_browser === 'function') {
            await callBackend(backend, 'navigate_browser', url);
          } else {
            console.warn('navigate_browser function not available');
          }
        } catch (e) {
          console.error('Error logging navigation:', e);
        }
      }
      
      // Set a timeout to automatically clear the loading state
      // in case we don't get a proper response from the backend
      setTimeout(() => {
        setLoading(false);
      }, 15000); // 15 seconds timeout
    } catch (error) {
      console.error('Error navigating to URL:', error);
      setError(`Failed to navigate: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setLoading(false);
    }
  };

  return (
    <div className="browser-container">
      <div className="url-bar">
        <input 
          type="text" 
          className="url-input" 
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleGoClick()}
        />
        <button 
          className="go-btn" 
          onClick={handleGoClick}
          disabled={loading}
        >
          {loading ? '...' : 'Go'}
        </button>
      </div>
      
      {error && (
        <div className="browser-error">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
      <div className="browser-frame" ref={browserFrameRef}>
        {loading && (
          <div className="browser-loading-overlay">
            <div className="browser-spinner"></div>
            <h3>Loading...</h3>
            <div className="loading-url">
              {loadingUrl}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Browser; 
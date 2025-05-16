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

  const handleGoClick = async () => {
    if (!url) return;
    
    // Clear any previous errors
    setError(null);
    setLoading(true);
    
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
    } catch (error) {
      console.error('Error navigating to URL:', error);
      setError(`Failed to navigate: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // const handleKeyPress = (e: React.KeyboardEvent) => {
  //   if (e.key === 'Enter') {
  //     handleGoClick();
  //   }
  // };

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
      
      <div className="browser-frame" ref={browserFrameRef}></div>
    </div>
  );
};

export default Browser; 
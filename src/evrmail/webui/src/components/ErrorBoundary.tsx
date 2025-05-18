// @ts-nocheck
import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
// @ts-ignore
interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          backgroundColor: '#fff0f0',
          border: '1px solid #ffcbcb',
          borderRadius: '4px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ color: '#d32f2f', margin: '0 0 10px 0' }}>Something went wrong</h2>
          <p style={{ color: '#333', margin: '0 0 15px 0' }}>
            The application encountered an error. Please try again or refresh the page.
          </p>
          {this.state.error && (
            <div style={{ 
              backgroundColor: '#f8f8f8', 
              padding: '10px', 
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '14px',
              color: '#d32f2f'
            }}>
              <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>Error:</p>
              <p style={{ margin: '0', wordBreak: 'break-word' }}>{this.state.error.toString()}</p>
            </div>
          )}
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              marginTop: '15px',
              padding: '8px 16px',
              backgroundColor: '#d32f2f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 
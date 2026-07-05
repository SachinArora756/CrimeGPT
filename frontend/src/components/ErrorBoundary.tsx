import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

function isChunkLoadError(error: Error): boolean {
  return (
    error.message.includes('Failed to fetch dynamically imported module') ||
    error.message.includes('Loading chunk') ||
    error.message.includes('Loading CSS chunk') ||
    error.name === 'ChunkLoadError'
  )
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error) {
    if (isChunkLoadError(error)) {
      const reloaded = sessionStorage.getItem('chunk_error_reload')
      if (!reloaded) {
        sessionStorage.setItem('chunk_error_reload', '1')
        window.location.reload()
        return
      }
      sessionStorage.removeItem('chunk_error_reload')
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  handleHardReload = () => {
    sessionStorage.removeItem('chunk_error_reload')
    sessionStorage.removeItem('chunk_reload')
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      const isChunk = this.state.error && isChunkLoadError(this.state.error)

      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 max-w-lg w-full text-center">
            <div className="text-red-400 text-4xl mb-4">{isChunk ? '🔄' : '⚠'}</div>
            <h1 className="text-xl font-semibold text-white mb-2">
              {isChunk ? 'Application Updated' : 'Something went wrong'}
            </h1>
            <p className="text-slate-400 mb-6 text-sm">
              {isChunk
                ? 'A new version is available. Please reload the page.'
                : (this.state.error?.message || 'An unexpected error occurred.')}
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleHardReload}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm transition-colors"
              >
                {isChunk ? 'Reload Page' : 'Try Again'}
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-md text-sm transition-colors"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

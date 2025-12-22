import React from 'react'
import { useAuth } from '../contexts/AuthContext'

const getModuleUrl = (key: string, fallback: string) => {
  const config = (window as any).APP_CONFIG;
  if (config && config[`MODULE_${key.toUpperCase()}_URL`]) {
    return config[`MODULE_${key.toUpperCase()}_URL`];
  }
  return (import.meta.env as any)[`VITE_MODULE_${key.toUpperCase()}_URL`] || fallback;
};

const modules = [
  { key: 'auth', name: 'Authentication', icon: '🔐', url: getModuleUrl('auth', 'http://localhost:3000') + '/login', color: '#7C3AED', desc: 'User & Access Management' },
  { key: 'ledger', name: 'Ledger', icon: '📒', url: getModuleUrl('ledger', 'http://localhost:3001'), color: '#2563EB', desc: 'Financial Accounting' },
  { key: 'inventory', name: 'Inventory', icon: '📦', url: getModuleUrl('inventory', 'http://localhost:3002'), color: '#059669', desc: 'Stock Management' },
  { key: 'pos', name: 'Point of Sale', icon: '🛒', url: getModuleUrl('pos', 'http://localhost:3003'), color: '#DC2626', desc: 'Sales & Checkout' },
]

const Modules: React.FC = () => {
  const { user, logout } = useAuth()
  const token = localStorage.getItem('auth_token') || ''
  
  const isTokenExpired = (jwt: string): boolean => {
    if (!jwt) return true
    try {
      const [, payload] = jwt.split('.')
      if (!payload) return true
      const decoded = JSON.parse(atob(payload))
      const expSec = decoded.exp
      if (!expSec) return true
      return expSec * 1000 <= Date.now()
    } catch {
      return true
    }
  }
  
  const appendToken = (url: string) => {
    try {
      const u = new URL(url)
      if (token && !isTokenExpired(token)) {
        u.searchParams.set('sso_token', token)
      }
      return u.toString()
    } catch {
      return url
    }
  }
  
  const handleModuleClick = (e: React.MouseEvent<HTMLAnchorElement>, url: string) => {
    if (!token || isTokenExpired(token)) {
      e.preventDefault()
      alert('Your session has expired. Please login again.')
      logout()
      return
    }
  }
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '32px 24px'
    }}>
      {/* Header */}
      <div style={{
        maxWidth: 1200,
        margin: '0 auto 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{
            fontSize: 32,
            fontWeight: 700,
            color: '#fff',
            margin: 0,
            marginBottom: 4,
            letterSpacing: '-0.5px'
          }}>MG ERP Dashboard</h1>
          <p style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.9)',
            margin: 0
          }}>Welcome back! Select a module to get started</p>
        </div>
        
        {/* User Profile Card */}
        {user && (
          <div style={{
            background: 'rgba(255,255,255,0.15)',
            backdropFilter: 'blur(10px)',
            borderRadius: 12,
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            border: '1px solid rgba(255,255,255,0.2)'
          }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 600,
              fontSize: 16
            }}>
              {user.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#fff', marginBottom: 2 }}>
                {user.full_name || user.username || 'User'}
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>
                {user.email}
              </div>
            </div>
            <button 
              onClick={() => { logout(); }} 
              style={{
                marginLeft: 8,
                padding: '8px 16px',
                border: 'none',
                background: 'rgba(255,255,255,0.2)',
                color: '#fff',
                cursor: 'pointer',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 500,
                transition: 'all 0.2s',
                backdropFilter: 'blur(10px)'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.3)'}
              onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
            >
              Logout
            </button>
          </div>
        )}
      </div>

      {/* Modules Grid */}
      <div style={{
        maxWidth: 1200,
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 24
      }}>
        {modules.map(m => (
          <a 
            key={m.key} 
            href={appendToken(m.url)} 
            onClick={(e) => handleModuleClick(e, m.url)}
            style={{
              textDecoration: 'none',
              display: 'block'
            }} 
            target="_blank" 
            rel="noreferrer"
          >
            <div 
              style={{
                background: '#fff',
                borderRadius: 16,
                padding: 32,
                textAlign: 'center',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.06)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: 'pointer',
                border: '1px solid rgba(0,0,0,0.05)',
                position: 'relative' as const,
                overflow: 'hidden'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)'
                e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.06)'
              }}
            >
              {/* Color accent bar */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 4,
                background: m.color
              }} />
              
              {/* Icon circle */}
              <div style={{
                width: 80,
                height: 80,
                margin: '0 auto 20px',
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${m.color}15, ${m.color}30)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 40
              }}>
                {m.icon}
              </div>
              
              {/* Module name */}
              <h3 style={{
                fontSize: 20,
                fontWeight: 600,
                color: '#1f2937',
                margin: '0 0 8px 0',
                letterSpacing: '-0.3px'
              }}>
                {m.name}
              </h3>
              
              {/* Description */}
              <p style={{
                fontSize: 14,
                color: '#6b7280',
                margin: 0,
                lineHeight: 1.5
              }}>
                {m.desc}
              </p>
              
              {/* Arrow indicator */}
              <div style={{
                marginTop: 20,
                display: 'inline-flex',
                alignItems: 'center',
                fontSize: 13,
                fontWeight: 500,
                color: m.color
              }}>
                Open Module
                <span style={{ marginLeft: 6, fontSize: 16 }}>→</span>
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

export default Modules

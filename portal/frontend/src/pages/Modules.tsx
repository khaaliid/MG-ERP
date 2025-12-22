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
  { key: 'auth', name: 'Authentication', icon: '🔐', url: getModuleUrl('auth', 'http://localhost:3000') + '/login' },
  { key: 'ledger', name: 'Ledger', icon: '📒', url: getModuleUrl('ledger', 'http://localhost:3001') },
  { key: 'inventory', name: 'Inventory', icon: '📦', url: getModuleUrl('inventory', 'http://localhost:3002') },
  { key: 'pos', name: 'POS', icon: '🛒', url: getModuleUrl('pos', 'http://localhost:3003') },
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
    <div style={{padding:24}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}}>
        <h1 style={{fontSize:24}}>Modules</h1>
        <div style={{display:'flex',alignItems:'center',gap:12}}>
          {user && <span style={{fontSize:14,color:'#555'}}>Signed in as {user.email}</span>}
          <button onClick={() => { logout(); }} style={{padding:'6px 12px',border:'1px solid #ccc',background:'#fff',cursor:'pointer',borderRadius:4}}>Logout</button>
        </div>
      </div>
      <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(160px, 1fr))', gap:16}}>
        {modules.map(m => (
          <a 
            key={m.key} 
            href={appendToken(m.url)} 
            onClick={(e) => handleModuleClick(e, m.url)}
            style={{textDecoration:'none'}} 
            target="_blank" 
            rel="noreferrer"
          >
            <div style={{border:'1px solid #ddd', borderRadius:8, padding:16, background:'#fff', textAlign:'center'}}>
              <div style={{fontSize:48}}>{m.icon}</div>
              <div style={{marginTop:8, color:'#333'}}>{m.name}</div>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

export default Modules

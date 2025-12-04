import React from 'react'
import { useAuth } from '../contexts/AuthContext'

const modules = [
  { key: 'auth', name: 'Authentication', icon: '🔐', url: import.meta.env.VITE_MODULE_AUTH_URL || 'http://localhost:3000' },
  { key: 'ledger', name: 'Ledger', icon: '📒', url: import.meta.env.VITE_MODULE_LEDGER_URL || 'http://localhost:3001' },
  { key: 'inventory', name: 'Inventory', icon: '📦', url: import.meta.env.VITE_MODULE_INVENTORY_URL || 'http://localhost:3002' },
  { key: 'pos', name: 'POS', icon: '🛒', url: import.meta.env.VITE_MODULE_POS_URL || 'http://localhost:3003' },
]

const Modules: React.FC = () => {
  const { user, logout } = useAuth()
  const token = localStorage.getItem('auth_token') || ''
  const appendToken = (url: string) => {
    try {
      const u = new URL(url)
      if (token) {
        u.searchParams.set('sso_token', token)
      }
      return u.toString()
    } catch {
      return url
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
          <a key={m.key} href={appendToken(m.url)} style={{textDecoration:'none'}} target="_blank" rel="noreferrer">
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

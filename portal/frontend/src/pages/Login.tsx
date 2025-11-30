import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

const Login: React.FC = () => {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const ok = await login(email, password)
    if (!ok) setError('Invalid credentials')
  }

  return (
    <div style={{display:'flex',justifyContent:'center',alignItems:'center',minHeight:'100vh'}}>
      <form onSubmit={handleSubmit} style={{width:320,padding:24,border:'1px solid #ddd',borderRadius:8,background:'#fff'}}>
        <h1 style={{marginBottom:16}}>MG-ERP Portal Login</h1>
        {error && <div style={{color:'red',marginBottom:12}}>{error}</div>}
        <div>
          <label>Email</label>
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} style={{width:'100%',marginTop:4,marginBottom:12}} required />
        </div>
        <div>
          <label>Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} style={{width:'100%',marginTop:4,marginBottom:12}} required />
        </div>
        <button type="submit" style={{width:'100%'}}>Login</button>
      </form>
    </div>
  )
}

export default Login

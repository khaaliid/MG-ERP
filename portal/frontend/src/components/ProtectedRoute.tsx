import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import Login from '../pages/Login'

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div style={{display:'flex',justifyContent:'center',alignItems:'center',minHeight:'100vh'}}>Loading...</div>
  if (!user) return <Login />
  return <>{children}</>
}

export default ProtectedRoute

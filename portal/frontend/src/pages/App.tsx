import React from 'react'
import ProtectedRoute from '../components/ProtectedRoute'
import { AuthProvider } from '../contexts/AuthContext'
import Modules from './Modules'

const App: React.FC = () => {
  return (
    <AuthProvider>
      <ProtectedRoute>
        <Modules />
      </ProtectedRoute>
    </AuthProvider>
  )
}

export default App

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Admin from './pages/Admin'
import Moderator from './pages/Moderator'
import Join from './pages/Join'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={<Admin />} />
        <Route path="/moderator" element={<Moderator />} />
        <Route path="/join" element={<Join />} />
        <Route path="/" element={<Navigate to="/join" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

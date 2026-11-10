import { Navigate, Route, Routes } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'
import DashboardPage from '../pages/DashboardPage'
import CheckerPage from '../pages/CheckerPage'
import ComparePage from '../pages/ComparePage'
import HistoryPage from '../pages/HistoryPage'
import ResultPage from '../pages/ResultPage'
import { ProtectedRoute } from '../components/common/ProtectedRoute'
import { AppLayout } from '../components/layout/AppLayout'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/checker" element={<CheckerPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/results/:id" element={<ResultPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

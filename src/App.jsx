import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import ToastContainer from './components/Toast';

// Auth pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';

// App pages
import Dashboard from './pages/Dashboard';
import ProjectList from './pages/projects/ProjectList';
import ProjectCreator from './pages/projects/ProjectCreator';
import RunMonitor from './pages/RunMonitor';
import ConsoleLogs from './pages/ConsoleLogs';
import SuccessScreen from './pages/SuccessScreen';
import FailureScreen from './pages/FailureScreen';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import DatabaseModels from './pages/DatabaseModels';
import NotFound from './pages/NotFound';
import AccessDenied from './pages/AccessDenied';

// Admin-only pages
import ManageUsers from './pages/admin/ManageUsers';

function ProtectedRoute({ children }) {
  const { isAuthenticated, isRestoring } = useAuth();
  if (isRestoring) return null; // avoid a login-page flash while a stored token is being validated
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

// Gates a route to specific roles. Must be used inside ProtectedRoute (or
// itself checks isAuthenticated) so it never renders admin-only content to
// a logged-out visitor.
function RoleRoute({ roles, children }) {
  const { isAuthenticated, isRestoring, user } = useAuth();
  if (isRestoring) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!roles.includes(user?.role)) return <Navigate to="/403" replace />;
  return children;
}

function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const pageTitles = {
    '/dashboard': 'Dashboard',
    '/projects': 'Projects',
    '/projects/new': 'New Project',
    '/run-monitor': 'Run Monitor',
    '/console': 'Console Logs',
    '/success': 'Reports',
    '/failure': 'Error Report',
    '/profile': 'Profile',
    '/settings': 'Settings',
    '/db-models': 'DB Models',
    '/admin/users': 'Manage Users',
  };

  return (
    <div className="app-layout">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <div className={`app-main ${sidebarCollapsed ? 'app-main--collapsed' : ''}`}>
        <Navbar
          onMenuClick={() => setMobileOpen(true)}
          title={pageTitles[location.pathname] || ''}
        />
        <div className="app-content">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route path="/projects/new" element={<ProjectCreator />} />
            <Route path="/run-monitor" element={<RunMonitor />} />
            <Route path="/console" element={<ConsoleLogs />} />
            <Route path="/success" element={<SuccessScreen />} />
            <Route path="/failure" element={<FailureScreen />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/db-models" element={<DatabaseModels />} />
            <Route path="/admin/users" element={<RoleRoute roles={['ADMIN']}><ManageUsers /></RoleRoute>} />
            <Route path="/403" element={<AccessDenied />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
            <ToastContainer />
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/*" element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      } />
    </Routes>
  );
}

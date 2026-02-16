import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

// Pages
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Tickets from "@/pages/Tickets";
import NewTicket from "@/pages/NewTicket";
import Inventory from "@/pages/Inventory";
import AIAssistant from "@/pages/AIAssistant";
import Users from "@/pages/Users";
import Vehicles from "@/pages/Vehicles";
import Alerts from "@/pages/Alerts";
import Settings from "@/pages/Settings";
import Suppliers from "@/pages/Suppliers";
import PurchaseOrders from "@/pages/PurchaseOrders";
import SalesOrders from "@/pages/SalesOrders";
import Invoices from "@/pages/Invoices";
import Accounting from "@/pages/Accounting";
import Customers from "@/pages/Customers";
import Expenses from "@/pages/Expenses";
import DataMigration from "@/pages/DataMigration";
import Attendance from "@/pages/Attendance";
import LeaveManagement from "@/pages/LeaveManagement";
import Payroll from "@/pages/Payroll";
import Employees from "@/pages/Employees";
import Layout from "@/components/Layout";
import AuthCallback from "@/components/AuthCallback";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/auth/me`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        setUser(null);
        localStorage.removeItem("token");
      }
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (userData, token) => {
    if (token) {
      localStorage.setItem("token", token);
    }
    setUser(userData);
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch (e) {
      console.error("Logout error:", e);
    }
    localStorage.removeItem("token");
    setUser(null);
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return { user, loading, login, logout, checkAuth };
};

// Protected Route Component
const ProtectedRoute = ({ children, user, loading }) => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user && !location.state?.user) {
      navigate("/login", { replace: true });
    }
  }, [user, loading, navigate, location.state]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-primary text-xl">Loading...</div>
      </div>
    );
  }

  const currentUser = user || location.state?.user;
  if (!currentUser) {
    return null;
  }

  return children;
};

function AppRouter() {
  const location = useLocation();
  const auth = useAuth();

  // Check URL fragment for session_id (Google OAuth callback)
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback onLogin={auth.login} />;
  }

  return (
    <Routes>
      <Route path="/login" element={
        auth.user ? <Navigate to="/dashboard" replace /> : <Login onLogin={auth.login} />
      } />
      <Route path="/dashboard" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Dashboard user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/tickets" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Tickets user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/tickets/new" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <NewTicket user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/inventory" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Inventory user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/ai-assistant" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <AIAssistant user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/vehicles" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Vehicles user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/users" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Users user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/alerts" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Alerts user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Settings user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* New ERP Modules */}
      <Route path="/suppliers" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Suppliers user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/purchases" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <PurchaseOrders user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/sales" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <SalesOrders user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/invoices" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Invoices user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/accounting" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Accounting user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/customers" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Customers user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/expenses" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Expenses user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/data-migration" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <DataMigration user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/attendance" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Attendance user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/leave" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <LeaveManagement user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/payroll" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Payroll user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;

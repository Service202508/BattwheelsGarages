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
import FailureIntelligence from "@/pages/FailureIntelligence";
import FaultTreeImport from "@/pages/FaultTreeImport";
import AMCManagement from "@/pages/AMCManagement";
import TechnicianProductivity from "@/pages/TechnicianProductivity";
import Quotes from "@/pages/Quotes";
import Layout from "@/components/Layout";
import AuthCallback from "@/components/AuthCallback";

// Customer Portal Pages
import CustomerLayout from "@/components/CustomerLayout";
import CustomerDashboard from "@/pages/customer/CustomerDashboard";
import CustomerVehicles from "@/pages/customer/CustomerVehicles";
import CustomerServiceHistory from "@/pages/customer/CustomerServiceHistory";
import CustomerInvoices from "@/pages/customer/CustomerInvoices";
import CustomerPayments from "@/pages/customer/CustomerPayments";
import CustomerAMC from "@/pages/customer/CustomerAMC";

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
const ProtectedRoute = ({ children, user, loading, allowedRoles = null }) => {
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

  // Role-based access check
  if (allowedRoles && !allowedRoles.includes(currentUser.role)) {
    // Redirect customer to customer portal, others to dashboard
    if (currentUser.role === "customer") {
      return <Navigate to="/customer" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Role-based redirect after login
const RoleBasedRedirect = ({ user }) => {
  if (user?.role === "customer") {
    return <Navigate to="/customer" replace />;
  }
  return <Navigate to="/dashboard" replace />;
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
        auth.user ? <RoleBasedRedirect user={auth.user} /> : <Login onLogin={auth.login} />
      } />
      <Route path="/dashboard" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Dashboard user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/tickets" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Tickets user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/tickets/new" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <NewTicket user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/inventory" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Inventory user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/ai-assistant" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <AIAssistant user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/vehicles" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Vehicles user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/users" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Users user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/alerts" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Alerts user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Settings user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* New ERP Modules */}
      <Route path="/suppliers" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Suppliers user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/purchases" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <PurchaseOrders user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/sales" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <SalesOrders user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/quotes" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Quotes user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/invoices" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Invoices user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/accounting" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Accounting user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/customers" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Customers user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/expenses" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Expenses user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/data-migration" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <DataMigration user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/attendance" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Attendance user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/leave" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <LeaveManagement user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/payroll" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Payroll user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/employees" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Employees user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/failure-intelligence" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <FailureIntelligence user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/fault-tree-import" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <FaultTreeImport user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/amc" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <AMCManagement user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/productivity" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <TechnicianProductivity user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      
      {/* Customer Portal Routes */}
      <Route path="/customer" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerDashboard user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      <Route path="/customer/vehicles" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerVehicles user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      <Route path="/customer/service-history" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerServiceHistory user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      <Route path="/customer/service-history/:ticketId" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerServiceHistory user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      <Route path="/customer/invoices" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerInvoices user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      <Route path="/customer/payments" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerPayments user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      <Route path="/customer/amc" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <CustomerLayout user={auth.user} onLogout={auth.logout}>
            <CustomerAMC user={auth.user} />
          </CustomerLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/" element={auth.user ? <RoleBasedRedirect user={auth.user} /> : <Navigate to="/login" replace />} />
      <Route path="*" element={auth.user ? <RoleBasedRedirect user={auth.user} /> : <Navigate to="/login" replace />} />
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

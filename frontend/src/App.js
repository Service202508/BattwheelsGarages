import { useEffect, useState, createContext, useContext } from "react";
import "@/App.css";
import "leaflet/dist/leaflet.css";
import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

// Pages
import Login from "@/pages/Login";
import SaaSLanding from "@/pages/SaaSLanding";
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
import Bills from "@/pages/Bills";
import CreditNotes from "@/pages/CreditNotes";
import Banking from "@/pages/Banking";
import Reports from "@/pages/Reports";
import GSTReports from "@/pages/GSTReports";
import VendorCredits from "@/pages/VendorCredits";
import ChartOfAccounts from "@/pages/ChartOfAccounts";
import JournalEntries from "@/pages/JournalEntries";
import RecurringTransactions from "@/pages/RecurringTransactions";
import Projects, { ProjectDetail } from "@/pages/Projects";
import Taxes from "@/pages/Taxes";
import DeliveryChallans from "@/pages/DeliveryChallans";
import Items from "@/pages/Items";
import ItemsEnhanced from "@/pages/ItemsEnhanced";
import ContactsEnhanced from "@/pages/ContactsEnhanced";
import EstimatesEnhanced from "@/pages/EstimatesEnhanced";
import SalesOrdersEnhanced from "@/pages/SalesOrdersEnhanced";
import InvoicesEnhanced from "@/pages/InvoicesEnhanced";
import PaymentsReceived from "@/pages/PaymentsReceived";
import InvoiceSettings from "@/pages/InvoiceSettings";
import CustomerPortal from "@/pages/CustomerPortal";
import ReportsAdvanced from "@/pages/ReportsAdvanced";
import BillsEnhanced from "@/pages/BillsEnhanced";
import InventoryEnhanced from "@/pages/InventoryEnhanced";
import CompositeItems from "@/pages/CompositeItems";
// CustomersEnhanced has been merged into ContactsEnhanced - redirect below
import PriceLists from "@/pages/PriceLists";
import InventoryAdjustments from "@/pages/InventoryAdjustments";
import SerialBatchTracking from "@/pages/SerialBatchTracking";
import RecurringExpenses from "@/pages/RecurringExpenses";
import RecurringBills from "@/pages/RecurringBills";
import FixedAssets from "@/pages/FixedAssets";
import CustomModules from "@/pages/CustomModules";
import ProjectTasks from "@/pages/ProjectTasks";
import OpeningBalances from "@/pages/OpeningBalances";
import ExchangeRates from "@/pages/ExchangeRates";
import ActivityLogs from "@/pages/ActivityLogs";
import ZohoSync from "@/pages/ZohoSync";
import OrganizationSettings from "@/pages/OrganizationSettings";
import AllSettings from "@/pages/AllSettings";
import FinanceDashboard from "@/pages/finance/FinanceDashboard";
import DataManagement from "@/pages/DataManagement";
import Home from "@/pages/Home";
import TimeTracking from "@/pages/TimeTracking";
import Documents from "@/pages/Documents";
import StockTransfers from "@/pages/StockTransfers";
import Accountant from "@/pages/Accountant";
import TrialBalance from "@/pages/TrialBalance";
import Layout from "@/components/Layout";
import AuthCallback from "@/components/AuthCallback";
import PublicQuoteView from "@/pages/PublicQuoteView";
import PublicTicketForm from "@/pages/PublicTicketForm";
import TrackTicket from "@/pages/TrackTicket";
import CustomerSurvey from "@/pages/CustomerSurvey";
import SubscriptionManagement from "@/pages/SubscriptionManagement";
import TeamManagement from "@/pages/TeamManagement";
import OrganizationSetupWizard from "@/pages/OrganizationSetupWizard";
import BrandingSettings from "@/pages/BrandingSettings";
import PlatformAdmin from "@/pages/PlatformAdmin";

// Customer Portal Pages
import CustomerLayout from "@/components/CustomerLayout";
import CustomerDashboard from "@/pages/customer/CustomerDashboard";
import CustomerVehicles from "@/pages/customer/CustomerVehicles";
import CustomerServiceHistory from "@/pages/customer/CustomerServiceHistory";
import CustomerInvoices from "@/pages/customer/CustomerInvoices";
import CustomerPayments from "@/pages/customer/CustomerPayments";
import CustomerAMC from "@/pages/customer/CustomerAMC";
import CommandPalette from "@/components/CommandPalette";
import UpgradeModal from "@/components/UpgradeModal";

// Technician Portal Pages
import TechnicianLayout from "@/components/TechnicianLayout";
import TechnicianDashboard from "@/pages/technician/TechnicianDashboard";
import TechnicianTickets from "@/pages/technician/TechnicianTickets";
import TechnicianAttendance from "@/pages/technician/TechnicianAttendance";
import TechnicianLeave from "@/pages/technician/TechnicianLeave";
import TechnicianPayroll from "@/pages/technician/TechnicianPayroll";
import TechnicianProductivityPage from "@/pages/technician/TechnicianProductivity";
import TechnicianAIAssistant from "@/pages/technician/TechnicianAIAssistant";

// Business Customer Portal Pages
import BusinessLayout from "@/components/BusinessLayout";
import BusinessDashboard from "@/pages/business/BusinessDashboard";
import BusinessFleet from "@/pages/business/BusinessFleet";
import BusinessTickets from "@/pages/business/BusinessTickets";
import BusinessInvoices from "@/pages/business/BusinessInvoices";
import BusinessAMC from "@/pages/business/BusinessAMC";
import BusinessReports from "@/pages/business/BusinessReports";

// Admin Settings
import PermissionsManager from "@/pages/settings/PermissionsManager";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Re-export API utilities for convenience
export { getAuthHeaders, getOrganizationId, setOrganizationId, apiFetch, apiGet, apiPost, apiPut, apiPatch, apiDelete } from '@/utils/api';

// Organization Context for global access
const OrganizationContext = createContext(null);
export const useOrganization = () => useContext(OrganizationContext);

// Auth Context
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [orgReady, setOrgReady] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [needsOrgSelection, setNeedsOrgSelection] = useState(false);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      
      const response = await fetch(`${API}/auth/me`, {
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        // Initialize organization after successful auth check
        await initializeOrgContext();
      } else {
        setUser(null);
        localStorage.removeItem("token");
        localStorage.removeItem("organization_id");
        localStorage.removeItem("organization");
      }
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };
  
  const initializeOrgContext = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setOrgReady(true);
        return;
      }
      
      // Check if org is already set in localStorage
      const existingOrgId = localStorage.getItem("organization_id");
      const existingOrg = localStorage.getItem("organization");
      
      if (existingOrgId && existingOrg) {
        try {
          setCurrentOrg(JSON.parse(existingOrg));
          setOrgReady(true);
          return;
        } catch (e) {
          // Invalid JSON, fetch fresh
        }
      }
      
      // Fetch user's organizations
      const response = await fetch(`${API}/organizations/my-organizations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        const orgs = data.organizations || [];
        setOrganizations(orgs);
        
        if (orgs.length === 0) {
          // No organizations - user needs to create or join one
          setNeedsOrgSelection(true);
        } else if (orgs.length === 1) {
          // Single organization - auto-select
          await selectOrganization(orgs[0]);
        } else {
          // Multiple organizations - user needs to pick
          // Check if default org exists
          if (existingOrgId) {
            const org = orgs.find(o => o.organization_id === existingOrgId);
            if (org) {
              await selectOrganization(org);
              return;
            }
          }
          // Need selection
          setNeedsOrgSelection(true);
        }
      }
    } catch (e) {
      console.error("Failed to init org:", e);
    } finally {
      setOrgReady(true);
    }
  };

  const selectOrganization = async (org) => {
    localStorage.setItem("organization_id", org.organization_id);
    localStorage.setItem("organization", JSON.stringify(org));
    setCurrentOrg(org);
    setNeedsOrgSelection(false);
    setOrgReady(true);
  };

  const login = async (userData, token, orgs = null) => {
    if (token) {
      localStorage.setItem("token", token);
    }
    setUser(userData);
    
    // If organizations are provided from login response
    if (orgs && orgs.length > 0) {
      setOrganizations(orgs);
      if (orgs.length === 1) {
        await selectOrganization(orgs[0]);
      } else {
        setNeedsOrgSelection(true);
        setOrgReady(true);
      }
    } else {
      // Initialize organization context after login
      setOrgReady(false);
      await initializeOrgContext();
    }
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
    localStorage.removeItem("organization_id");
    localStorage.removeItem("organization");
    setUser(null);
    setCurrentOrg(null);
    setOrganizations([]);
    setNeedsOrgSelection(false);
    setOrgReady(false);
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return { 
    user, 
    loading, 
    login, 
    logout, 
    checkAuth, 
    orgReady,
    organizations,
    currentOrg,
    needsOrgSelection,
    selectOrganization
  };
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
    // Redirect based on role
    if (currentUser.role === "customer") {
      return <Navigate to="/customer" replace />;
    }
    if (currentUser.role === "technician") {
      return <Navigate to="/technician" replace />;
    }
    if (currentUser.role === "business_customer") {
      return <Navigate to="/business" replace />;
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
  if (user?.role === "technician") {
    return <Navigate to="/technician" replace />;
  }
  if (user?.role === "business_customer") {
    return <Navigate to="/business" replace />;
  }
  return <Navigate to="/dashboard" replace />;
};

// Organization Selection Page for multi-org users
const OrganizationSelection = ({ auth }) => {
  const navigate = useNavigate();
  
  const handleSelectOrg = async (org) => {
    await auth.selectOrganization(org);
    // Redirect based on role after org selection
    if (auth.user?.role === "customer") {
      navigate("/customer", { replace: true });
    } else if (auth.user?.role === "technician") {
      navigate("/technician", { replace: true });
    } else if (auth.user?.role === "business_customer") {
      navigate("/business", { replace: true });
    } else {
      navigate("/dashboard", { replace: true });
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/30">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Select Organization</h1>
          <p className="text-slate-400">Choose which organization you want to access</p>
        </div>
        
        <div className="space-y-3" data-testid="org-selection-list">
          {auth.organizations.map((org) => (
            <button
              key={org.organization_id}
              onClick={() => handleSelectOrg(org)}
              className="w-full p-4 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 hover:border-emerald-500/50 rounded-xl flex items-center gap-4 transition group"
              data-testid={`org-select-${org.organization_id}`}
            >
              <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-500/30 transition">
                {org.logo_url ? (
                  <img src={org.logo_url} alt="" className="w-8 h-8 rounded" />
                ) : (
                  <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                )}
              </div>
              <div className="flex-1 text-left">
                <p className="font-semibold text-white group-hover:text-emerald-400 transition">{org.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 capitalize">{org.role}</span>
                  <span className="text-xs text-slate-500 capitalize">{org.plan_type || 'Free'}</span>
                </div>
              </div>
              <svg className="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}
        </div>
        
        <div className="mt-6 pt-6 border-t border-slate-700">
          <a
            href="/"
            className="flex items-center justify-center gap-2 w-full p-3 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded-xl transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create New Organization
          </a>
        </div>
        
        <button
          onClick={auth.logout}
          className="mt-4 w-full p-3 text-slate-400 hover:text-white hover:bg-slate-800/50 rounded-xl transition text-sm"
        >
          Sign out and use a different account
        </button>
      </div>
    </div>
  );
};

function AppRouter() {
  const location = useLocation();
  const auth = useAuth();

  // Check URL fragment for session_id (Google OAuth callback)
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback onLogin={auth.login} />;
  }
  
  // Show loading state
  if (auth.loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-primary text-xl">Loading...</div>
      </div>
    );
  }
  
  // If user is logged in but needs to select an organization
  if (auth.user && auth.needsOrgSelection && auth.organizations.length > 1) {
    return <OrganizationSelection auth={auth} />;
  }

  return (
    <OrganizationContext.Provider value={auth.currentOrg}>
      <Routes>
        {/* SaaS Landing Page - Public, shown to non-authenticated users */}
        <Route path="/" element={
          auth.user ? <RoleBasedRedirect user={auth.user} /> : <SaaSLanding />
        } />
        
        {/* Public Quote View - No Auth Required */}
        <Route path="/quote/:shareToken" element={<PublicQuoteView />} />
        
        {/* Public Ticket Submission Form - No Auth Required */}
        <Route path="/submit-ticket" element={<PublicTicketForm />} />
        
        {/* Public Ticket Tracking - No Auth Required */}
        <Route path="/track-ticket" element={<TrackTicket />} />

        <Route path="/login" element={
          auth.user ? <RoleBasedRedirect user={auth.user} /> : <Login onLogin={auth.login} />
        } />
      
      {/* Zoho-style Financial Home Dashboard */}
      <Route path="/home" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Home user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      
      {/* Time Tracking */}
      <Route path="/time-tracking" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager", "technician"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <TimeTracking user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      
      {/* Documents */}
      <Route path="/documents" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Documents user={auth.user} />
          </Layout>
        </ProtectedRoute>
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
      <Route path="/finance" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <FinanceDashboard user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/bills" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Bills user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/credit-notes" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <CreditNotes user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/banking" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Banking user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/accountant" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Accountant user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/stock-transfers" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <StockTransfers user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/reports" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Reports user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/gst-reports" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <GSTReports user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/vendor-credits" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <VendorCredits user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/chart-of-accounts" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ChartOfAccounts user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/journal-entries" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <JournalEntries user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/trial-balance" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <TrialBalance user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/recurring-transactions" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <RecurringTransactions user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/projects" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Projects user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/projects/:projectId" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ProjectDetail user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/taxes" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <Taxes user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/delivery-challans" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <DeliveryChallans user={auth.user} />
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
      <Route path="/items" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ItemsEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/inventory-management" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ItemsEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/price-lists" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <PriceLists user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/inventory-adjustments" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <InventoryAdjustments user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/serial-batch-tracking" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <SerialBatchTracking user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/recurring-expenses" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <RecurringExpenses user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/project-tasks" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ProjectTasks user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/opening-balances" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <OpeningBalances user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/exchange-rates" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ExchangeRates user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/activity-logs" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ActivityLogs user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/zoho-sync" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ZohoSync user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/subscription" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <SubscriptionManagement user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/team" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <TeamManagement user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/setup" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <OrganizationSetupWizard user={auth.user} />
        </ProtectedRoute>
      } />
      <Route path="/branding" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <BrandingSettings user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/organization-settings" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <OrganizationSettings user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/all-settings" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <AllSettings user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/data-management" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <DataManagement user={auth.user} />
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
      <Route path="/contacts" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ContactsEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/estimates" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <EstimatesEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/sales-orders" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <SalesOrdersEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/invoices-enhanced" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "technician", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <InvoicesEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/payments-received" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <PaymentsReceived user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/invoice-settings" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <InvoiceSettings user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Redirect old customers-enhanced route to unified contacts page */}
      <Route path="/customers-enhanced" element={<Navigate to="/contacts" replace />} />
      {/* Customer Portal - Public access with token authentication */}
      <Route path="/customer-portal" element={<CustomerPortal />} />
      {/* Advanced Reports with Charts */}
      <Route path="/reports-advanced" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <ReportsAdvanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Bills Enhanced Module */}
      <Route path="/bills-enhanced" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <BillsEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Composite Items (Kits/Assemblies/Bundles) */}
      <Route path="/composite-items" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <CompositeItems user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Inventory Enhanced Module (Variants, Bundles, Shipments, Returns) */}
      <Route path="/inventory-enhanced" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <InventoryEnhanced user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Recurring Bills */}
      <Route path="/recurring-bills" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <RecurringBills user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Fixed Assets */}
      <Route path="/fixed-assets" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <FixedAssets user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      {/* Custom Modules */}
      <Route path="/custom-modules" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin", "manager"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <CustomModules user={auth.user} />
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
      
      {/* Technician Portal Routes */}
      <Route path="/technician" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianDashboard user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/tickets" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianTickets user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/tickets/:ticketId" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianTickets user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/attendance" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianAttendance user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/leave" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianLeave user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/payroll" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianPayroll user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/productivity" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianProductivityPage user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      <Route path="/technician/ai-assist" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["technician"]}>
          <TechnicianLayout user={auth.user} onLogout={auth.logout}>
            <TechnicianAIAssistant user={auth.user} />
          </TechnicianLayout>
        </ProtectedRoute>
      } />
      
      {/* Business Customer Portal Routes */}
      <Route path="/business" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessDashboard user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/fleet" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessFleet user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/tickets" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessTickets user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/tickets/:ticketId" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessTickets user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/tickets/new" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessTickets user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/invoices" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessInvoices user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/payments" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessInvoices user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/amc" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessAMC user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      <Route path="/business/reports" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["business_customer", "customer"]}>
          <BusinessLayout user={auth.user} onLogout={auth.logout}>
            <BusinessReports user={auth.user} />
          </BusinessLayout>
        </ProtectedRoute>
      } />
      
      {/* Admin Settings - Permissions */}
      <Route path="/settings/permissions" element={
        <ProtectedRoute user={auth.user} loading={auth.loading} allowedRoles={["admin"]}>
          <Layout user={auth.user} onLogout={auth.logout}>
            <PermissionsManager user={auth.user} />
          </Layout>
        </ProtectedRoute>
      } />
      
      {/* Platform Admin — operator-only, bypasses org context */}
      <Route path="/platform-admin" element={
        <ProtectedRoute user={auth.user} loading={auth.loading}>
          <PlatformAdmin user={auth.user} />
        </ProtectedRoute>
      } />
      
      {/* Catch-all: redirect to SaaS landing or dashboard */}
      <Route path="*" element={auth.user ? <RoleBasedRedirect user={auth.user} /> : <Navigate to="/" replace />} />
    </Routes>
    </OrganizationContext.Provider>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
        <CommandPalette />
        <UpgradeModal />
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;

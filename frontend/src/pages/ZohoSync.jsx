import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { 
  RefreshCw, Loader2, CheckCircle2, XCircle, Clock, 
  Users, Package, FileText, Receipt, CreditCard, Wallet,
  CloudDownload, History, Zap, AlertCircle, Building2,
  Power, Trash2, AlertTriangle
} from "lucide-react";
import { API } from "@/App";

// Module configurations for sync
const SYNC_MODULES = [
  { id: "contacts", name: "Contacts", icon: Users, description: "Customers & Vendors", endpoint: "/zoho-sync/import/contacts" },
  { id: "items", name: "Items", icon: Package, description: "Products & Services", endpoint: "/zoho-sync/import/items" },
  { id: "invoices", name: "Invoices", icon: FileText, description: "Sales Invoices", endpoint: "/zoho-sync/import/invoices" },
  { id: "bills", name: "Bills", icon: Receipt, description: "Vendor Bills", endpoint: "/zoho-sync/import/bills" },
  { id: "estimates", name: "Estimates", icon: FileText, description: "Quotes & Estimates", endpoint: "/zoho-sync/import/estimates" },
  { id: "expenses", name: "Expenses", icon: CreditCard, description: "Business Expenses", endpoint: "/zoho-sync/import/expenses" },
  { id: "payments", name: "Payments", icon: Wallet, description: "Customer & Vendor Payments", endpoint: "/zoho-sync/import/payments" },
  { id: "purchase-orders", name: "Purchase Orders", icon: Receipt, description: "POs from Vendors", endpoint: "/zoho-sync/import/purchase-orders" },
  { id: "sales-orders", name: "Sales Orders", icon: FileText, description: "SOs to Customers", endpoint: "/zoho-sync/import/sales-orders" },
  { id: "credit-notes", name: "Credit Notes", icon: CreditCard, description: "Customer Credits", endpoint: "/zoho-sync/import/credit-notes" },
  { id: "bank-accounts", name: "Bank Accounts", icon: Building2, description: "Banking Info", endpoint: "/zoho-sync/import/bank-accounts" },
];

export default function ZohoSync() {
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [syncHistory, setSyncHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [currentSync, setCurrentSync] = useState(null);
  const [syncingModule, setSyncingModule] = useState(null);
  const [fullSyncInProgress, setFullSyncInProgress] = useState(false);
  const [moduleResults, setModuleResults] = useState({});
  
  // Disconnect & Purge states
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [purgeStats, setPurgeStats] = useState(null);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    testConnection();
    fetchSyncHistory();
  }, []);

  // Poll for sync status when full sync is in progress
  useEffect(() => {
    if (currentSync && currentSync.status === "started") {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`${API}/zoho-sync/import/status/${currentSync.sync_id}`, { headers });
          const data = await res.json();
          if (data.sync) {
            setCurrentSync(data.sync);
            if (data.sync.status === "completed" || data.sync.status === "failed") {
              setFullSyncInProgress(false);
              fetchSyncHistory();
              if (data.sync.status === "completed") {
                toast.success("Full sync completed successfully!");
              } else {
                toast.error("Sync failed: " + (data.sync.error || "Unknown error"));
              }
            }
          }
        } catch (error) {
          console.error("Error polling sync status:", error);
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [currentSync]);

  const testConnection = async () => {
    setTestingConnection(true);
    try {
      const res = await fetch(`${API}/zoho-sync/test-connection`, { headers });
      const data = await res.json();
      setConnectionStatus(data);
      if (data.status === "connected") {
        toast.success("Connected to Zoho Books");
      }
    } catch (error) {
      setConnectionStatus({ status: "error", message: error.message });
      toast.error("Failed to connect to Zoho Books");
    } finally {
      setTestingConnection(false);
    }
  };

  const fetchSyncHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API}/zoho-sync/import/history?limit=10`, { headers });
      const data = await res.json();
      setSyncHistory(data.sync_logs || []);
    } catch (error) {
      console.error("Error fetching sync history:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const syncModule = async (module) => {
    setSyncingModule(module.id);
    try {
      const res = await fetch(`${API}${module.endpoint}`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        setModuleResults(prev => ({ ...prev, [module.id]: { status: "success", message: data.message } }));
      } else {
        toast.error(data.message || "Sync failed");
        setModuleResults(prev => ({ ...prev, [module.id]: { status: "error", message: data.message } }));
      }
    } catch (error) {
      toast.error(`Failed to sync ${module.name}`);
      setModuleResults(prev => ({ ...prev, [module.id]: { status: "error", message: error.message } }));
    } finally {
      setSyncingModule(null);
    }
  };

  const startFullSync = async () => {
    if (!confirm("This will sync ALL data from Zoho Books. This may take several minutes. Continue?")) {
      return;
    }

    setFullSyncInProgress(true);
    try {
      const res = await fetch(`${API}/zoho-sync/import/all`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        setCurrentSync({ sync_id: data.sync_id, status: "started" });
        toast.info("Full sync started. This may take several minutes...");
      } else {
        toast.error("Failed to start sync");
        setFullSyncInProgress(false);
      }
    } catch (error) {
      toast.error("Failed to start full sync");
      setFullSyncInProgress(false);
    }
  };

  const handleDisconnectAndPurge = async () => {
    setDisconnecting(true);
    try {
      const res = await fetch(`${API}/zoho-sync/disconnect-and-purge`, {
        method: "POST",
        headers,
        body: JSON.stringify({ confirm: true })
      });
      const data = await res.json();
      
      if (data.code === 0) {
        setPurgeStats(data.purge_stats);
        toast.success("Zoho Books disconnected and data purged successfully!");
        setConnectionStatus({ status: "disconnected", message: "Zoho Books integration disabled" });
        fetchSyncHistory();
      } else {
        toast.error(data.message || "Failed to disconnect");
      }
    } catch (error) {
      toast.error("Error disconnecting from Zoho Books");
    } finally {
      setDisconnecting(false);
      setShowDisconnectDialog(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "-";
    return new Date(timestamp).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const styles = {
      started: { class: "bg-blue-100 text-blue-800", icon: Loader2 },
      completed: { class: "bg-green-100 text-green-800", icon: CheckCircle2 },
      failed: { class: "bg-red-100 text-red-800", icon: XCircle }
    };
    const config = styles[status] || { class: "bg-[rgba(255,255,255,0.05)]", icon: Clock };
    const Icon = config.icon;
    return (
      <Badge className={`${config.class} flex items-center gap-1`}>
        <Icon className={`h-3 w-3 ${status === 'started' ? 'animate-spin' : ''}`} />
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-6" data-testid="zoho-sync-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Zoho Books Sync</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Sync data from your Zoho Books account</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={testConnection} disabled={testingConnection} data-testid="test-connection-btn">
            {testingConnection ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Zap className="h-4 w-4 mr-2" />}
            Test Connection
          </Button>
          <Button 
            onClick={startFullSync} 
            disabled={fullSyncInProgress || connectionStatus?.status !== "connected"}
            className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold"
            data-testid="full-sync-btn"
          >
            {fullSyncInProgress ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <CloudDownload className="h-4 w-4 mr-2" />
                Full Sync
              </>
            )}
          </Button>
          {connectionStatus?.status === "connected" && (
            <Button 
              variant="destructive"
              onClick={() => setShowDisconnectDialog(true)}
              disabled={fullSyncInProgress}
              data-testid="disconnect-zoho-btn"
            >
              <Power className="h-4 w-4 mr-2" />
              Turn Off Sync
            </Button>
          )}
        </div>
      </div>

      {/* Connection Status */}
      {connectionStatus && (
        <Alert className={connectionStatus.status === "connected" ? "border-green-500 bg-[rgba(34,197,94,0.08)]" : "border-red-500 bg-[rgba(255,59,47,0.08)]"}>
          {connectionStatus.status === "connected" ? (
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-600" />
          )}
          <AlertTitle className={connectionStatus.status === "connected" ? "text-green-800" : "text-red-800"}>
            {connectionStatus.status === "connected" ? "Connected to Zoho Books" : "Connection Failed"}
          </AlertTitle>
          <AlertDescription className={connectionStatus.status === "connected" ? "text-green-700" : "text-red-700"}>
            {connectionStatus.status === "connected" 
              ? `Organization ID: ${connectionStatus.organization_id}`
              : connectionStatus.message || "Unable to connect to Zoho Books API"
            }
          </AlertDescription>
        </Alert>
      )}

      {/* Current Sync Progress */}
      {currentSync && currentSync.status === "started" && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-[#3B9EFF]" />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900">Full Sync in Progress</h3>
                <p className="text-sm text-[#3B9EFF]">Sync ID: {currentSync.sync_id}</p>
                <Progress value={50} className="h-2 mt-2" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Module Cards */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Sync Individual Modules</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {SYNC_MODULES.map((module) => {
            const Icon = module.icon;
            const result = moduleResults[module.id];
            const isSyncing = syncingModule === module.id;
            
            return (
              <Card 
                key={module.id} 
                className={`hover:border-[rgba(200,255,0,0.2)] transition-colors ${
                  result?.status === "success" ? "border-green-200 bg-[rgba(34,197,94,0.08)]" :
                  result?.status === "error" ? "border-red-200 bg-[rgba(255,59,47,0.08)]" : ""
                }`}
              >
                <CardContent className="py-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2 rounded-lg ${
                      result?.status === "success" ? "bg-green-100" :
                      result?.status === "error" ? "bg-red-100" : "bg-[rgba(255,255,255,0.05)]"
                    }`}>
                      <Icon className={`h-5 w-5 ${
                        result?.status === "success" ? "text-green-600" :
                        result?.status === "error" ? "text-red-600" : "text-[rgba(244,246,240,0.35)]"
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate">{module.name}</h3>
                      <p className="text-xs text-[rgba(244,246,240,0.45)] truncate">{module.description}</p>
                    </div>
                  </div>
                  
                  {result && (
                    <p className={`text-xs mb-2 truncate ${
                      result.status === "success" ? "text-green-600" : "text-red-600"
                    }`}>
                      {result.message}
                    </p>
                  )}
                  
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="w-full"
                    onClick={() => syncModule(module)}
                    disabled={isSyncing || connectionStatus?.status !== "connected" || fullSyncInProgress}
                    data-testid={`sync-${module.id}-btn`}
                  >
                    {isSyncing ? (
                      <>
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Syncing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Sync
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Sync History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <History className="h-5 w-5" />
                Sync History
              </CardTitle>
              <CardDescription>Recent synchronization activities</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={fetchSyncHistory}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-[rgba(244,246,240,0.45)]" />
            </div>
          ) : syncHistory.length === 0 ? (
            <div className="text-center py-8 text-[rgba(244,246,240,0.45)]">
              <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No sync history yet</p>
              <p className="text-sm">Run a sync to see activity here</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#111820]">
                  <TableHead>Sync ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Completed</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {syncHistory.map((log) => (
                  <TableRow key={log.sync_id}>
                    <TableCell className="font-mono text-xs">{log.sync_id}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{log.type || "full_import"}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(log.status)}</TableCell>
                    <TableCell className="text-sm text-[rgba(244,246,240,0.35)]">{formatTimestamp(log.started_at)}</TableCell>
                    <TableCell className="text-sm text-[rgba(244,246,240,0.35)]">{formatTimestamp(log.completed_at)}</TableCell>
                    <TableCell>
                      {log.results && (
                        <span className="text-xs text-[rgba(244,246,240,0.45)]">
                          {Object.keys(log.results).length} modules synced
                        </span>
                      )}
                      {log.error && (
                        <span className="text-xs text-red-500">{log.error}</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Disconnect Confirmation Dialog */}
      <Dialog open={showDisconnectDialog} onOpenChange={setShowDisconnectDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Disconnect Zoho Books & Purge Data
            </DialogTitle>
            <DialogDescription>
              This action cannot be undone. Please read carefully:
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Warning: Destructive Action</AlertTitle>
              <AlertDescription>
                This will permanently delete ALL data synced from Zoho Books including:
              </AlertDescription>
            </Alert>
            
            <div className="bg-[rgba(255,59,47,0.08)] border border-red-200 rounded-lg p-4 text-sm">
              <ul className="space-y-1 text-red-800">
                <li className="flex items-center gap-2"><Trash2 className="h-3 w-3" /> All contacts (customers & vendors)</li>
                <li className="flex items-center gap-2"><Trash2 className="h-3 w-3" /> All items (products & services)</li>
                <li className="flex items-center gap-2"><Trash2 className="h-3 w-3" /> All invoices & estimates</li>
                <li className="flex items-center gap-2"><Trash2 className="h-3 w-3" /> All bills & purchase orders</li>
                <li className="flex items-center gap-2"><Trash2 className="h-3 w-3" /> All payments & expenses</li>
                <li className="flex items-center gap-2"><Trash2 className="h-3 w-3" /> All sync history & logs</li>
              </ul>
            </div>
            
            <p className="text-sm text-[rgba(244,246,240,0.35)]">
              After this, you can start fresh with manual data entry or reconnect to Zoho Books later.
            </p>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDisconnectDialog(false)} disabled={disconnecting}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDisconnectAndPurge}
              disabled={disconnecting}
              data-testid="confirm-disconnect-btn"
            >
              {disconnecting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Disconnecting...
                </>
              ) : (
                <>
                  <Power className="h-4 w-4 mr-2" />
                  Disconnect & Purge Data
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Purge Results */}
      {purgeStats && (
        <Dialog open={!!purgeStats} onOpenChange={() => setPurgeStats(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="h-5 w-5" />
                Data Purge Complete
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-2 py-4">
              <p className="text-sm text-[rgba(244,246,240,0.35)]">The following data was removed:</p>
              <div className="bg-[#111820] rounded-lg p-4 text-sm">
                {Object.entries(purgeStats).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-1 border-b border-gray-200 last:border-0">
                    <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-[rgba(244,246,240,0.35)]">{value} records</span>
                  </div>
                ))}
              </div>
            </div>
            <DialogFooter>
              <Button onClick={() => setPurgeStats(null)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

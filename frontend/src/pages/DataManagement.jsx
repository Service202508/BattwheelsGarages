import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import {
  Database, RefreshCw, Trash2, CloudDownload, CheckCircle2, XCircle,
  AlertTriangle, Clock, Play, Pause, RotateCcw, Eye, FileText,
  TrendingUp, TrendingDown, Activity, Zap, Server, Link2
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

export default function DataManagement() {
  const [activeTab, setActiveTab] = useState("overview");
  const [dataCounts, setDataCounts] = useState({});
  const [syncStatus, setSyncStatus] = useState({});
  const [sanitizationReport, setSanitizationReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [sanitizing, setSanitizing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  const fetchDataCounts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/data-management/counts`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setDataCounts(data.counts || {});
      }
    } catch (error) {
      console.error("Failed to fetch data counts:", error);
    }
  }, []);

  const fetchSyncStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/data-management/sync/status`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(data.status || {});
      }
    } catch (error) {
      console.error("Failed to fetch sync status:", error);
    }
  }, []);

  const testConnection = useCallback(async () => {
    try {
      const res = await fetch(`${API}/data-management/sync/test-connection`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setConnectionStatus(data.connection);
      }
    } catch (error) {
      setConnectionStatus({ status: "error", error: error.message });
    }
  }, []);

  useEffect(() => {
    Promise.all([fetchDataCounts(), fetchSyncStatus(), testConnection()])
      .finally(() => setLoading(false));
  }, [fetchDataCounts, fetchSyncStatus, testConnection]);

  const runSanitizationAudit = async () => {
    setSanitizing(true);
    try {
      const res = await fetch(`${API}/data-management/sanitize`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ mode: "audit" })
      });
      if (res.ok) {
        const data = await res.json();
        setSanitizationReport(data.report);
        toast.success("Audit completed");
      }
    } catch (error) {
      toast.error("Audit failed");
    } finally {
      setSanitizing(false);
    }
  };

  const runSanitizationDelete = async () => {
    setSanitizing(true);
    setShowDeleteConfirm(false);
    try {
      const res = await fetch(`${API}/data-management/sanitize`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ mode: "delete" })
      });
      if (res.ok) {
        toast.success("Sanitization started in background");
        // Refresh data after a delay
        setTimeout(() => {
          fetchDataCounts();
        }, 5000);
      }
    } catch (error) {
      toast.error("Sanitization failed");
    } finally {
      setSanitizing(false);
    }
  };

  const runFullSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch(`${API}/data-management/sync/full`, {
        method: "POST",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        toast.success("Full sync started in background");
        // Poll for status
        const pollStatus = setInterval(async () => {
          await fetchSyncStatus();
          const status = syncStatus?.modules || {};
          const allCompleted = Object.values(status).every(m => m.status !== "syncing");
          if (allCompleted) {
            clearInterval(pollStatus);
            setSyncing(false);
            fetchDataCounts();
          }
        }, 3000);
      }
    } catch (error) {
      toast.error("Sync failed");
      setSyncing(false);
    }
  };

  const syncModule = async (module) => {
    try {
      const res = await fetch(`${API}/data-management/sync/module`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ module, full_sync: true })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Synced ${data.result.records_synced} ${module} records`);
        fetchSyncStatus();
        fetchDataCounts();
      }
    } catch (error) {
      toast.error(`Failed to sync ${module}`);
    }
  };

  const fixNegativeStock = async () => {
    try {
      const res = await fetch(`${API}/data-management/cleanup/negative-stock`, {
        method: "POST",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchDataCounts();
      }
    } catch (error) {
      toast.error("Failed to fix negative stock");
    }
  };

  const cleanOrphanedRecords = async () => {
    try {
      const res = await fetch(`${API}/data-management/cleanup/orphaned-records`, {
        method: "POST",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        const total = Object.values(data.cleaned).reduce((a, b) => a + b, 0);
        toast.success(`Cleaned ${total} orphaned records`);
        fetchDataCounts();
      }
    } catch (error) {
      toast.error("Failed to clean orphaned records");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const totalRecords = Object.values(dataCounts).reduce((a, b) => a + (b.total || 0), 0);
  const zohoSyncedRecords = Object.values(dataCounts).reduce((a, b) => a + (b.zoho_synced || 0), 0);
  const localOnlyRecords = totalRecords - zohoSyncedRecords;

  return (
    <div className="space-y-6" data-testid="data-management-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Management</h1>
          <p className="text-muted-foreground">
            Manage data synchronization with Zoho Books and clean test data
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => Promise.all([fetchDataCounts(), fetchSyncStatus()])}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Connection Status */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`h-12 w-12 rounded-full flex items-center justify-center ${
                connectionStatus?.status === "connected" 
                  ? "bg-[rgba(34,197,94,0.10)] text-[#22C55E]" 
                  : "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F]"
              }`}>
                <Link2 className="h-6 w-6" />
              </div>
              <div>
                <div className="font-medium">Zoho Books Connection</div>
                <div className="text-sm text-muted-foreground">
                  {connectionStatus?.status === "connected" 
                    ? `Connected to organization ${connectionStatus.active_org}`
                    : connectionStatus?.error || "Not connected"}
                </div>
              </div>
            </div>
            <Badge variant={connectionStatus?.status === "connected" ? "default" : "destructive"}>
              {connectionStatus?.status === "connected" ? "Connected" : "Disconnected"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Records</p>
                <p className="text-2xl font-bold">{totalRecords.toLocaleString()}</p>
              </div>
              <Database className="h-8 w-8 text-primary opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Zoho Synced</p>
                <p className="text-2xl font-bold text-[#22C55E]">{zohoSyncedRecords.toLocaleString()}</p>
              </div>
              <CloudDownload className="h-8 w-8 text-[#22C55E] opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Local Only</p>
                <p className="text-2xl font-bold text-amber-600">{localOnlyRecords.toLocaleString()}</p>
              </div>
              <Server className="h-8 w-8 text-amber-600 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Test Records</p>
                <p className="text-2xl font-bold text-[#FF3B2F]">
                  {sanitizationReport?.total_test_records || "—"}
                </p>
              </div>
              <Trash2 className="h-8 w-8 text-[#FF3B2F] opacity-80" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sync">Zoho Sync</TabsTrigger>
          <TabsTrigger value="sanitize">Data Cleanup</TabsTrigger>
          <TabsTrigger value="validation">Validation</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Distribution by Module</CardTitle>
              <CardDescription>Record counts per collection</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {Object.entries(dataCounts).map(([collection, counts]) => (
                  <div key={collection} className="p-4 border rounded-lg">
                    <div className="text-sm font-medium capitalize">{collection.replace(/_/g, " ")}</div>
                    <div className="text-2xl font-bold">{counts.total || 0}</div>
                    <div className="flex gap-2 mt-1 text-xs">
                      <span className="text-[#22C55E]">{counts.zoho_synced || 0} Zoho</span>
                      <span className="text-muted-foreground">{counts.local_only || 0} local</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Zoho Sync Tab */}
        <TabsContent value="sync" className="space-y-4">
          <div className="flex gap-4">
            <Button onClick={runFullSync} disabled={syncing || connectionStatus?.status !== "connected"}>
              {syncing ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CloudDownload className="h-4 w-4 mr-2" />
              )}
              Full Sync from Zoho
            </Button>
            <Button variant="outline" onClick={testConnection}>
              <Zap className="h-4 w-4 mr-2" />
              Test Connection
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Module Sync Status</CardTitle>
              <CardDescription>Last sync time and status for each module</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Module</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Records Synced</TableHead>
                    <TableHead>Last Sync</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {["contacts", "items", "invoices", "estimates", "bills", "expenses", "customerpayments", "salesorders"].map(module => {
                    const status = syncStatus?.modules?.[module] || {};
                    return (
                      <TableRow key={module}>
                        <TableCell className="font-medium capitalize">{module}</TableCell>
                        <TableCell>
                          <Badge variant={
                            status.status === "synced" ? "default" :
                            status.status === "syncing" ? "secondary" :
                            status.status === "error" ? "destructive" : "outline"
                          }>
                            {status.status || "Not synced"}
                          </Badge>
                        </TableCell>
                        <TableCell>{status.records_synced || 0}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {status.last_sync ? new Date(status.last_sync).toLocaleString() : "Never"}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => syncModule(module)}
                            disabled={connectionStatus?.status !== "connected"}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sanitization Tab */}
        <TabsContent value="sanitize" className="space-y-4">
          <div className="flex gap-4">
            <Button onClick={runSanitizationAudit} disabled={sanitizing}>
              {sanitizing ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Eye className="h-4 w-4 mr-2" />
              )}
              Audit Test Data
            </Button>
            <Button 
              variant="destructive" 
              onClick={() => setShowDeleteConfirm(true)}
              disabled={sanitizing || !sanitizationReport}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Test Data
            </Button>
            <Button variant="outline" onClick={fixNegativeStock}>
              <TrendingUp className="h-4 w-4 mr-2" />
              Fix Negative Stock
            </Button>
            <Button variant="outline" onClick={cleanOrphanedRecords}>
              <FileText className="h-4 w-4 mr-2" />
              Clean Orphaned Records
            </Button>
          </div>

          {sanitizationReport && (
            <Card>
              <CardHeader>
                <CardTitle>Sanitization Report</CardTitle>
                <CardDescription>
                  Job: {sanitizationReport.job_id} | Mode: {sanitizationReport.mode} | 
                  Status: {sanitizationReport.status}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="p-4 border rounded-lg text-center">
                    <p className="text-2xl font-bold">{sanitizationReport.total_records_scanned}</p>
                    <p className="text-sm text-muted-foreground">Records Scanned</p>
                  </div>
                  <div className="p-4 border rounded-lg text-center bg-[rgba(255,59,47,0.08)]">
                    <p className="text-2xl font-bold text-[#FF3B2F]">{sanitizationReport.total_test_records}</p>
                    <p className="text-sm text-muted-foreground">Test Records Found</p>
                  </div>
                  <div className="p-4 border rounded-lg text-center bg-[rgba(34,197,94,0.08)]">
                    <p className="text-2xl font-bold text-[#22C55E]">{sanitizationReport.total_deleted}</p>
                    <p className="text-sm text-muted-foreground">Records Deleted</p>
                  </div>
                </div>

                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Collection</TableHead>
                        <TableHead>Total</TableHead>
                        <TableHead>Test Found</TableHead>
                        <TableHead>Deleted</TableHead>
                        <TableHead>Kept</TableHead>
                        <TableHead>Sample Records</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sanitizationReport.results?.map((result) => (
                        <TableRow key={result.collection}>
                          <TableCell className="font-medium">{result.collection}</TableCell>
                          <TableCell>{result.total_records}</TableCell>
                          <TableCell className="text-[#FF3B2F]">{result.test_records_found}</TableCell>
                          <TableCell className="text-[#22C55E]">{result.records_deleted}</TableCell>
                          <TableCell>{result.records_kept}</TableCell>
                          <TableCell className="max-w-xs truncate">
                            {result.sample_deleted?.slice(0, 2).map(s => s.name).join(", ") || "—"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Validation Tab */}
        <TabsContent value="validation" className="space-y-4">
          <div className="flex gap-4">
            <Button variant="outline" onClick={async () => {
              const res = await fetch(`${API}/data-management/validate/integrity`, {
                headers: getAuthHeaders()
              });
              if (res.ok) {
                const data = await res.json();
                toast.success(`Integrity check: ${data.validation.total_issues} issues found`);
              }
            }}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Check Referential Integrity
            </Button>
            <Button variant="outline" onClick={async () => {
              const res = await fetch(`${API}/data-management/validate/completeness`, {
                headers: getAuthHeaders()
              });
              if (res.ok) {
                const data = await res.json();
                toast.success(`Completeness check: ${data.validation.total_issues} issues found`);
              }
            }}>
              <Activity className="h-4 w-4 mr-2" />
              Check Data Completeness
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Data Quality Checks</CardTitle>
              <CardDescription>Validate data integrity and completeness</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">Referential Integrity</p>
                      <p className="text-sm text-muted-foreground">All foreign keys reference valid records</p>
                    </div>
                  </div>
                  <Badge variant="outline">Run Check</Badge>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">Stock Levels</p>
                      <p className="text-sm text-muted-foreground">No negative inventory quantities</p>
                    </div>
                  </div>
                  <Badge variant="outline">Run Check</Badge>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                    <div>
                      <p className="font-medium">Contact Data</p>
                      <p className="text-sm text-muted-foreground">Required fields are populated</p>
                    </div>
                  </div>
                  <Badge variant="outline">Run Check</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Test Data</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete {sanitizationReport?.total_test_records || 0} test records 
              from your database. A backup will be created for rollback. This action cannot be undone 
              without using the rollback feature.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={runSanitizationDelete} className="bg-destructive text-destructive-foreground">
              Delete Test Data
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

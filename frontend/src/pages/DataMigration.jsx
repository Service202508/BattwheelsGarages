import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { Database, Upload, Play, CheckCircle2, AlertCircle, Users, Package, FileText, CreditCard, Building2, Receipt } from "lucide-react";
import { API } from "@/App";

export default function DataMigration({ user }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [migrating, setMigrating] = useState(false);
  const [filesReady, setFilesReady] = useState(false);

  useEffect(() => {
    checkStatus();
    checkFiles();
  }, []);

  const checkStatus = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/migration/status`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch status:", error);
    } finally {
      setLoading(false);
    }
  };

  const checkFiles = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/migration/upload`, {
        method: "POST",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setFilesReady(data.files_found > 0);
      }
    } catch (error) {
      setFilesReady(false);
    }
  };

  const runFullMigration = async () => {
    setMigrating(true);
    toast.info("Starting full migration... This may take several minutes.");
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/migration/run`, {
        method: "POST",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success("Migration completed successfully!");
        checkStatus();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Migration failed");
      }
    } catch (error) {
      toast.error("Migration failed: " + error.message);
    } finally {
      setMigrating(false);
    }
  };

  const migrationItems = [
    { key: "customers", label: "Customers", icon: Users, color: "text-blue-500" },
    { key: "suppliers", label: "Suppliers", icon: Building2, color: "text-purple-500" },
    { key: "inventory", label: "Inventory", icon: Package, color: "text-green-500" },
    { key: "invoices", label: "Invoices", icon: FileText, color: "text-orange-500" },
    { key: "sales_orders", label: "Sales Orders", icon: CreditCard, color: "text-yellow-500" },
    { key: "purchase_orders", label: "Purchase Orders", icon: Receipt, color: "text-pink-500" },
    { key: "payments", label: "Payments", icon: CreditCard, color: "text-cyan-500" },
    { key: "expenses", label: "Expenses", icon: Receipt, color: "text-red-500" },
    { key: "accounts", label: "Chart of Accounts", icon: Database, color: "text-indigo-500" },
  ];

  const totalMigrated = status ? Object.values(status.migrated_records).reduce((a, b) => a + b, 0) : 0;
  const totalRecords = status ? Object.values(status.total_records).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="space-y-6" data-testid="data-migration-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Migration</h1>
          <p className="text-muted-foreground">Import data from legacy ERP systems (Zoho Books).</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={runFullMigration} 
            disabled={migrating || !filesReady}
            data-testid="run-migration-btn"
          >
            <Play className="mr-2 h-4 w-4" />
            {migrating ? "Migrating..." : "Run Full Migration"}
          </Button>
        </div>
      </div>

      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Migration Status
          </CardTitle>
          <CardDescription>
            Current state of data migration from legacy system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Overall Progress</span>
              <Badge className={status?.migration_complete ? 'badge-success' : 'bg-bw-amber/10'}>
                {status?.migration_complete ? 'Complete' : 'Pending'}
              </Badge>
            </div>
            <Progress value={totalRecords > 0 ? (totalMigrated / totalRecords) * 100 : 0} className="h-2" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{totalMigrated.toLocaleString()} records migrated</span>
              <span>{totalRecords.toLocaleString()} total records</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* File Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Legacy Data Files
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            {filesReady ? (
              <>
                <CheckCircle2 className="h-6 w-6 text-green-500" />
                <div>
                  <p className="font-medium">Legacy data files found</p>
                  <p className="text-sm text-muted-foreground">Ready for migration from /tmp/legacy_data</p>
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="h-6 w-6 text-yellow-500" />
                <div>
                  <p className="font-medium">No legacy data files found</p>
                  <p className="text-sm text-muted-foreground">
                    Extract backup files to /tmp/legacy_data directory
                  </p>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Migration Details */}
      <div className="grid gap-4 md:grid-cols-3">
        {migrationItems.map((item) => {
          const Icon = item.icon;
          const migrated = status?.migrated_records?.[item.key] || 0;
          const total = status?.total_records?.[item.key] || 0;
          
          return (
            <Card key={item.key}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{item.label}</CardTitle>
                <Icon className={`h-4 w-4 ${item.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{total.toLocaleString()}</div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-muted-foreground">
                    {migrated.toLocaleString()} migrated
                  </span>
                  {migrated > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <CheckCircle2 className="h-3 w-3 mr-1 text-green-500" />
                      Done
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Migration Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium">Supported Source Systems:</h4>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              <li>Zoho Books - Full export with all modules</li>
              <li>XLS/XLSX files from backup exports</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">Data Migrated:</h4>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              <li>Contacts → Customers</li>
              <li>Vendors → Suppliers</li>
              <li>Items → Inventory</li>
              <li>Sales Orders, Purchase Orders, Invoices</li>
              <li>Customer Payments, Expenses</li>
              <li>Chart of Accounts</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  RefreshCw, Loader2, Activity, Clock, User,
  FileText, Edit, Trash2, Plus, Eye, ChevronLeft, ChevronRight
} from "lucide-react";
import { API } from "@/App";

// Entity types with icons and colors
const ENTITY_TYPES = {
  invoice: { label: "Invoice", color: "bg-blue-100 text-blue-800", icon: FileText },
  bill: { label: "Bill", color: "bg-orange-100 text-orange-800", icon: FileText },
  expense: { label: "Expense", color: "bg-red-100 text-red-800", icon: FileText },
  contact: { label: "Contact", color: "bg-[rgba(34,197,94,0.10)] text-[#22C55E]", icon: User },
  customer: { label: "Customer", color: "bg-[rgba(34,197,94,0.10)] text-[#22C55E]", icon: User },
  vendor: { label: "Vendor", color: "bg-yellow-100 text-yellow-800", icon: User },
  item: { label: "Item", color: "bg-purple-100 text-purple-800", icon: FileText },
  payment: { label: "Payment", color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] text-800", icon: FileText },
  project: { label: "Project", color: "bg-indigo-100 text-indigo-800", icon: FileText },
  estimate: { label: "Estimate", color: "bg-cyan-100 text-cyan-800", icon: FileText },
  creditnote: { label: "Credit Note", color: "bg-pink-100 text-pink-800", icon: FileText },
  journal: { label: "Journal", color: "bg-amber-100 text-amber-800", icon: FileText }
};

// Action types with icons and colors
const ACTION_TYPES = {
  created: { label: "Created", color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]", icon: Plus },
  updated: { label: "Updated", color: "bg-blue-100 text-[#3B9EFF]", icon: Edit },
  deleted: { label: "Deleted", color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]", icon: Trash2 },
  viewed: { label: "Viewed", color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]", icon: Eye },
  sent: { label: "Sent", color: "bg-purple-100 text-[#8B5CF6]", icon: FileText },
  paid: { label: "Paid", color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] text-700", icon: FileText },
  approved: { label: "Approved", color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]", icon: FileText },
  voided: { label: "Voided", color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]", icon: FileText }
};

export default function ActivityLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [entityTypeFilter, setEntityTypeFilter] = useState("");
  const [page, setPage] = useState(1);
  const [pageContext, setPageContext] = useState({ total: 0, per_page: 50 });
  
  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchLogs();
  }, [entityTypeFilter, page]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (entityTypeFilter) params.set("entity_type", entityTypeFilter);
      params.set("page", page.toString());
      params.set("per_page", "50");
      
      const res = await fetch(`${API}/zoho/activity-logs?${params}`, { headers });
      const data = await res.json();
      setLogs(data.activity_logs || []);
      setPageContext(data.page_context || { total: 0, per_page: 50 });
    } catch (error) {
      console.error("Error fetching activity logs:", error);
      toast.error("Failed to load activity logs");
    } finally {
      setLoading(false);
    }
  };

  const getEntityTypeBadge = (type) => {
    const config = ENTITY_TYPES[type?.toLowerCase()] || { 
      label: type, 
      color: "bg-[rgba(255,255,255,0.05)] text-[#F4F6F0]" 
    };
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  const getActionBadge = (action) => {
    const config = ACTION_TYPES[action?.toLowerCase()] || { 
      label: action, 
      color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]" 
    };
    const Icon = config.icon || Activity;
    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "-";
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const totalPages = Math.ceil(pageContext.total / pageContext.per_page);

  return (
    <div className="space-y-6" data-testid="activity-logs-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Activity Logs</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Audit trail of all system activities</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={entityTypeFilter || "all"} onValueChange={(v) => { setEntityTypeFilter(v === "all" ? "" : v); setPage(1); }}>
            <SelectTrigger className="w-40" data-testid="entity-type-filter">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {Object.entries(ENTITY_TYPES).map(([key, val]) => (
                <SelectItem key={key} value={key}>{val.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={fetchLogs}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Activity className="h-5 w-5 text-[#3B9EFF]" />
              </div>
              <div>
                <p className="text-xs text-[#3B9EFF]">Total Activities</p>
                <p className="text-xl font-bold text-blue-800">{pageContext.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[rgba(34,197,94,0.10)] rounded-lg">
                <Plus className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-green-600">Created</p>
                <p className="text-xl font-bold text-[#22C55E]">
                  {logs.filter(l => l.action?.toLowerCase() === 'created').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Edit className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-xs text-amber-600">Updated</p>
                <p className="text-xl font-bold text-amber-800">
                  {logs.filter(l => l.action?.toLowerCase() === 'updated').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-50 to-rose-50 border-red-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <Trash2 className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-xs text-red-600">Deleted</p>
                <p className="text-xl font-bold text-red-800">
                  {logs.filter(l => l.action?.toLowerCase() === 'deleted').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No activity logs found</p>
              <p className="text-sm">Activities will appear here as users interact with the system</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#111820]">
                    <TableHead className="w-[180px]">Timestamp</TableHead>
                    <TableHead>Entity Type</TableHead>
                    <TableHead>Entity ID</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.log_id}>
                      <TableCell>
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                          <span className="text-[rgba(244,246,240,0.35)]">{formatTimestamp(log.timestamp)}</span>
                        </div>
                      </TableCell>
                      <TableCell>{getEntityTypeBadge(log.entity_type)}</TableCell>
                      <TableCell>
                        <span className="font-mono text-sm text-[rgba(244,246,240,0.35)]">
                          {log.entity_id?.slice(0, 20) || "-"}
                        </span>
                      </TableCell>
                      <TableCell>{getActionBadge(log.action)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                          <span className="text-sm">{log.user_name || log.user_id || "System"}</span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[200px]">
                        {log.details && Object.keys(log.details).length > 0 ? (
                          <span className="text-xs text-[rgba(244,246,240,0.45)] truncate block">
                            {JSON.stringify(log.details).slice(0, 50)}...
                          </span>
                        ) : (
                          <span className="text-[rgba(244,246,240,0.45)]">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">
                    Showing {((page - 1) * pageContext.per_page) + 1} to {Math.min(page * pageContext.per_page, pageContext.total)} of {pageContext.total} entries
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-[rgba(244,246,240,0.35)]">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

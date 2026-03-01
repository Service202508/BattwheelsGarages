import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bell, AlertTriangle, Package, Ticket, CheckCircle } from "lucide-react";
import { API } from "@/App";

const severityColors = {
  info: "badge-info",
  warning: "badge-warning",
  critical: "badge-danger",
};

const typeIcons = {
  low_inventory: Package,
  pending_ticket: Ticket,
  maintenance_due: AlertTriangle,
  system: Bell,
};

export default function Alerts({ user }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/alerts`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
    } finally {
      setLoading(false);
    }
  };

  const criticalAlerts = alerts.filter(a => a.severity === "critical");
  const warningAlerts = alerts.filter(a => a.severity === "warning");
  const infoAlerts = alerts.filter(a => a.severity === "info");

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="alerts-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Alerts</h1>
        <p className="text-muted-foreground mt-1">System notifications and warnings.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-red-500/30 bg-bw-red/5">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-red-400">Critical</p>
              <p className="text-2xl font-bold text-red-400 mono">{criticalAlerts.length}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-400" />
          </CardContent>
        </Card>
        <Card className="border-orange-500/30 bg-bw-orange/5">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-400">Warnings</p>
              <p className="text-2xl font-bold text-orange-400 mono">{warningAlerts.length}</p>
            </div>
            <Bell className="h-8 w-8 text-orange-400" />
          </CardContent>
        </Card>
        <Card className="border-cyan-500/30 bg-cyan-500/5">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-cyan-400">Info</p>
              <p className="text-2xl font-bold text-cyan-400 mono">{infoAlerts.length}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-cyan-400" />
          </CardContent>
        </Card>
      </div>

      {/* Alerts List */}
      <Card className="border-white/10 bg-card/50">
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>All active system notifications</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading alerts...</div>
          ) : alerts.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 text-bw-volt text-400" />
              <p>All systems operational. No alerts at this time.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {alerts.map((alert) => {
                const Icon = typeIcons[alert.type] || Bell;
                return (
                  <div
                    key={alert.alert_id}
                    className={`p-4 rounded-lg border transition-all hover:border-white/20 ${
                      alert.severity === "critical"
                        ? "border-red-500/30 bg-bw-red/5"
                        : alert.severity === "warning"
                        ? "border-orange-500/30 bg-bw-orange/5"
                        : "border-white/10 bg-background/50"
                    }`}
                    data-testid={`alert-${alert.alert_id}`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        alert.severity === "critical"
                          ? "bg-bw-red/20"
                          : alert.severity === "warning"
                          ? "bg-bw-orange/20"
                          : "bg-primary/20"
                      }`}>
                        <Icon className={`h-5 w-5 ${
                          alert.severity === "critical"
                            ? "text-red-400"
                            : alert.severity === "warning"
                            ? "text-orange-400"
                            : "text-primary"
                        }`} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-medium">{alert.title}</h4>
                          <Badge className={severityColors[alert.severity]} variant="outline">
                            {alert.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{alert.message}</p>
                        <p className="text-xs text-muted-foreground mt-2 mono">
                          {new Date(alert.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

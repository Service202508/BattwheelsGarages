import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  Ticket, Clock, AlertCircle, CheckCircle, TrendingUp,
  Play, Square, ArrowRight, Zap, Award, Calendar,
  Loader2, FileText, Timer, Target
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  open: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  assigned: "bg-bw-purple/[0.08]0/20 text-purple-400 border-purple-500/30",
  work_in_progress: "bg-bw-orange/[0.08]0/20 text-orange-400 border-orange-500/30",
  estimate_sent: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  work_completed: "bg-bw-green/[0.08]0/20 text-green-400 border-green-500/30",
  closed: "bg-slate-500/20 text-slate-400 border-white/[0.07] border-500/30",
};

const priorityColors = {
  low: "bg-bw-green/[0.08]0/10 text-green-400",
  medium: "bg-bw-amber/[0.08]0/10 text-yellow-400",
  high: "bg-bw-orange/[0.08]0/10 text-orange-400",
  critical: "bg-bw-red/[0.08]0/10 text-red-400",
};

export default function TechnicianDashboard({ user }) {
  const [dashboard, setDashboard] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [showCheckDialog, setShowCheckDialog] = useState(false);
  const [checkType, setCheckType] = useState(null); // 'in' or 'out'

  useEffect(() => {
    fetchDashboard();
    fetchRecentTickets();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/technician/dashboard`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentTickets = async () => {
    try {
      const res = await fetch(`${API}/technician/tickets?status=active&limit=5`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setRecentTickets(data.tickets || []);
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    }
  };

  const handleCheckInOut = async (type) => {
    setCheckingIn(true);
    try {
      const endpoint = type === 'in' ? 'check-in' : 'check-out';
      const res = await fetch(`${API}/technician/attendance/${endpoint}`, {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include"
      });
      
      if (res.ok) {
        toast.success(type === 'in' ? "Checked in successfully!" : "Checked out successfully!");
        fetchDashboard();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to record attendance");
      }
    } catch (error) {
      toast.error("Failed to record attendance");
    } finally {
      setCheckingIn(false);
      setShowCheckDialog(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-green-500" />
      </div>
    );
  }

  const attendance = dashboard?.attendance || {};
  const canCheckIn = !attendance.check_in;
  const canCheckOut = attendance.check_in && !attendance.check_out;

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="technician-dashboard">
      {/* Welcome Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-500/20 via-emerald-500/10 to-slate-900 border border-green-500/20 p-6">
        <div className="absolute top-0 right-0 w-64 h-64 bg-bw-green/[0.08]0/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">
                Good {new Date().getHours() < 12 ? 'Morning' : new Date().getHours() < 17 ? 'Afternoon' : 'Evening'}, {dashboard?.technician?.name?.split(' ')[0] || 'Technician'}!
              </h1>
              <p className="text-slate-400">
                You have <span className="text-green-400 font-semibold">{dashboard?.tickets?.total_assigned || 0}</span> tickets assigned to you
              </p>
            </div>
            <div className="flex items-center gap-3">
              {canCheckIn && (
                <Button 
                  onClick={() => { setCheckType('in'); setShowCheckDialog(true); }}
                  className="bg-bw-green hover:bg-bw-green-hover"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Check In
                </Button>
              )}
              {canCheckOut && (
                <Button 
                  onClick={() => { setCheckType('out'); setShowCheckDialog(true); }}
                  variant="outline"
                  className="border-red-500/30 text-red-400 hover:bg-bw-red/[0.08]0/10"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Check Out
                </Button>
              )}
            </div>
          </div>
          
          {/* Attendance Status */}
          {attendance.check_in && (
            <div className="mt-4 flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-white/[0.07] border-700">
                <Clock className="h-4 w-4 text-green-400" />
                <span className="text-slate-300">In: {attendance.check_in}</span>
              </div>
              {attendance.check_out && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-white/[0.07] border-700">
                  <Clock className="h-4 w-4 text-red-400" />
                  <span className="text-slate-300">Out: {attendance.check_out}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-blue-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Open</p>
                <p className="text-2xl font-bold text-white mt-1">{dashboard?.tickets?.open || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-blue-500/10">
                <Ticket className="h-5 w-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-orange-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">In Progress</p>
                <p className="text-2xl font-bold text-white mt-1">{dashboard?.tickets?.in_progress || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-bw-orange/[0.08]0/10">
                <Timer className="h-5 w-5 text-orange-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-cyan-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Estimate Pending</p>
                <p className="text-2xl font-bold text-white mt-1">{dashboard?.tickets?.pending_estimate_approval || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-cyan-500/10">
                <FileText className="h-5 w-5 text-cyan-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-green-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Completed Today</p>
                <p className="text-2xl font-bold text-white mt-1">{dashboard?.tickets?.completed_today || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-bw-green/[0.08]0/10">
                <CheckCircle className="h-5 w-5 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-purple-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">This Month</p>
                <p className="text-2xl font-bold text-white mt-1">{dashboard?.tickets?.completed_month || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-bw-purple/[0.08]0/10">
                <Target className="h-5 w-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* My Active Tickets */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-900/50 border-white/[0.07] border-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-white">My Active Tickets</CardTitle>
                <CardDescription>Tickets assigned to you</CardDescription>
              </div>
              <Link to="/technician/tickets">
                <Button variant="ghost" size="sm" className="text-green-400 hover:text-green-300">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {recentTickets.length === 0 ? (
                <div className="text-center py-8">
                  <Ticket className="h-12 w-12 mx-auto text-slate-600 mb-3" />
                  <p className="text-slate-400">No active tickets assigned</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentTickets.map((ticket) => (
                    <Link 
                      key={ticket.ticket_id} 
                      to={`/technician/tickets/${ticket.ticket_id}`}
                      className="block p-4 rounded-xl border border-white/[0.07] border-800 hover:border-green-500/30 hover:bg-slate-800/50 transition-all"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={statusColors[ticket.status] || statusColors.open}>
                              {ticket.status?.replace('_', ' ')}
                            </Badge>
                            <Badge className={priorityColors[ticket.priority] || priorityColors.medium}>
                              {ticket.priority}
                            </Badge>
                          </div>
                          <h4 className="font-medium text-white truncate">{ticket.title}</h4>
                          <div className="flex items-center gap-3 mt-2 text-sm text-slate-400">
                            <span>{ticket.vehicle_number}</span>
                            <span>•</span>
                            <span>{ticket.vehicle_model}</span>
                          </div>
                        </div>
                        <ArrowRight className="h-5 w-5 text-slate-600 flex-shrink-0" />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Performance Card */}
          <Card className="bg-slate-900/50 border-white/[0.07] border-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-400" />
                My Performance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Avg. Resolution Time</span>
                  <span className="text-white font-medium">{dashboard?.performance?.avg_resolution_hours || 0} hrs</span>
                </div>
                <Progress 
                  value={Math.min((8 / (dashboard?.performance?.avg_resolution_hours || 8)) * 100, 100)} 
                  className="h-2 bg-slate-800"
                />
                <p className="text-xs text-slate-500">Target: Under 8 hours</p>
              </div>
              
              <div className="pt-4 border-t border-white/[0.07] border-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">This Month</span>
                  <span className="text-2xl font-bold text-green-400">{dashboard?.tickets?.completed_month || 0}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">tickets resolved</p>
              </div>
              
              <Link to="/technician/productivity">
                <Button variant="outline" className="w-full border-white/[0.07] border-700 text-slate-300 hover:bg-slate-800">
                  View Detailed Stats
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-slate-900/50 border-white/[0.07] border-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-white">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to="/technician/leave">
                <Button variant="outline" className="w-full justify-start border-white/[0.07] border-700 text-slate-300 hover:bg-slate-800">
                  <Calendar className="h-4 w-4 mr-2 text-purple-400" />
                  Apply for Leave
                  {dashboard?.pending_leave_requests > 0 && (
                    <Badge className="ml-auto bg-bw-purple/[0.08]0/20 text-purple-400">{dashboard.pending_leave_requests}</Badge>
                  )}
                </Button>
              </Link>
              <Link to="/technician/ai-assist">
                <Button variant="outline" className="w-full justify-start border-white/[0.07] border-700 text-slate-300 hover:bg-slate-800">
                  <Zap className="h-4 w-4 mr-2 text-yellow-400" />
                  AI Diagnosis Help
                </Button>
              </Link>
              <Link to="/technician/attendance">
                <Button variant="outline" className="w-full justify-start border-white/[0.07] border-700 text-slate-300 hover:bg-slate-800">
                  <Clock className="h-4 w-4 mr-2 text-blue-400" />
                  View Attendance
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Check In/Out Dialog */}
      <Dialog open={showCheckDialog} onOpenChange={setShowCheckDialog}>
        <DialogContent className="bg-slate-900 border-white/[0.07] border-800">
          <DialogHeader>
            <DialogTitle className="text-white">
              {checkType === 'in' ? 'Check In' : 'Check Out'} Confirmation
            </DialogTitle>
          </DialogHeader>
          <div className="py-4 text-center">
            <div className={`inline-flex p-4 rounded-full ${checkType === 'in' ? 'bg-bw-green/[0.08]0/20' : 'bg-bw-red/[0.08]0/20'} mb-4`}>
              {checkType === 'in' ? (
                <Play className="h-8 w-8 text-green-400" />
              ) : (
                <Square className="h-8 w-8 text-red-400" />
              )}
            </div>
            <p className="text-slate-300">
              {checkType === 'in' 
                ? 'Start your work day by checking in.' 
                : 'End your work day by checking out.'}
            </p>
            <p className="text-sm text-slate-500 mt-2">
              Current time: {new Date().toLocaleTimeString()}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCheckDialog(false)} className="border-white/[0.07] border-700">
              Cancel
            </Button>
            <Button 
              onClick={() => handleCheckInOut(checkType)}
              disabled={checkingIn}
              className={checkType === 'in' ? 'bg-bw-green hover:bg-bw-green-hover' : 'bg-red-600 hover:bg-red-700'}
            >
              {checkingIn ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              {checkType === 'in' ? 'Check In' : 'Check Out'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

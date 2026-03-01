import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
  TrendingUp, Award, Target, Loader2, Ticket, Clock,
  CheckCircle, BarChart3, Trophy, Zap, ArrowUp, ArrowDown
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

export default function TechnicianProductivity({ user }) {
  const [productivityData, setProductivityData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProductivity();
  }, []);

  const fetchProductivity = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/technician/productivity`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setProductivityData(data);
      }
    } catch (error) {
      console.error("Failed to fetch productivity:", error);
      toast.error("Failed to load productivity data");
    } finally {
      setLoading(false);
    }
  };

  const priorityColors = {
    low: { bg: "bg-bw-green/[0.08]0/10", text: "text-green-400", bar: "bg-bw-green/[0.08]0" },
    medium: { bg: "bg-amber-500/10", text: "text-amber-400", bar: "bg-amber-500" },
    high: { bg: "bg-bw-orange/[0.08]0/10", text: "text-orange-400", bar: "bg-bw-orange/[0.08]0" },
    critical: { bg: "bg-bw-red/[0.08]0/10", text: "text-red-400", bar: "bg-bw-red/[0.08]0" },
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-green-500" />
      </div>
    );
  }

  const thisMonth = productivityData?.this_month || {};
  const priorityBreakdown = productivityData?.priority_breakdown || {};
  const weeklyTrend = productivityData?.weekly_trend || [];
  const rank = productivityData?.rank || 0;
  const totalTechs = productivityData?.total_technicians || 1;

  return (
    <div className="space-y-6" data-testid="technician-productivity">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Performance</h1>
          <p className="text-slate-400">Track your productivity metrics</p>
        </div>
        <Button variant="outline" onClick={fetchProductivity} className="border-white/[0.07] border-700">
          <TrendingUp className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Rank Card */}
      <Card className="bg-gradient-to-br from-amber-500/20 via-yellow-500/10 to-slate-900 border border-amber-500/20 overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-amber-300 text-sm mb-2">Your Rank This Month</p>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-white">#{rank}</span>
                <span className="text-slate-400">of {totalTechs} technicians</span>
              </div>
              {rank <= 3 && (
                <div className="flex items-center gap-2 mt-3">
                  <Trophy className={`h-5 w-5 ${rank === 1 ? 'text-yellow-400' : rank === 2 ? 'text-slate-300' : 'text-amber-600'}`} />
                  <span className="text-amber-300 text-sm">
                    {rank === 1 ? 'Top Performer!' : rank === 2 ? 'Runner Up!' : 'Top 3!'}
                  </span>
                </div>
              )}
            </div>
            <div className="p-4 rounded-2xl bg-amber-500/20">
              <Award className="h-12 w-12 text-amber-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-bw-green/[0.08]0/10">
                <CheckCircle className="h-5 w-5 text-green-400" />
              </div>
              <Badge className="bg-bw-green/[0.08]0/20 text-green-400 border-green-500/30">This Month</Badge>
            </div>
            <p className="text-3xl font-bold text-white">{thisMonth.tickets_resolved || 0}</p>
            <p className="text-xs text-slate-500 mt-1">Tickets Resolved</p>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Clock className="h-5 w-5 text-blue-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">{thisMonth.avg_resolution_hours || 0}h</p>
            <p className="text-xs text-slate-500 mt-1">Avg Resolution Time</p>
            <div className="flex items-center gap-1 mt-2">
              {thisMonth.avg_resolution_hours <= 8 ? (
                <>
                  <ArrowDown className="h-3 w-3 text-green-400" />
                  <span className="text-xs text-green-400">Within target</span>
                </>
              ) : (
                <>
                  <ArrowUp className="h-3 w-3 text-amber-400" />
                  <span className="text-xs text-amber-400">Above target</span>
                </>
              )}
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-bw-purple/[0.08]0/10">
                <Target className="h-5 w-5 text-purple-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">
              {Object.values(priorityBreakdown).reduce((a, b) => a + b, 0)}
            </p>
            <p className="text-xs text-slate-500 mt-1">Total Resolved</p>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <Zap className="h-5 w-5 text-amber-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">
              {priorityBreakdown.critical || 0}
            </p>
            <p className="text-xs text-slate-500 mt-1">Critical Resolved</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Weekly Trend */}
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-green-400" />
              Weekly Trend
            </CardTitle>
            <CardDescription>Tickets resolved per week</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {weeklyTrend.map((week, index) => {
                const maxResolved = Math.max(...weeklyTrend.map(w => w.resolved || 0), 1);
                const percentage = ((week.resolved || 0) / maxResolved) * 100;
                
                return (
                  <div key={index}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-400">{week.week}</span>
                      <span className="text-white font-medium">{week.resolved || 0} tickets</span>
                    </div>
                    <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Priority Breakdown */}
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Ticket className="h-5 w-5 text-purple-400" />
              By Priority
            </CardTitle>
            <CardDescription>Tickets resolved by priority level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(priorityBreakdown).map(([priority, count]) => {
                const colors = priorityColors[priority] || priorityColors.medium;
                const total = Object.values(priorityBreakdown).reduce((a, b) => a + b, 1);
                const percentage = (count / total) * 100;
                
                return (
                  <div key={priority}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${colors.bar}`} />
                        <span className={`text-sm capitalize ${colors.text}`}>{priority}</span>
                      </div>
                      <span className="text-white font-medium">{count}</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${colors.bar} rounded-full transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Total */}
            <div className="mt-6 pt-4 border-t border-white/[0.07] border-800">
              <div className="flex justify-between">
                <span className="text-slate-400">Total Resolved</span>
                <span className="text-xl font-bold text-green-400">
                  {Object.values(priorityBreakdown).reduce((a, b) => a + b, 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Tips */}
      <Card className="bg-slate-900/50 border-white/[0.07] border-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-400" />
            Performance Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-800/50 border border-white/[0.07] border-700">
              <div className="p-2 rounded-lg bg-bw-green/[0.08]0/10 w-fit mb-3">
                <CheckCircle className="h-5 w-5 text-green-400" />
              </div>
              <h4 className="text-white font-medium mb-1">Stay Consistent</h4>
              <p className="text-sm text-slate-400">Aim to resolve at least 5 tickets daily to maintain your ranking.</p>
            </div>
            
            <div className="p-4 rounded-xl bg-slate-800/50 border border-white/[0.07] border-700">
              <div className="p-2 rounded-lg bg-amber-500/10 w-fit mb-3">
                <Clock className="h-5 w-5 text-amber-400" />
              </div>
              <h4 className="text-white font-medium mb-1">Quick Response</h4>
              <p className="text-sm text-slate-400">Start work on assigned tickets within 1 hour for better metrics.</p>
            </div>
            
            <div className="p-4 rounded-xl bg-slate-800/50 border border-white/[0.07] border-700">
              <div className="p-2 rounded-lg bg-bw-purple/[0.08]0/10 w-fit mb-3">
                <Target className="h-5 w-5 text-purple-400" />
              </div>
              <h4 className="text-white font-medium mb-1">Prioritize Critical</h4>
              <p className="text-sm text-slate-400">Focus on critical tickets first - they carry more weight in rankings.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

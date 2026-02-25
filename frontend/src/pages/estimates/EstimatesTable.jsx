/**
 * EstimatesTable — Main listing content, summary cards, funnel, and Ticket Estimates tab.
 * The Tabs wrapper is managed by the parent (index.jsx).
 * This component renders Estimates and Ticket-Estimates TabsContent.
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Plus, Search, Eye, Copy, FileDown, FileUp, ListChecks, Settings, Edit,
  LayoutTemplate, TrendingUp, ChevronRight, IndianRupee, FileText, Clock,
  CheckCircle, ArrowRightLeft, Ticket, AlertTriangle, Send, Package
} from "lucide-react";
import { EstimateStatusBadge } from "@/components/estimates";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";

export function EstimatesSummary({ summary, funnel, setStatusFilter, fetchEstimates }) {

  return (
    <>
      {/* Summary Cards */}
      {summary && (
        <StatCardGrid>
          <StatCard title="Total" value={summary.total || 0} icon={FileText} variant="default" />
          <StatCard title="Drafts" value={summary.by_status?.draft || 0} icon={Edit} variant="warning" />
          <StatCard title="Sent" value={summary.by_status?.sent || 0} icon={Send} variant="primary" />
          <StatCard title="Viewed" value={summary.by_status?.customer_viewed || 0} icon={Eye} variant="info"
            onClick={() => { setStatusFilter('customer_viewed'); fetchEstimates(); }}
            className="cursor-pointer hover:ring-2 hover:ring-cyan-300"
          />
          <StatCard title="Accepted" value={summary.by_status?.accepted || 0} icon={CheckCircle} variant="success" />
          <StatCard title="Expired" value={summary.by_status?.expired || 0} icon={Clock} variant="warning" />
          <StatCard title="Converted" value={summary.by_status?.converted || 0} icon={ArrowRightLeft} variant="purple" />
          <StatCard title="Total Value" value={formatCurrencyCompact(summary.total_value || 0)} icon={IndianRupee} variant="success" />
        </StatCardGrid>
      )}

      {/* Quick Actions Row */}
      <div className="flex flex-wrap justify-between items-center gap-2">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => handleExport("csv")} className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="export-csv-btn">
            <FileDown className="h-4 w-4" /> Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowImportDialog(true)} className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="import-btn">
            <FileUp className="h-4 w-4" /> Import
          </Button>
          {selectedIds.length > 0 && (
            <Button variant="outline" size="sm" onClick={() => setShowBulkActionDialog(true)} className="gap-2 bg-[rgba(59,158,255,0.08)] border-[rgba(59,158,255,0.25)] text-[#3B9EFF] hover:bg-[rgba(59,158,255,0.15)]" data-testid="bulk-action-btn">
              <ListChecks className="h-4 w-4" /> Bulk Actions ({selectedIds.length})
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => { fetchCustomFields(); setShowCustomFieldsDialog(true); }} className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="custom-fields-btn">
            <Edit className="h-4 w-4" /> Custom Fields
          </Button>
          <Button variant="outline" size="sm" onClick={() => { fetchPdfTemplates(); setShowTemplateDialog(true); }} className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="templates-btn">
            <LayoutTemplate className="h-4 w-4" /> Templates
          </Button>
          <Button variant="outline" size="sm" onClick={() => { fetchPreferences(); setShowPreferencesDialog(true); }} className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="preferences-btn">
            <Settings className="h-4 w-4" /> Preferences
          </Button>
        </div>
      </div>

      {/* Conversion Funnel */}
      {funnel && (
        <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)]">
          <CardHeader className="pb-2 border-b border-[rgba(255,255,255,0.07)]">
            <CardTitle className="text-sm flex items-center gap-2 text-[#F4F6F0]"><TrendingUp className="h-4 w-4 text-[#C8FF00]" /> Conversion Funnel</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between text-xs">
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Created</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.total_created}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-[rgba(255,255,255,0.15)]" />
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Sent</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.sent_to_customer}</p>
                <p className="text-[#3B9EFF] text-xs">{funnel.send_rate}%</p>
              </div>
              <ChevronRight className="h-4 w-4 text-[rgba(255,255,255,0.15)]" />
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Accepted</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.accepted}</p>
                <p className="text-[#C8FF00] text-xs">{funnel.acceptance_rate}%</p>
              </div>
              <ChevronRight className="h-4 w-4 text-[rgba(255,255,255,0.15)]" />
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Converted</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.converted}</p>
                <p className="text-[#8B5CF6] text-xs">{funnel.conversion_rate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-[#111820] border border-[rgba(255,255,255,0.07)] p-1">
          <TabsTrigger value="estimates" className="data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">Estimates</TabsTrigger>
          <TabsTrigger value="ticket-estimates" className="flex items-center gap-1 data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">
            <Ticket className="h-4 w-4" />
            Ticket Estimates ({ticketEstimates.length})
          </TabsTrigger>
          <TabsTrigger value="create" className="data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">Create New</TabsTrigger>
        </TabsList>

        {/* Estimates Tab */}
        <TabsContent value="estimates" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.25)]" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchEstimates()} placeholder="Search estimates..." className="pl-10 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.25)] focus:border-[#C8FF00]" data-testid="search-estimates" />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setTimeout(fetchEstimates, 100); }}>
                <SelectTrigger className="w-36 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0]"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#111820] border-[rgba(255,255,255,0.1)]">
                  <SelectItem value="all" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">All Status</SelectItem>
                  <SelectItem value="draft" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Draft</SelectItem>
                  <SelectItem value="sent" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Sent</SelectItem>
                  <SelectItem value="customer_viewed" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Viewed</SelectItem>
                  <SelectItem value="accepted" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Accepted</SelectItem>
                  <SelectItem value="declined" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Declined</SelectItem>
                  <SelectItem value="expired" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Expired</SelectItem>
                  <SelectItem value="converted" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Converted</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setActiveTab("create")} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2 rounded-[3px] hover:shadow-[0_0_20px_rgba(200,255,0,0.3)]" data-testid="new-estimate-btn">
              <Plus className="h-4 w-4" /> New Estimate
            </Button>
          </div>

          {loading ? (
            <TableSkeleton columns={8} rows={5} />
          ) : estimates.length === 0 ? (
            <Card className="bg-[#111820] border-[rgba(255,255,255,0.07)]">
              <EmptyState icon={FileText} title="No estimates found" description="Create your first estimate to start quoting customers." actionLabel="New Estimate" onAction={() => setActiveTab("create")} actionIcon={Plus} />
            </Card>
          ) : (
            <div className="bg-[#0D1317] border border-[rgba(255,255,255,0.07)] rounded">
              <ResponsiveTable>
                <thead className="bg-[#111820] border-b border-[rgba(255,255,255,0.07)]">
                  <tr>
                    <th className="px-2 py-3 text-center w-10">
                      <input type="checkbox" checked={selectedIds.length === estimates.length && estimates.length > 0} onChange={toggleSelectAll} className="h-4 w-4 rounded border-[rgba(255,255,255,0.2)] bg-transparent" onClick={(e) => e.stopPropagation()} />
                    </th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Estimate #</th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Customer</th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Date</th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Expiry</th>
                    <th className="px-4 py-3 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Amount</th>
                    <th className="px-4 py-3 text-center font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Status</th>
                    <th className="px-4 py-3 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {estimates.map(est => (
                    <tr key={est.estimate_id} className={`border-b border-[rgba(255,255,255,0.04)] hover:bg-[rgba(200,255,0,0.03)] cursor-pointer transition-colors ${selectedIds.includes(est.estimate_id) ? 'bg-[rgba(59,158,255,0.08)]' : ''}`} onClick={() => fetchEstimateDetail(est.estimate_id)} data-testid={`estimate-row-${est.estimate_id}`}>
                      <td className="px-2 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                        <input type="checkbox" checked={selectedIds.includes(est.estimate_id)} onChange={() => toggleSelect(est.estimate_id)} className="h-4 w-4 rounded border-[rgba(255,255,255,0.2)] bg-transparent" />
                      </td>
                      <td className="px-4 py-3 font-mono font-medium text-sm text-[#C8FF00] tracking-[0.06em]">{est.estimate_number}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-[#F4F6F0]">{est.customer_name}</td>
                      <td className="px-4 py-3 text-[rgba(244,246,240,0.45)] text-sm">{est.date}</td>
                      <td className="px-4 py-3 text-[rgba(244,246,240,0.45)] text-sm">{est.expiry_date}</td>
                      <td className="px-4 py-3 text-right font-bold text-sm text-[#C8FF00]">₹{(est.grand_total || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-center"><EstimateStatusBadge status={est.status} /></td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchEstimateDetail(est.estimate_id)} className="text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"><Eye className="h-4 w-4" /></Button>
                        <Button size="icon" variant="ghost" onClick={() => handleClone(est.estimate_id)} className="text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"><Copy className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </ResponsiveTable>
            </div>
          )}
        </TabsContent>

        {/* Ticket Estimates Tab */}
        <TabsContent value="ticket-estimates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Ticket className="h-5 w-5" /> Ticket-Linked Estimates</CardTitle>
              <CardDescription>Estimates created from service tickets. These are managed through the Job Card interface.</CardDescription>
            </CardHeader>
            <CardContent>
              {ticketEstimates.length === 0 ? (
                <EmptyState icon={Ticket} title="No Ticket Estimates" description="When estimates are created from service tickets, they'll appear here." />
              ) : (
                <div className="border rounded overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820] border-b">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium">Linked Ticket</th>
                        <th className="px-4 py-3 text-left font-medium">Estimate #</th>
                        <th className="px-4 py-3 text-left font-medium">Customer</th>
                        <th className="px-4 py-3 text-left font-medium">Vehicle</th>
                        <th className="px-4 py-3 text-right font-medium">Amount</th>
                        <th className="px-4 py-3 text-center font-medium">Status</th>
                        <th className="px-4 py-3 text-right font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ticketEstimates.map((est) => (
                        <tr key={est.estimate_id} className="border-b hover:bg-[rgba(59,158,255,0.04)] cursor-pointer" onClick={() => fetchEstimateDetail(est.estimate_id)}>
                          <td className="px-4 py-3">
                            <a href={`/tickets?id=${est.ticket_id}`} className="text-[#3B9EFF] hover:underline font-mono text-sm" onClick={(e) => e.stopPropagation()}>
                              {est.ticket_id?.slice(0, 12)}...
                            </a>
                          </td>
                          <td className="px-4 py-3 font-mono text-[#C8FF00]">{est.estimate_number}</td>
                          <td className="px-4 py-3 font-semibold">{est.customer_name}</td>
                          <td className="px-4 py-3 text-[rgba(244,246,240,0.45)]">{est.vehicle_number || '-'}</td>
                          <td className="px-4 py-3 text-right font-bold text-[#C8FF00]">₹{(est.grand_total || 0).toLocaleString('en-IN')}</td>
                          <td className="px-4 py-3 text-center"><EstimateStatusBadge status={est.status} /></td>
                          <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                            <Button size="sm" variant="ghost" onClick={() => window.open(`/tickets?id=${est.ticket_id}`, '_blank')} className="text-[#3B9EFF] hover:text-[#5BB0FF]">
                              Open Ticket
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => {
                              handleOpenEdit({
                                ...est,
                                is_ticket_estimate: true,
                              });
                            }}>
                              <Eye className="h-4 w-4 mr-1" /> View
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </>
  );
}

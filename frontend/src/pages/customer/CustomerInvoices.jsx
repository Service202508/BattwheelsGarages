import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { 
  FileText, Download, Eye, Calendar, CreditCard, 
  CheckCircle, Clock, AlertCircle
} from "lucide-react";
import { API } from "@/App";

export default function CustomerInvoices({ user }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/invoices`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setInvoices(data);
      }
    } catch (error) {
      console.error("Failed to fetch invoices:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInvoiceDetail = async (invoiceId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/invoices/${invoiceId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedInvoice(data);
      }
    } catch (error) {
      console.error("Failed to fetch invoice detail:", error);
    }
  };

  const getPaymentStatusConfig = (status) => {
    const configs = {
      paid: { color: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25", icon: CheckCircle, label: "Paid" },
      partial: { color: "bg-bw-orange/10 text-bw-orange", icon: Clock, label: "Partial" },
      pending: { color: "bg-bw-red/10 text-bw-red border border-bw-red/25", icon: AlertCircle, label: "Pending" }
    };
    return configs[status] || configs.pending;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customer-invoices">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-bw-white">Invoices</h1>
        <p className="text-bw-white/35">View and download your service invoices</p>
      </div>

      {/* Invoices List */}
      {invoices.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-16 w-16 mx-auto mb-4 text-bw-white/20" />
            <h3 className="text-lg font-semibold text-bw-white mb-2">No Invoices Yet</h3>
            <p className="text-bw-white/35">Your invoices will appear here after services are completed</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((invoice) => {
                  const statusConfig = getPaymentStatusConfig(invoice.payment_status);
                  const StatusIcon = statusConfig.icon;
                  
                  return (
                    <TableRow key={invoice.invoice_id}>
                      <TableCell className="font-mono font-medium">
                        {invoice.invoice_number}
                      </TableCell>
                      <TableCell>
                        {new Date(invoice.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{invoice.vehicle_number || "N/A"}</TableCell>
                      <TableCell className="font-semibold">
                        ₹{(invoice.total_amount || 0).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusConfig.color}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => fetchInvoiceDetail(invoice.invoice_id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Invoice Detail Dialog */}
      <Dialog open={!!selectedInvoice} onOpenChange={() => setSelectedInvoice(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedInvoice && (
            <>
              <DialogHeader>
                <DialogTitle>Invoice {selectedInvoice.invoice_number}</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6 py-4">
                {/* Invoice Header */}
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-xl text-bw-white">Battwheels OS</h3>
                    <p className="text-sm text-bw-white/35">EV Service & Repair Center</p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-lg font-bold">{selectedInvoice.invoice_number}</p>
                    <p className="text-sm text-bw-white/35">
                      {new Date(selectedInvoice.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Customer & Vehicle Info */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-bw-panel rounded-lg">
                  <div>
                    <p className="text-sm text-bw-white/[0.45]">Customer</p>
                    <p className="font-medium">{selectedInvoice.customer_name}</p>
                    <p className="text-sm text-bw-white/35">{selectedInvoice.customer_email}</p>
                  </div>
                  <div>
                    <p className="text-sm text-bw-white/[0.45]">Vehicle</p>
                    <p className="font-medium font-mono">{selectedInvoice.vehicle_number}</p>
                  </div>
                </div>

                {/* Items */}
                {selectedInvoice.items && selectedInvoice.items.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-3">Items & Services</h4>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Description</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead className="text-right">Price</TableHead>
                          <TableHead className="text-right">Total</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedInvoice.items.map((item, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{item.name}</TableCell>
                            <TableCell className="text-right">{item.quantity || 1}</TableCell>
                            <TableCell className="text-right">₹{(item.unit_price || 0).toLocaleString()}</TableCell>
                            <TableCell className="text-right font-medium">
                              ₹{((item.unit_price || 0) * (item.quantity || 1)).toLocaleString()}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {/* Totals */}
                <div className="border-t pt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-bw-white/35">Subtotal</span>
                    <span>₹{(selectedInvoice.subtotal || 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-bw-white/35">Tax (GST)</span>
                    <span>₹{(selectedInvoice.tax_amount || 0).toLocaleString()}</span>
                  </div>
                  {selectedInvoice.discount_amount > 0 && (
                    <div className="flex justify-between text-sm text-green-600">
                      <span>Discount</span>
                      <span>-₹{selectedInvoice.discount_amount.toLocaleString()}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-lg font-bold pt-2 border-t">
                    <span>Total</span>
                    <span>₹{(selectedInvoice.total_amount || 0).toLocaleString()}</span>
                  </div>
                </div>

                {/* Payment Status */}
                <div className={`p-4 rounded-lg ${
                  selectedInvoice.payment_status === 'paid' 
                    ? 'bg-bw-green/[0.08] border border-green-200' 
                    : 'bg-bw-orange/[0.08] border border-orange-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CreditCard className={`h-5 w-5 ${
                        selectedInvoice.payment_status === 'paid' ? 'text-green-600' : 'text-bw-orange'
                      }`} />
                      <span className="font-medium">
                        {selectedInvoice.payment_status === 'paid' ? 'Payment Complete' : 'Payment Pending'}
                      </span>
                    </div>
                    {selectedInvoice.payment_status !== 'paid' && (
                      <span className="font-bold text-bw-orange">
                        Balance: ₹{((selectedInvoice.total_amount || 0) - (selectedInvoice.amount_paid || 0)).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => window.print()}>
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </Button>
                  {selectedInvoice.payment_status !== 'paid' && (
                    <Button className="flex-1 bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold">
                      <CreditCard className="h-4 w-4 mr-2" />
                      Pay Now
                    </Button>
                  )}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

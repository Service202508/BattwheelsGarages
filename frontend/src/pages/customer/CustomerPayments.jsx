import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  CreditCard, AlertCircle, Calendar, Car, FileText, 
  ArrowRight, Banknote, Clock
} from "lucide-react";
import { API } from "@/App";

export default function CustomerPayments({ user }) {
  const [paymentsData, setPaymentsData] = useState({ payments: [], total_due: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/payments-due`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setPaymentsData(data);
      }
    } catch (error) {
      console.error("Failed to fetch payments:", error);
    } finally {
      setLoading(false);
    }
  };

  const isOverdue = (dueDate) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customer-payments">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#F4F6F0]">Payments Due</h1>
        <p className="text-[rgba(244,246,240,0.35)]">View and manage your outstanding payments</p>
      </div>

      {/* Summary Card */}
      <Card className={paymentsData.total_due > 0 ? "border-orange-200 bg-[rgba(255,140,0,0.08)]" : "bg-[rgba(34,197,94,0.08)] border-green-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-4 rounded-2xl ${paymentsData.total_due > 0 ? 'bg-[rgba(255,140,0,0.10)]' : 'bg-[rgba(34,197,94,0.10)]'}`}>
                <CreditCard className={`h-8 w-8 ${paymentsData.total_due > 0 ? 'text-[#FF8C00]' : 'text-green-600'}`} />
              </div>
              <div>
                <p className="text-sm text-[rgba(244,246,240,0.35)]">Total Outstanding</p>
                <p className={`text-3xl font-bold ${paymentsData.total_due > 0 ? 'text-[#FF8C00]' : 'text-green-600'}`}>
                  ₹{paymentsData.total_due.toLocaleString()}
                </p>
              </div>
            </div>
            {paymentsData.total_due > 0 && (
              <Button className="bg-orange-600 hover:bg-orange-700">
                Pay All
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Payment Instructions */}
      {paymentsData.total_due > 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Banknote className="h-5 w-5 text-[#3B9EFF] mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">Payment Options</h4>
                <ul className="text-sm text-blue-800 mt-1 space-y-1">
                  <li>• UPI: <span className="font-mono">battwheels@kotak</span></li>
                  <li>• Pay at workshop counter</li>
                  <li>• Online payment coming soon</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payments List */}
      {paymentsData.payments.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <CreditCard className="h-16 w-16 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
            <h3 className="text-lg font-semibold text-[#F4F6F0] mb-2">No Pending Payments</h3>
            <p className="text-[rgba(244,246,240,0.35)]">All your invoices are paid. Great job! 🎉</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {paymentsData.payments.map((payment) => {
            const overdue = isOverdue(payment.due_date);
            
            return (
              <Card 
                key={payment.invoice_id}
                className={`overflow-hidden ${overdue ? 'border-red-200' : 'border-orange-200'}`}
              >
                {overdue && (
                  <div className="bg-[rgba(255,59,47,0.08)]0 text-white text-xs font-medium px-4 py-1">
                    <AlertCircle className="h-3 w-3 inline mr-1" />
                    OVERDUE
                  </div>
                )}
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                        <span className="font-mono font-medium">{payment.invoice_number}</span>
                        <Badge variant="outline" className={overdue ? "border-red-200 text-red-600" : "border-orange-200 text-[#FF8C00]"}>
                          {payment.status}
                        </Badge>
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-[rgba(244,246,240,0.35)]">
                        {payment.vehicle_number && (
                          <span className="flex items-center gap-1">
                            <Car className="h-4 w-4" />
                            {payment.vehicle_number}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          Issued: {new Date(payment.created_at).toLocaleDateString()}
                        </span>
                        {payment.due_date && (
                          <span className={`flex items-center gap-1 ${overdue ? 'text-red-600 font-medium' : ''}`}>
                            <Clock className="h-4 w-4" />
                            Due: {new Date(payment.due_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-sm text-[rgba(244,246,240,0.45)]">Balance Due</p>
                      <p className={`text-2xl font-bold ${overdue ? 'text-red-600' : 'text-[#FF8C00]'}`}>
                        ₹{payment.balance_due.toLocaleString()}
                      </p>
                      {payment.amount_paid > 0 && (
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">
                          Paid: ₹{payment.amount_paid.toLocaleString()} / ₹{payment.amount.toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4 pt-4 border-t">
                    <Button variant="outline" size="sm" className="flex-1">
                      <FileText className="h-4 w-4 mr-2" />
                      View Invoice
                    </Button>
                    <Button 
                      size="sm" 
                      className={`flex-1 ${overdue ? 'bg-red-600 hover:bg-red-700' : 'bg-orange-600 hover:bg-orange-700'}`}
                    >
                      <CreditCard className="h-4 w-4 mr-2" />
                      Pay ₹{payment.balance_due.toLocaleString()}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

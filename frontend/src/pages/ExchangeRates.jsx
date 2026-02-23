import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { 
  Plus, RefreshCw, Loader2, ArrowRightLeft, 
  TrendingUp, TrendingDown, Globe, Calendar
} from "lucide-react";
import { API } from "@/App";

// Common currencies with their symbols
const CURRENCIES = [
  { code: "INR", name: "Indian Rupee", symbol: "₹" },
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "€" },
  { code: "GBP", name: "British Pound", symbol: "£" },
  { code: "AED", name: "UAE Dirham", symbol: "د.إ" },
  { code: "SGD", name: "Singapore Dollar", symbol: "S$" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$" },
  { code: "JPY", name: "Japanese Yen", symbol: "¥" },
  { code: "CNY", name: "Chinese Yuan", symbol: "¥" },
  { code: "CHF", name: "Swiss Franc", symbol: "CHF" },
  { code: "SAR", name: "Saudi Riyal", symbol: "﷼" }
];

export default function ExchangeRates() {
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [fromCurrencyFilter, setFromCurrencyFilter] = useState("");
  
  const [formData, setFormData] = useState({
    from_currency: "USD",
    to_currency: "INR",
    rate: 83.50,
    effective_date: new Date().toISOString().split('T')[0]
  });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchRates();
  }, [fromCurrencyFilter]);

  const fetchRates = async () => {
    setLoading(true);
    try {
      const url = `${API}/zoho/settings/exchange-rates${fromCurrencyFilter ? `?from_currency=${fromCurrencyFilter}` : ''}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setRates(data.exchange_rates || []);
    } catch (error) {
      console.error("Error fetching exchange rates:", error);
      toast.error("Failed to load exchange rates");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.from_currency || !formData.to_currency || !formData.rate || !formData.effective_date) {
      toast.error("Please fill all required fields");
      return;
    }

    if (formData.from_currency === formData.to_currency) {
      toast.error("From and To currencies must be different");
      return;
    }

    try {
      const res = await fetch(`${API}/zoho/settings/exchange-rates`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Exchange rate set successfully");
        setDialogOpen(false);
        fetchRates();
        resetForm();
      } else {
        toast.error(data.message || "Failed to set exchange rate");
      }
    } catch (error) {
      toast.error("Failed to set exchange rate");
    }
  };

  const resetForm = () => {
    setFormData({
      from_currency: "USD",
      to_currency: "INR",
      rate: 83.50,
      effective_date: new Date().toISOString().split('T')[0]
    });
  };

  const getCurrencySymbol = (code) => {
    return CURRENCIES.find(c => c.code === code)?.symbol || code;
  };

  const getCurrencyName = (code) => {
    return CURRENCIES.find(c => c.code === code)?.name || code;
  };

  // Group rates by currency pair for latest rate display
  const latestRates = rates.reduce((acc, rate) => {
    const key = `${rate.from_currency}-${rate.to_currency}`;
    if (!acc[key] || rate.effective_date > acc[key].effective_date) {
      acc[key] = rate;
    }
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="exchange-rates-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Exchange Rates</h1>
          <p className="text-gray-500 text-sm mt-1">Manage currency exchange rates for multi-currency transactions</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={fromCurrencyFilter || "all"} onValueChange={(v) => setFromCurrencyFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-40" data-testid="currency-filter">
              <SelectValue placeholder="All Currencies" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Currencies</SelectItem>
              {CURRENCIES.map(c => (
                <SelectItem key={c.code} value={c.code}>
                  {c.code} - {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={fetchRates}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold" data-testid="new-rate-btn">
                <Plus className="h-4 w-4 mr-2" /> Add Rate
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Set Exchange Rate</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-5 gap-4 items-end">
                  <div className="col-span-2 space-y-2">
                    <Label>From Currency *</Label>
                    <Select 
                      value={formData.from_currency} 
                      onValueChange={(v) => setFormData({...formData, from_currency: v})}
                    >
                      <SelectTrigger data-testid="from-currency-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CURRENCIES.map(c => (
                          <SelectItem key={c.code} value={c.code}>
                            {c.symbol} {c.code}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex justify-center pb-2">
                    <ArrowRightLeft className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="col-span-2 space-y-2">
                    <Label>To Currency *</Label>
                    <Select 
                      value={formData.to_currency} 
                      onValueChange={(v) => setFormData({...formData, to_currency: v})}
                    >
                      <SelectTrigger data-testid="to-currency-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CURRENCIES.map(c => (
                          <SelectItem key={c.code} value={c.code}>
                            {c.symbol} {c.code}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="bg-[#111820] p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-500 mb-2">Exchange Rate Preview</p>
                  <p className="text-lg font-semibold">
                    1 {getCurrencySymbol(formData.from_currency)} = {formData.rate} {getCurrencySymbol(formData.to_currency)}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Rate *</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={formData.rate}
                      onChange={(e) => setFormData({...formData, rate: parseFloat(e.target.value) || 0})}
                      data-testid="rate-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Effective Date *</Label>
                    <Input
                      type="date"
                      value={formData.effective_date}
                      onChange={(e) => setFormData({...formData, effective_date: e.target.value})}
                      data-testid="effective-date-input"
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold" data-testid="save-rate-btn">
                  Save Rate
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Current Rates Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.values(latestRates).slice(0, 4).map((rate) => (
          <Card key={rate.exchange_rate_id} className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-2">
                <Badge className="bg-blue-100 text-blue-800">{rate.from_currency}/{rate.to_currency}</Badge>
                <Globe className="h-4 w-4 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-blue-900">
                {getCurrencySymbol(rate.to_currency)}{rate.rate.toFixed(4)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                1 {rate.from_currency} • Effective: {rate.effective_date}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Exchange Rate History</CardTitle>
          <CardDescription>All exchange rates sorted by effective date</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
            </div>
          ) : rates.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <ArrowRightLeft className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No exchange rates configured</p>
              <p className="text-sm">Add exchange rates for multi-currency support</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#111820]">
                  <TableHead>From</TableHead>
                  <TableHead></TableHead>
                  <TableHead>To</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead>Effective Date</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rates.map((rate) => (
                  <TableRow key={rate.exchange_rate_id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">{rate.from_currency}</span>
                        <span className="text-gray-500 text-sm">{getCurrencyName(rate.from_currency)}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <ArrowRightLeft className="h-4 w-4 text-gray-400" />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">{rate.to_currency}</span>
                        <span className="text-gray-500 text-sm">{getCurrencyName(rate.to_currency)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono font-semibold text-lg">{rate.rate.toFixed(4)}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        {rate.effective_date}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {rate.created_time ? new Date(rate.created_time).toLocaleDateString() : "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

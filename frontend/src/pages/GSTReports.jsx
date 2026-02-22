import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { 
  FileText, Download, RefreshCw, FileSpreadsheet, Loader2, 
  CheckCircle, AlertCircle, Building2, Calculator, Receipt
} from "lucide-react";
import { API } from "@/App";

export default function GSTReports() {
  const [activeTab, setActiveTab] = useState("gstr1");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(
    new Date().toISOString().slice(0, 7) // YYYY-MM format
  );
  
  // Report data
  const [gstr1Data, setGstr1Data] = useState(null);
  const [gstr3bData, setGstr3bData] = useState(null);
  const [hsnSummary, setHsnSummary] = useState(null);
  const [orgSettings, setOrgSettings] = useState(null);
  
  // Settings dialog
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [gstinInput, setGstinInput] = useState("");
  const [stateInput, setStateInput] = useState("27");
  const [gstinValid, setGstinValid] = useState(null);
  
  // Indian states
  const [indianStates, setIndianStates] = useState([]);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchIndianStates();
    fetchOrgSettings();
  }, []);

  useEffect(() => {
    fetchActiveReport();
  }, [activeTab, selectedMonth]);

  const fetchIndianStates = async () => {
    try {
      const res = await fetch(`${API}/gst/states`, { headers });
      const data = await res.json();
      setIndianStates(data.states || []);
    } catch (error) {
      console.error("Failed to fetch states:", error);
    }
  };

  const fetchOrgSettings = async () => {
    try {
      const res = await fetch(`${API}/gst/organization-settings`, { headers });
      const data = await res.json();
      setOrgSettings(data.settings);
      setGstinInput(data.settings?.gstin || "");
      setStateInput(data.settings?.place_of_supply || "27");
    } catch (error) {
      console.error("Failed to fetch org settings:", error);
    }
  };

  const fetchActiveReport = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case "gstr1":
          await fetchGSTR1();
          break;
        case "gstr3b":
          await fetchGSTR3B();
          break;
        case "hsn":
          await fetchHSNSummary();
          break;
      }
    } catch (error) {
      console.error("Failed to fetch report:", error);
      toast.error("Error loading report");
    } finally {
      setLoading(false);
    }
  };

  const fetchGSTR1 = async () => {
    const res = await fetch(`${API}/gst/gstr1?month=${selectedMonth}`, { headers });
    const data = await res.json();
    setGstr1Data(data);
  };

  const fetchGSTR3B = async () => {
    const res = await fetch(`${API}/gst/gstr3b?month=${selectedMonth}`, { headers });
    const data = await res.json();
    setGstr3bData(data);
  };

  const fetchHSNSummary = async () => {
    const res = await fetch(`${API}/gst/hsn-summary?month=${selectedMonth}`, { headers });
    const data = await res.json();
    setHsnSummary(data);
  };

  const validateGSTIN = async () => {
    try {
      const res = await fetch(`${API}/gst/validate-gstin`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ gstin: gstinInput })
      });
      const data = await res.json();
      setGstinValid(data.valid);
      if (data.valid) {
        toast.success(`Valid GSTIN - ${data.state_name}`);
      } else {
        toast.error(data.error || "Invalid GSTIN");
      }
    } catch (error) {
      toast.error("GSTIN validation failed");
    }
  };

  const saveOrgSettings = async () => {
    try {
      const res = await fetch(`${API}/gst/organization-settings`, {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          gstin: gstinInput,
          place_of_supply: stateInput,
          legal_name: orgSettings?.legal_name || "",
          trade_name: orgSettings?.trade_name || ""
        })
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("GST settings saved");
        setSettingsOpen(false);
        fetchOrgSettings();
      }
    } catch (error) {
      toast.error("Failed to save settings");
    }
  };

  const exportReport = async (format) => {
    setExporting(true);
    try {
      let url = "";
      let filename = "";
      
      switch (activeTab) {
        case "gstr1":
          url = `${API}/gst/gstr1?month=${selectedMonth}&format=${format}`;
          filename = `gstr1_${selectedMonth}`;
          break;
        case "gstr3b":
          url = `${API}/gst/gstr3b?month=${selectedMonth}&format=${format}`;
          filename = `gstr3b_${selectedMonth}`;
          break;
        case "hsn":
          url = `${API}/gst/hsn-summary?month=${selectedMonth}&format=excel`;
          filename = `hsn_summary_${selectedMonth}`;
          break;
      }

      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error("Export failed");
      
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${filename}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error("Export failed:", error);
      toast.error("Failed to export report");
    } finally {
      setExporting(false);
    }
  };

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const getMonthOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      options.push({
        value: d.toISOString().slice(0, 7),
        label: d.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
      });
    }
    return options;
  };

  return (
    <div className="space-y-6" data-testid="gst-reports-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">GST Reports</h1>
          <p className="text-gray-500 text-sm mt-1">
            GSTR-1, GSTR-3B, and HSN Summary for GST filing
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" data-testid="gst-settings-btn">
                <Building2 className="h-4 w-4 mr-2" />
                GST Settings
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Organization GST Settings</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>GSTIN</Label>
                  <div className="flex gap-2">
                    <Input
                      value={gstinInput}
                      onChange={(e) => {
                        setGstinInput(e.target.value.toUpperCase());
                        setGstinValid(null);
                      }}
                      placeholder="27AAACT1234A1ZB"
                      maxLength={15}
                      data-testid="gstin-input"
                    />
                    <Button variant="outline" onClick={validateGSTIN}>
                      Validate
                    </Button>
                  </div>
                  {gstinValid !== null && (
                    <div className={`flex items-center gap-2 text-sm ${gstinValid ? 'text-green-600' : 'text-red-600'}`}>
                      {gstinValid ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                      {gstinValid ? 'Valid GSTIN' : 'Invalid GSTIN format'}
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Place of Supply (State)</Label>
                  <Select value={stateInput} onValueChange={setStateInput}>
                    <SelectTrigger data-testid="state-select">
                      <SelectValue placeholder="Select State" />
                    </SelectTrigger>
                    <SelectContent>
                      {indianStates.map(state => (
                        <SelectItem key={state.code} value={state.code}>
                          {state.code} - {state.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setSettingsOpen(false)}>Cancel</Button>
                <Button onClick={saveOrgSettings} data-testid="save-gst-settings-btn">Save Settings</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Current GSTIN Display */}
      {orgSettings?.gstin && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">
                GSTIN: {orgSettings.gstin}
              </Badge>
              <span className="text-sm text-gray-600">
                State: {indianStates.find(s => s.code === orgSettings.place_of_supply)?.name || orgSettings.place_of_supply}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 h-auto">
          <TabsTrigger value="gstr1" className="py-2" data-testid="gstr1-tab">
            <Receipt className="h-4 w-4 mr-2" />
            GSTR-1
          </TabsTrigger>
          <TabsTrigger value="gstr3b" className="py-2" data-testid="gstr3b-tab">
            <Calculator className="h-4 w-4 mr-2" />
            GSTR-3B
          </TabsTrigger>
          <TabsTrigger value="hsn" className="py-2" data-testid="hsn-tab">
            <FileText className="h-4 w-4 mr-2" />
            HSN Summary
          </TabsTrigger>
        </TabsList>

        {/* GSTR-1 Tab */}
        <TabsContent value="gstr1" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>GSTR-1 - Outward Supplies</CardTitle>
                  <CardDescription>Details of outward supplies (sales invoices)</CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                    <SelectTrigger className="w-48" data-testid="month-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getMonthOptions().map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={fetchActiveReport} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button onClick={() => exportReport("pdf")} variant="outline" size="sm" disabled={exporting} data-testid="export-gstr1-pdf">
                    {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  </Button>
                  <Button onClick={() => exportReport("excel")} variant="outline" size="sm" disabled={exporting} data-testid="export-gstr1-excel">
                    {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : gstr1Data && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-blue-700 font-medium">Total Invoices</p>
                        <p className="text-2xl font-bold text-blue-800">{gstr1Data.grand_total?.total_invoices || 0}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-green-50 border-green-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-green-700 font-medium">Taxable Value</p>
                        <p className="text-xl font-bold text-green-800">{formatCurrency(gstr1Data.grand_total?.taxable_value)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-orange-50 border-orange-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-orange-700 font-medium">CGST + SGST</p>
                        <p className="text-xl font-bold text-orange-800">{formatCurrency((gstr1Data.grand_total?.cgst || 0) + (gstr1Data.grand_total?.sgst || 0))}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-purple-50 border-purple-200">
                      <CardContent className="p-4">
                        <p className="text-xs text-purple-700 font-medium">IGST</p>
                        <p className="text-xl font-bold text-purple-800">{formatCurrency(gstr1Data.grand_total?.igst)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* B2B Section */}
                  <div>
                    <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <Badge className="bg-blue-100 text-blue-800">B2B</Badge>
                      Registered Business Invoices ({gstr1Data.b2b?.summary?.count || 0})
                    </h3>
                    <div className="border rounded-lg overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-gray-50">
                            <TableHead>Invoice #</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead>Customer</TableHead>
                            <TableHead>GSTIN</TableHead>
                            <TableHead className="text-right">Taxable</TableHead>
                            <TableHead className="text-right">CGST</TableHead>
                            <TableHead className="text-right">SGST</TableHead>
                            <TableHead className="text-right">IGST</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {gstr1Data.b2b?.invoices?.slice(0, 10).map((inv, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{inv.invoice_number}</TableCell>
                              <TableCell>{inv.invoice_date}</TableCell>
                              <TableCell>{inv.customer_name?.slice(0, 25)}</TableCell>
                              <TableCell className="font-mono text-xs">{inv.customer_gstin}</TableCell>
                              <TableCell className="text-right">{formatCurrency(inv.taxable_value)}</TableCell>
                              <TableCell className="text-right">{formatCurrency(inv.cgst)}</TableCell>
                              <TableCell className="text-right">{formatCurrency(inv.sgst)}</TableCell>
                              <TableCell className="text-right">{formatCurrency(inv.igst)}</TableCell>
                            </TableRow>
                          ))}
                          <TableRow className="bg-blue-50 font-semibold">
                            <TableCell colSpan={4}>Total B2B</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr1Data.b2b?.summary?.taxable_value)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr1Data.b2b?.summary?.cgst)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr1Data.b2b?.summary?.sgst)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr1Data.b2b?.summary?.igst)}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </div>
                  </div>

                  {/* B2C Summary */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="py-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Badge className="bg-green-100 text-green-800">B2C Large</Badge>
                          Inter-state &gt; ₹2.5L
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex justify-between"><span className="text-gray-600">Count:</span><span className="font-medium">{gstr1Data.b2c_large?.summary?.count || 0}</span></div>
                          <div className="flex justify-between"><span className="text-gray-600">Taxable:</span><span className="font-medium">{formatCurrency(gstr1Data.b2c_large?.summary?.taxable_value)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-600">IGST:</span><span className="font-medium">{formatCurrency(gstr1Data.b2c_large?.summary?.igst)}</span></div>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="py-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Badge className="bg-orange-100 text-orange-800">B2C Small</Badge>
                          Other B2C
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex justify-between"><span className="text-gray-600">Count:</span><span className="font-medium">{gstr1Data.b2c_small?.summary?.count || 0}</span></div>
                          <div className="flex justify-between"><span className="text-gray-600">Taxable:</span><span className="font-medium">{formatCurrency(gstr1Data.b2c_small?.summary?.taxable_value)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-600">CGST:</span><span className="font-medium">{formatCurrency(gstr1Data.b2c_small?.summary?.cgst)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-600">SGST:</span><span className="font-medium">{formatCurrency(gstr1Data.b2c_small?.summary?.sgst)}</span></div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* GSTR-3B Tab */}
        <TabsContent value="gstr3b" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>GSTR-3B - Summary Return</CardTitle>
                  <CardDescription>Monthly summary of GST liability and ITC</CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getMonthOptions().map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={fetchActiveReport} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button onClick={() => exportReport("pdf")} variant="outline" size="sm" disabled={exporting} data-testid="export-gstr3b-pdf">
                    <FileText className="h-4 w-4" />
                  </Button>
                  <Button onClick={() => exportReport("excel")} variant="outline" size="sm" disabled={exporting} data-testid="export-gstr3b-excel">
                    <FileSpreadsheet className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : gstr3bData && (
                <div className="space-y-6">
                  {/* Net Tax Payable Highlight */}
                  <Card className="bg-[#22EDA9]/10 border-[#22EDA9]">
                    <CardContent className="py-6">
                      <div className="text-center">
                        <p className="text-sm text-gray-600 mb-1">Net Tax Payable</p>
                        <p className="text-4xl font-bold text-[#F4F6F0]">{formatCurrency(gstr3bData.summary?.net_tax_payable)}</p>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Section 3.1 - Outward Supplies */}
                  <Card>
                    <CardHeader className="py-3 bg-gray-50">
                      <CardTitle className="text-base">3.1 Outward Supplies (Sales)</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Description</TableHead>
                            <TableHead className="text-right">Taxable Value</TableHead>
                            <TableHead className="text-right">CGST</TableHead>
                            <TableHead className="text-right">SGST</TableHead>
                            <TableHead className="text-right">IGST</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <TableRow>
                            <TableCell>Outward taxable supplies</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.taxable_value)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.cgst)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.sgst)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.igst)}</TableCell>
                          </TableRow>
                          <TableRow className="bg-gray-50 font-semibold">
                            <TableCell>Total Output Tax</TableCell>
                            <TableCell></TableCell>
                            <TableCell colSpan={3} className="text-right">
                              {formatCurrency(gstr3bData.section_3_1?.total_tax)}
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  {/* Section 4 - ITC */}
                  <Card>
                    <CardHeader className="py-3 bg-green-50">
                      <CardTitle className="text-base text-green-800">4. Eligible ITC (Input Tax Credit)</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Description</TableHead>
                            <TableHead className="text-right">CGST</TableHead>
                            <TableHead className="text-right">SGST</TableHead>
                            <TableHead className="text-right">IGST</TableHead>
                            <TableHead className="text-right">Total</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <TableRow>
                            <TableCell>Input Tax Credit (from purchases)</TableCell>
                            <TableCell className="text-right text-green-700">{formatCurrency(gstr3bData.section_4?.cgst)}</TableCell>
                            <TableCell className="text-right text-green-700">{formatCurrency(gstr3bData.section_4?.sgst)}</TableCell>
                            <TableCell className="text-right text-green-700">{formatCurrency(gstr3bData.section_4?.igst)}</TableCell>
                            <TableCell className="text-right font-semibold text-green-700">{formatCurrency(gstr3bData.section_4?.total_itc)}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  {/* Section 6 - Payment */}
                  <Card>
                    <CardHeader className="py-3 bg-orange-50">
                      <CardTitle className="text-base text-orange-800">6.1 Payment of Tax</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Tax Type</TableHead>
                            <TableHead className="text-right">Output Tax</TableHead>
                            <TableHead className="text-right">ITC Used</TableHead>
                            <TableHead className="text-right">Net Payable</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <TableRow>
                            <TableCell>CGST</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.cgst)}</TableCell>
                            <TableCell className="text-right text-green-600">{formatCurrency(gstr3bData.section_4?.cgst)}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(gstr3bData.section_6?.net_cgst)}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>SGST</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.sgst)}</TableCell>
                            <TableCell className="text-right text-green-600">{formatCurrency(gstr3bData.section_4?.sgst)}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(gstr3bData.section_6?.net_sgst)}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>IGST</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.igst)}</TableCell>
                            <TableCell className="text-right text-green-600">{formatCurrency(gstr3bData.section_4?.igst)}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(gstr3bData.section_6?.net_igst)}</TableCell>
                          </TableRow>
                          <TableRow className="bg-[#22EDA9] font-bold">
                            <TableCell>TOTAL</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_3_1?.total_tax)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_4?.total_itc)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(gstr3bData.section_6?.total_liability)}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* HSN Summary Tab */}
        <TabsContent value="hsn" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>HSN-wise Summary</CardTitle>
                  <CardDescription>Summary of outward supplies by HSN/SAC code</CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getMonthOptions().map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={fetchActiveReport} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button onClick={() => exportReport("excel")} variant="outline" size="sm" disabled={exporting} data-testid="export-hsn-excel">
                    <FileSpreadsheet className="h-4 w-4 mr-2" /> Export
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : hsnSummary && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead>HSN/SAC</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-center">UQC</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Taxable Value</TableHead>
                        <TableHead className="text-right">CGST</TableHead>
                        <TableHead className="text-right">SGST</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {hsnSummary.hsn_summary?.map((item, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono font-medium">{item.hsn_code}</TableCell>
                          <TableCell>{item.description?.slice(0, 30)}</TableCell>
                          <TableCell className="text-center">{item.uqc}</TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right">{formatCurrency(item.taxable_value)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(item.cgst)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(item.sgst)}</TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-[#22EDA9]/20 font-bold">
                        <TableCell colSpan={4}>TOTAL</TableCell>
                        <TableCell className="text-right">{formatCurrency(hsnSummary.total?.taxable_value)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(hsnSummary.total?.cgst)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(hsnSummary.total?.sgst)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Plus, BookOpen, Calendar, ArrowLeftRight, Trash2 } from "lucide-react";
import { API } from "@/App";

export default function JournalEntries() {
  const [journals, setJournals] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const [newJournal, setNewJournal] = useState({
    reference_number: "", notes: "", line_items: []
  });
  const [newLine, setNewLine] = useState({ account_id: "", account_name: "", debit: 0, credit: 0, description: "" });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [journalsRes, accountsRes] = await Promise.all([
        fetch(`${API}/zoho/journals?per_page=100`, { headers }),
        fetch(`${API}/zoho/chartofaccounts`, { headers })
      ]);
      const [journalsData, accountsData] = await Promise.all([journalsRes.json(), accountsRes.json()]);
      setJournals(journalsData.journals || []);
      setAccounts(accountsData.chartofaccounts || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleAddLine = () => {
    if (!newLine.account_id) return toast.error("Select an account");
    if (newLine.debit === 0 && newLine.credit === 0) return toast.error("Enter debit or credit amount");
    if (newLine.debit > 0 && newLine.credit > 0) return toast.error("Entry can have either debit or credit, not both");
    setNewJournal({ ...newJournal, line_items: [...newJournal.line_items, { ...newLine }] });
    setNewLine({ account_id: "", account_name: "", debit: 0, credit: 0, description: "" });
  };

  const totalDebit = newJournal.line_items.reduce((sum, l) => sum + (l.debit || 0), 0);
  const totalCredit = newJournal.line_items.reduce((sum, l) => sum + (l.credit || 0), 0);
  const isBalanced = totalDebit === totalCredit && totalDebit > 0;

  const handleCreate = async () => {
    if (!newJournal.line_items.length) return toast.error("Add at least one entry");
    if (!isBalanced) return toast.error("Debits must equal Credits");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/journals`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newJournal)
      });
      if (res.ok) {
        toast.success("Journal entry created");
        setShowCreateDialog(false);
        setNewJournal({ reference_number: "", notes: "", line_items: [] });
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Error creating journal");
      }
    } catch { toast.error("Error creating journal entry"); }
  };

  return (
    <div className="space-y-6" data-testid="journal-entries-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Journal Entries</h1>
          <p className="text-gray-500 text-sm mt-1">Manual accounting entries</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black" data-testid="create-journal-btn">
              <Plus className="h-4 w-4 mr-2" /> New Journal Entry
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Create Journal Entry</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Reference Number</Label>
                  <Input value={newJournal.reference_number} onChange={(e) => setNewJournal({ ...newJournal, reference_number: e.target.value })} placeholder="Optional reference" />
                </div>
                <div>
                  <Label>Notes</Label>
                  <Input value={newJournal.notes} onChange={(e) => setNewJournal({ ...newJournal, notes: e.target.value })} placeholder="Journal description" />
                </div>
              </div>

              <div className="border rounded-lg p-4 bg-gray-50">
                <h3 className="font-medium mb-3">Add Entry Line</h3>
                <div className="grid grid-cols-5 gap-3">
                  <div className="col-span-2">
                    <Select onValueChange={(v) => {
                      const acc = accounts.find(a => a.account_id === v);
                      if (acc) setNewLine({ ...newLine, account_id: acc.account_id, account_name: acc.account_name });
                    }}>
                      <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                      <SelectContent>
                        {accounts.map(a => <SelectItem key={a.account_id} value={a.account_id}>{a.account_name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <Input type="number" value={newLine.debit || ""} onChange={(e) => setNewLine({ ...newLine, debit: parseFloat(e.target.value) || 0 })} placeholder="Debit" />
                  <Input type="number" value={newLine.credit || ""} onChange={(e) => setNewLine({ ...newLine, credit: parseFloat(e.target.value) || 0 })} placeholder="Credit" />
                  <Button onClick={handleAddLine} className="bg-[#22EDA9] text-black">Add</Button>
                </div>
              </div>

              {newJournal.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left">Account</th>
                        <th className="px-3 py-2 text-right">Debit</th>
                        <th className="px-3 py-2 text-right">Credit</th>
                        <th className="px-3 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {newJournal.line_items.map((line, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{line.account_name}</td>
                          <td className="px-3 py-2 text-right">{line.debit > 0 ? `₹${line.debit.toLocaleString('en-IN')}` : '-'}</td>
                          <td className="px-3 py-2 text-right">{line.credit > 0 ? `₹${line.credit.toLocaleString('en-IN')}` : '-'}</td>
                          <td className="px-3 py-2">
                            <Button variant="ghost" size="icon" onClick={() => setNewJournal({ ...newJournal, line_items: newJournal.line_items.filter((_, i) => i !== idx) })}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className={`font-semibold ${isBalanced ? 'bg-green-50' : 'bg-red-50'}`}>
                      <tr>
                        <td className="px-3 py-2 text-right">Total:</td>
                        <td className="px-3 py-2 text-right">₹{totalDebit.toLocaleString('en-IN')}</td>
                        <td className="px-3 py-2 text-right">₹{totalCredit.toLocaleString('en-IN')}</td>
                        <td className="px-3 py-2">
                          {isBalanced ? <Badge className="bg-green-100 text-green-700">Balanced</Badge> : <Badge className="bg-red-100 text-red-700">Unbalanced</Badge>}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreate} className="bg-[#22EDA9] text-black" disabled={!isBalanced}>Create Entry</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        journals.length === 0 ? <Card><CardContent className="py-12 text-center text-gray-500">No journal entries found</CardContent></Card> :
        <div className="space-y-3">
          {journals.map(journal => (
            <Card key={journal.journal_id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-5 w-5 text-gray-400" />
                    <div>
                      <h3 className="font-semibold">{journal.journal_number}</h3>
                      <div className="flex gap-3 text-sm text-gray-500">
                        <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{journal.date}</span>
                        {journal.reference_number && <span>Ref: {journal.reference_number}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <ArrowLeftRight className="h-4 w-4 text-gray-400" />
                    <span className="font-bold">₹{journal.total_debit?.toLocaleString('en-IN')}</span>
                  </div>
                </div>
                {journal.notes && <p className="text-sm text-gray-600 mt-2">{journal.notes}</p>}
                <div className="mt-3 text-xs text-gray-400">
                  {journal.line_items?.length || 0} line items
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      }
    </div>
  );
}

/**
 * EstimateModal — The "Create New" tab content with the full estimate form.
 * Extracted from EstimatesEnhanced.jsx Create Tab (lines 1489-1816).
 * Rendered inside the Tabs component managed by the parent.
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TabsContent } from "@/components/ui/tabs";
import { Plus, Package, Settings, IndianRupee } from "lucide-react";
import { EstimateLineItemRow } from "@/components/estimates";
import { AutoSaveIndicator, DraftRecoveryBanner } from "@/components/shared/FormPersistence";

export function EstimateModal({ state, handlers }) {
  const {
    newEstimate, setNewEstimate, newLineItem, setNewLineItem, contactSearch, setContactSearch,
    contacts, setContacts, selectedContact, customerPricing, items, totals,
    newEstimatePersistence, quickAddItem, setQuickAddItem,
  } = state;
  const {
    handleCreateEstimate, addLineItem, removeLineItem, selectItem,
    searchContacts, fetchCustomerPricing, setSelectedContact, setShowAddItemDialog,
    setShowBulkActionDialog, resetForm,
  } = handlers;

  return (
    <TabsContent value="create" className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Create New Estimate</CardTitle>
              <CardDescription>Fill in the details and add line items</CardDescription>
            </div>
            <AutoSaveIndicator
              lastSaved={newEstimatePersistence.lastSaved}
              isSaving={newEstimatePersistence.isSaving}
              isDirty={newEstimatePersistence.isDirty}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <DraftRecoveryBanner
            show={newEstimatePersistence.showRecoveryBanner}
            savedAt={newEstimatePersistence.savedDraftInfo?.timestamp}
            onRestore={newEstimatePersistence.handleRestoreDraft}
            onDiscard={newEstimatePersistence.handleDiscardDraft}
          />

          {/* Customer Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Customer *</Label>
              <div className="relative">
                <Input
                  value={contactSearch}
                  onChange={(e) => { setContactSearch(e.target.value); searchContacts(e.target.value); }}
                  placeholder="Search customer..."
                  data-testid="customer-search"
                />
                {contacts.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-[#111820] border border-[rgba(255,255,255,0.13)] rounded max-h-48 overflow-y-auto">
                    {contacts.map(c => (
                      <div
                        key={c.contact_id}
                        className="px-3 py-2 hover:bg-[rgba(255,255,255,0.05)] cursor-pointer"
                        onClick={() => {
                          setSelectedContact(c);
                          setNewEstimate(prev => ({ ...prev, customer_id: c.contact_id }));
                          setContactSearch(c.name);
                          setContacts([]);
                          fetchCustomerPricing(c.contact_id);
                        }}
                      >
                        <p className="font-medium">{c.name}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.45)]">{c.company_name} {c.gstin && `• ${c.gstin}`}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {selectedContact && (
                <div className="mt-2 p-2 bg-[#111820] rounded text-xs">
                  <p><strong>{selectedContact.name}</strong></p>
                  {selectedContact.email && <p>{selectedContact.email}</p>}
                  {selectedContact.gstin && <p>GSTIN: {selectedContact.gstin}</p>}
                  {customerPricing?.sales_price_list && (
                    <div className="mt-1 flex items-center gap-1">
                      <Badge variant="outline" className="text-xs bg-[rgba(34,197,94,0.08)] text-[#22C55E] border-[rgba(34,197,94,0.25)]">
                        <IndianRupee className="h-3 w-3 mr-1" />
                        {customerPricing.sales_price_list.name}
                        {customerPricing.sales_price_list.discount_percentage > 0 && ` (-${customerPricing.sales_price_list.discount_percentage}%)`}
                        {customerPricing.sales_price_list.markup_percentage > 0 && ` (+${customerPricing.sales_price_list.markup_percentage}%)`}
                      </Badge>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Date</Label><Input type="date" value={newEstimate.date} onChange={(e) => setNewEstimate({...newEstimate, date: e.target.value})} /></div>
              <div><Label>Expiry Date</Label><Input type="date" value={newEstimate.expiry_date} onChange={(e) => setNewEstimate({...newEstimate, expiry_date: e.target.value})} /></div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div><Label>Reference #</Label><Input value={newEstimate.reference_number} onChange={(e) => setNewEstimate({...newEstimate, reference_number: e.target.value})} placeholder="PO-123" /></div>
            <div><Label>Subject</Label><Input value={newEstimate.subject} onChange={(e) => setNewEstimate({...newEstimate, subject: e.target.value})} placeholder="Quote for..." /></div>
            <div><Label>Salesperson</Label><Input value={newEstimate.salesperson_name} onChange={(e) => setNewEstimate({...newEstimate, salesperson_name: e.target.value})} /></div>
          </div>

          <Separator />

          {/* Line Items Table */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h4 className="font-medium">Item Table</h4>
              <Button variant="outline" size="sm" className="text-[#3B9EFF]" onClick={() => setShowBulkActionDialog(true)}>
                <Settings className="h-4 w-4 mr-1" /> Bulk Actions
              </Button>
            </div>

            <div className="border rounded-lg overflow-visible">
              <table className="w-full text-sm">
                <thead className="bg-[#111820] border-b">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium w-[280px]">ITEM DETAILS</th>
                    <th className="px-3 py-2 text-center font-medium w-20">QUANTITY</th>
                    <th className="px-3 py-2 text-center font-medium w-24"><div className="flex items-center justify-center gap-1">RATE <IndianRupee className="h-3 w-3" /></div></th>
                    <th className="px-3 py-2 text-center font-medium w-28">DISCOUNT</th>
                    <th className="px-3 py-2 text-center font-medium w-32">TAX</th>
                    <th className="px-3 py-2 text-right font-medium w-24">AMOUNT</th>
                    <th className="px-3 py-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {newEstimate.line_items.map((item, idx) => (
                    <EstimateLineItemRow key={idx} item={item} index={idx} onRemove={removeLineItem} readOnly={false} />
                  ))}

                  {/* New Item Row */}
                  <tr className="border-t bg-[rgba(59,158,255,0.08)]/30">
                    <td className="px-3 py-2">
                      <div className="relative">
                        <div className="flex items-center gap-1">
                          <Package className="h-4 w-4 text-[rgba(244,246,240,0.25)]" />
                          <Input
                            value={newLineItem.name}
                            onChange={(e) => setNewLineItem({...newLineItem, name: e.target.value, item_id: ""})}
                            placeholder="Type or click to select an item..."
                            className="border-0 bg-transparent focus:ring-0 h-8"
                            data-testid="item-search-input"
                          />
                        </div>
                        {newLineItem.name && newLineItem.name.length >= 1 && !newLineItem.item_id && (
                          <div className="absolute z-50 left-0 right-0 mt-1 bg-[#111820] border border-[rgba(255,255,255,0.13)] rounded max-h-64 overflow-y-auto">
                            {items
                              .filter(item => item.name?.toLowerCase().includes(newLineItem.name.toLowerCase()) || item.sku?.toLowerCase().includes(newLineItem.name.toLowerCase()))
                              .slice(0, 10)
                              .map(item => (
                                <div key={item.item_id} className="px-3 py-2 hover:bg-[rgba(200,255,0,0.08)] cursor-pointer border-b last:border-0" onClick={() => selectItem(item)}>
                                  <div className="flex justify-between">
                                    <div>
                                      <div className="font-medium text-[#F4F6F0]">{item.name}</div>
                                      <div className="text-xs text-[rgba(244,246,240,0.45)]">
                                        {item.sku && <span>SKU: {item.sku}</span>}
                                        {item.rate && <span className="ml-2">Rate: ₹{item.rate?.toLocaleString('en-IN')}</span>}
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <div className={`text-sm font-medium ${(item.stock_on_hand || 0) < 0 ? 'text-red-500' : 'text-[rgba(244,246,240,0.45)]'}`}>
                                        {item.stock_on_hand !== undefined && (
                                          <>Stock on Hand<br/><span className={`font-bold ${(item.stock_on_hand || 0) < 0 ? 'text-red-500' : 'text-[#22C55E]'}`}>{item.stock_on_hand} {item.unit || 'pcs'}</span></>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            <div className="px-3 py-2 hover:bg-[rgba(59,158,255,0.08)] cursor-pointer border-t flex items-center gap-2 text-[#3B9EFF]" onClick={() => { setQuickAddItem({...quickAddItem, name: newLineItem.name}); setShowAddItemDialog(true); }}>
                              <Plus className="h-4 w-4" /><span>Add New Item "{newLineItem.name}"</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2"><Input type="number" value={newLineItem.quantity} onChange={(e) => setNewLineItem({...newLineItem, quantity: parseFloat(e.target.value) || 1})} min="1" className="w-16 h-8 text-center mx-auto" /></td>
                    <td className="px-3 py-2"><Input type="number" value={newLineItem.rate} onChange={(e) => setNewLineItem({...newLineItem, rate: parseFloat(e.target.value) || 0})} min="0" className="w-20 h-8 text-center mx-auto" placeholder="0.00" /></td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1 justify-center">
                        <Input type="number" value={newLineItem.discount_type === 'amount' ? newLineItem.discount_value : newLineItem.discount_percent} onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          if (newLineItem.discount_type === 'amount') setNewLineItem({...newLineItem, discount_value: val, discount_percent: 0});
                          else setNewLineItem({...newLineItem, discount_percent: val, discount_value: 0});
                        }} min="0" className="w-14 h-8 text-center" />
                        <Select value={newLineItem.discount_type || "percent"} onValueChange={(v) => setNewLineItem({...newLineItem, discount_type: v, discount_percent: 0, discount_value: 0})}>
                          <SelectTrigger className="w-12 h-8 px-1"><SelectValue /></SelectTrigger>
                          <SelectContent><SelectItem value="percent">%</SelectItem><SelectItem value="amount">₹</SelectItem></SelectContent>
                        </Select>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <Select value={String(newLineItem.tax_percentage || 18)} onValueChange={(v) => setNewLineItem({...newLineItem, tax_percentage: parseFloat(v)})}>
                        <SelectTrigger className="w-28 h-8 mx-auto"><SelectValue placeholder="Select Tax" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">GST 0%</SelectItem><SelectItem value="5">GST 5%</SelectItem>
                          <SelectItem value="12">GST 12%</SelectItem><SelectItem value="18">GST 18%</SelectItem><SelectItem value="28">GST 28%</SelectItem>
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-3 py-2 text-right font-medium text-[rgba(244,246,240,0.25)]">₹{((newLineItem.quantity || 0) * (newLineItem.rate || 0)).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    <td className="px-3 py-2">
                      <Button size="sm" onClick={addLineItem} className="h-7 bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" disabled={!newLineItem.name}><Plus className="h-4 w-4" /></Button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="flex justify-end mt-4">
              <div className="w-64 space-y-2 text-sm">
                <div className="flex justify-between"><span>Subtotal:</span><span>₹{totals.subtotal.toFixed(2)}</span></div>
                <div className="flex justify-between items-center gap-2">
                  <span>Discount:</span>
                  <div className="flex gap-1">
                    <Select value={newEstimate.discount_type} onValueChange={(v) => setNewEstimate({...newEstimate, discount_type: v})}>
                      <SelectTrigger className="w-20 h-7"><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="none">None</SelectItem><SelectItem value="percent">%</SelectItem><SelectItem value="amount">₹</SelectItem></SelectContent>
                    </Select>
                    {newEstimate.discount_type !== "none" && (
                      <Input type="number" className="w-16 h-7" value={newEstimate.discount_value} onChange={(e) => setNewEstimate({...newEstimate, discount_value: parseFloat(e.target.value) || 0})} />
                    )}
                  </div>
                </div>
                <div className="flex justify-between"><span>Tax:</span><span>₹{totals.totalTax.toFixed(2)}</span></div>
                <div className="flex justify-between items-center"><span>Shipping:</span><Input type="number" className="w-24 h-7" value={newEstimate.shipping_charge} onChange={(e) => setNewEstimate({...newEstimate, shipping_charge: parseFloat(e.target.value) || 0})} /></div>
                <div className="flex justify-between items-center"><span>Adjustment:</span><Input type="number" className="w-24 h-7" value={newEstimate.adjustment} onChange={(e) => setNewEstimate({...newEstimate, adjustment: parseFloat(e.target.value) || 0})} /></div>
                <Separator />
                <div className="flex justify-between font-bold text-lg"><span>Grand Total:</span><span>₹{totals.grandTotal.toFixed(2)}</span></div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Notes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><Label>Terms & Conditions</Label><Textarea value={newEstimate.terms_and_conditions} onChange={(e) => setNewEstimate({...newEstimate, terms_and_conditions: e.target.value})} rows={3} /></div>
            <div><Label>Notes</Label><Textarea value={newEstimate.notes} onChange={(e) => setNewEstimate({...newEstimate, notes: e.target.value})} rows={3} /></div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={resetForm}>Reset</Button>
            <Button onClick={handleCreateEstimate} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-estimate-submit">Create Estimate</Button>
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  );
}

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { 
  Plus, Folder, Settings, Database, Edit, Trash2, 
  Eye, FileText, Calendar, Hash, Mail, Phone, Link,
  CheckSquare, List, Search
} from "lucide-react";
import { API } from "@/App";

const fieldTypeIcons = {
  text: FileText,
  number: Hash,
  decimal: Hash,
  date: Calendar,
  datetime: Calendar,
  email: Mail,
  phone: Phone,
  url: Link,
  textarea: FileText,
  dropdown: List,
  checkbox: CheckSquare,
  lookup: Search
};

const fieldTypes = [
  { value: "text", label: "Text" },
  { value: "number", label: "Number" },
  { value: "decimal", label: "Decimal" },
  { value: "date", label: "Date" },
  { value: "datetime", label: "Date & Time" },
  { value: "email", label: "Email" },
  { value: "phone", label: "Phone" },
  { value: "url", label: "URL" },
  { value: "textarea", label: "Multi-line Text" },
  { value: "dropdown", label: "Dropdown" },
  { value: "checkbox", label: "Checkbox" }
];

export default function CustomModules() {
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModuleDialog, setShowCreateModuleDialog] = useState(false);
  const [showCreateRecordDialog, setShowCreateRecordDialog] = useState(false);
  const [showRecordDetailDialog, setShowRecordDetailDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const [newModule, setNewModule] = useState({
    module_name: "",
    module_label: "",
    description: "",
    fields: [],
    icon: "folder"
  });

  const [newField, setNewField] = useState({
    name: "",
    label: "",
    type: "text",
    required: false,
    options: ""
  });

  const [newRecord, setNewRecord] = useState({});

  useEffect(() => { fetchModules(); }, []);

  useEffect(() => {
    if (selectedModule) {
      fetchRecords(selectedModule.module_id);
    }
  }, [selectedModule]);

  const fetchModules = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/custom-modules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setModules(data.custom_modules || []);
    } catch (error) {
      console.error("Failed to fetch modules:", error);
      toast.error("Failed to load custom modules");
    } finally {
      setLoading(false);
    }
  };

  const fetchRecords = async (moduleId) => {
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({ per_page: "100" });
      if (searchQuery) params.append("search", searchQuery);
      
      const res = await fetch(`${API}/zoho/custom-modules/${moduleId}/records?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setRecords(data.records || []);
    } catch (error) {
      console.error("Failed to fetch records:", error);
    }
  };

  const handleAddField = () => {
    if (!newField.name || !newField.label) {
      return toast.error("Enter field name and label");
    }
    // Create field name from label if not provided
    const fieldName = newField.name || newField.label.toLowerCase().replace(/\s+/g, "_");
    
    setNewModule({
      ...newModule,
      fields: [...newModule.fields, {
        ...newField,
        name: fieldName,
        options: newField.type === "dropdown" ? newField.options.split(",").map(o => o.trim()) : undefined
      }]
    });
    setNewField({ name: "", label: "", type: "text", required: false, options: "" });
  };

  const removeField = (index) => {
    setNewModule({
      ...newModule,
      fields: newModule.fields.filter((_, i) => i !== index)
    });
  };

  const handleCreateModule = async () => {
    if (!newModule.module_label) return toast.error("Enter module name");
    if (newModule.fields.length === 0) return toast.error("Add at least one field");

    const moduleName = newModule.module_name || newModule.module_label.toLowerCase().replace(/\s+/g, "_");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/custom-modules`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...newModule, module_name: moduleName })
      });
      if (res.ok) {
        toast.success("Custom module created");
        setShowCreateModuleDialog(false);
        setNewModule({ module_name: "", module_label: "", description: "", fields: [], icon: "folder" });
        fetchModules();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create module");
      }
    } catch {
      toast.error("Error creating module");
    }
  };

  const handleDeleteModule = async (moduleId) => {
    if (!confirm("Deactivate this custom module?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/custom-modules/${moduleId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Module deactivated");
        setSelectedModule(null);
        fetchModules();
      }
    } catch {
      toast.error("Failed to delete module");
    }
  };

  const handleCreateRecord = async () => {
    if (!selectedModule) return;

    // Validate required fields
    for (const field of selectedModule.fields) {
      if (field.required && !newRecord[field.name]) {
        return toast.error(`${field.label} is required`);
      }
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/custom-modules/${selectedModule.module_id}/records`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newRecord)
      });
      if (res.ok) {
        toast.success("Record created");
        setShowCreateRecordDialog(false);
        setNewRecord({});
        fetchRecords(selectedModule.module_id);
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create record");
      }
    } catch {
      toast.error("Error creating record");
    }
  };

  const handleDeleteRecord = async (recordId) => {
    if (!selectedModule || !confirm("Delete this record?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/custom-modules/${selectedModule.module_id}/records/${recordId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Record deleted");
        setShowRecordDetailDialog(false);
        fetchRecords(selectedModule.module_id);
      }
    } catch {
      toast.error("Failed to delete record");
    }
  };

  const renderFieldInput = (field, value, onChange) => {
    const Icon = fieldTypeIcons[field.type] || FileText;
    
    switch (field.type) {
      case "textarea":
        return (
          <Textarea
            value={value || ""}
            onChange={e => onChange(e.target.value)}
            placeholder={field.label}
            rows={3}
          />
        );
      case "number":
      case "decimal":
        return (
          <Input
            type="number"
            step={field.type === "decimal" ? "0.01" : "1"}
            value={value || ""}
            onChange={e => onChange(parseFloat(e.target.value) || 0)}
            placeholder={field.label}
          />
        );
      case "date":
        return (
          <Input
            type="date"
            value={value || ""}
            onChange={e => onChange(e.target.value)}
          />
        );
      case "datetime":
        return (
          <Input
            type="datetime-local"
            value={value || ""}
            onChange={e => onChange(e.target.value)}
          />
        );
      case "dropdown":
        return (
          <Select value={value || ""} onValueChange={onChange}>
            <SelectTrigger>
              <SelectValue placeholder={`Select ${field.label}`} />
            </SelectTrigger>
            <SelectContent>
              {(field.options || []).map(opt => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      case "checkbox":
        return (
          <div className="flex items-center gap-2">
            <Switch checked={value || false} onCheckedChange={onChange} />
            <span className="text-sm text-[rgba(244,246,240,0.45)]">{value ? "Yes" : "No"}</span>
          </div>
        );
      default:
        return (
          <Input
            type={field.type === "email" ? "email" : field.type === "url" ? "url" : "text"}
            value={value || ""}
            onChange={e => onChange(e.target.value)}
            placeholder={field.label}
          />
        );
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6" data-testid="custom-modules-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Custom Modules</h1>
          <p className="text-[rgba(244,246,240,0.45)]">Create and manage your own data modules</p>
        </div>
        <Dialog open={showCreateModuleDialog} onOpenChange={setShowCreateModuleDialog}>
          <DialogTrigger asChild>
            <Button data-testid="create-module-btn">
              <Plus className="h-4 w-4 mr-2" />
              New Custom Module
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Custom Module</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Module Label *</Label>
                  <Input
                    value={newModule.module_label}
                    onChange={e => setNewModule({ ...newModule, module_label: e.target.value })}
                    placeholder="e.g., Equipment Maintenance"
                  />
                </div>
                <div>
                  <Label>Module Name (internal)</Label>
                  <Input
                    value={newModule.module_name}
                    onChange={e => setNewModule({ ...newModule, module_name: e.target.value })}
                    placeholder="e.g., equipment_maintenance"
                  />
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">Auto-generated if left blank</p>
                </div>
              </div>

              <div>
                <Label>Description</Label>
                <Textarea
                  value={newModule.description}
                  onChange={e => setNewModule({ ...newModule, description: e.target.value })}
                  placeholder="What is this module for?"
                  rows={2}
                />
              </div>

              {/* Fields Builder */}
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-3">Fields</h4>
                
                {/* Add Field Form */}
                <div className="grid grid-cols-5 gap-2 mb-3">
                  <Input
                    placeholder="Field Label"
                    value={newField.label}
                    onChange={e => setNewField({ ...newField, label: e.target.value })}
                  />
                  <Input
                    placeholder="Field Name"
                    value={newField.name}
                    onChange={e => setNewField({ ...newField, name: e.target.value.toLowerCase().replace(/\s+/g, "_") })}
                  />
                  <Select value={newField.type} onValueChange={v => setNewField({ ...newField, type: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {fieldTypes.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={newField.required}
                      onCheckedChange={v => setNewField({ ...newField, required: v })}
                    />
                    <span className="text-sm">Required</span>
                  </div>
                  <Button type="button" onClick={handleAddField} variant="outline">Add</Button>
                </div>

                {newField.type === "dropdown" && (
                  <div className="mb-3">
                    <Input
                      placeholder="Dropdown options (comma-separated)"
                      value={newField.options}
                      onChange={e => setNewField({ ...newField, options: e.target.value })}
                    />
                  </div>
                )}

                {/* Added Fields */}
                {newModule.fields.length > 0 ? (
                  <div className="space-y-2">
                    {newModule.fields.map((field, idx) => {
                      const Icon = fieldTypeIcons[field.type] || FileText;
                      return (
                        <div key={idx} className="flex justify-between items-center bg-[#111820] p-3 rounded">
                          <div className="flex items-center gap-3">
                            <Icon className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                            <div>
                              <span className="font-medium">{field.label}</span>
                              <span className="text-sm text-[rgba(244,246,240,0.45)] ml-2">({field.name})</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{field.type}</Badge>
                            {field.required && <Badge className="bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]">Required</Badge>}
                            <Button size="sm" variant="ghost" onClick={() => removeField(idx)}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-[rgba(244,246,240,0.45)] text-center py-4">No fields added yet</p>
                )}
              </div>

              <Button className="w-full" onClick={handleCreateModule}>Create Module</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-4 gap-6">
        {/* Modules List */}
        <div className="col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Modules</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {modules.length > 0 ? (
                <div className="divide-y">
                  {modules.map(module => (
                    <div
                      key={module.module_id}
                      className={`p-4 cursor-pointer hover:bg-[#111820] ${selectedModule?.module_id === module.module_id ? "bg-blue-50 border-l-4 border-blue-500" : ""}`}
                      onClick={() => setSelectedModule(module)}
                    >
                      <div className="flex items-center gap-3">
                        <Folder className="h-5 w-5 text-[rgba(244,246,240,0.45)]" />
                        <div>
                          <p className="font-medium">{module.module_label}</p>
                          <p className="text-sm text-[rgba(244,246,240,0.45)]">{module.records_count || 0} records</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-[rgba(244,246,240,0.45)]">
                  <Database className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
                  <p>No custom modules yet</p>
                  <p className="text-sm">Create your first module to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Module Content */}
        <div className="col-span-3">
          {selectedModule ? (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>{selectedModule.module_label}</CardTitle>
                  <p className="text-sm text-[rgba(244,246,240,0.45)] mt-1">{selectedModule.description || "No description"}</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => handleDeleteModule(selectedModule.module_id)}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Deactivate
                  </Button>
                  <Dialog open={showCreateRecordDialog} onOpenChange={setShowCreateRecordDialog}>
                    <DialogTrigger asChild>
                      <Button>
                        <Plus className="h-4 w-4 mr-2" />
                        Add Record
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-lg">
                      <DialogHeader>
                        <DialogTitle>Add Record to {selectedModule.module_label}</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        {selectedModule.fields.map(field => (
                          <div key={field.name}>
                            <Label>
                              {field.label}
                              {field.required && <span className="text-red-500 ml-1">*</span>}
                            </Label>
                            {renderFieldInput(
                              field,
                              newRecord[field.name],
                              (value) => setNewRecord({ ...newRecord, [field.name]: value })
                            )}
                          </div>
                        ))}
                        <Button className="w-full" onClick={handleCreateRecord}>
                          Create Record
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>

              <CardContent>
                {/* Search */}
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                    <Input
                      placeholder="Search records..."
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && fetchRecords(selectedModule.module_id)}
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Fields Info */}
                <div className="mb-4 flex gap-2 flex-wrap">
                  {selectedModule.fields.map(field => {
                    const Icon = fieldTypeIcons[field.type] || FileText;
                    return (
                      <Badge key={field.name} variant="outline" className="flex items-center gap-1">
                        <Icon className="h-3 w-3" />
                        {field.label}
                      </Badge>
                    );
                  })}
                </div>

                {/* Records Table */}
                {records.length > 0 ? (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-[#111820]">
                        <tr>
                          {selectedModule.fields.slice(0, 5).map(field => (
                            <th key={field.name} className="text-left p-3 font-medium">
                              {field.label}
                            </th>
                          ))}
                          <th className="text-right p-3 font-medium">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {records.map(record => (
                          <tr key={record.record_id} className="border-t hover:bg-[#111820]">
                            {selectedModule.fields.slice(0, 5).map(field => (
                              <td key={field.name} className="p-3">
                                {field.type === "checkbox" 
                                  ? (record[field.name] ? "Yes" : "No")
                                  : (record[field.name] || "-")}
                              </td>
                            ))}
                            <td className="p-3 text-right">
                              <div className="flex justify-end gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => { setSelectedRecord(record); setShowRecordDetailDialog(true); }}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDeleteRecord(record.record_id)}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
                    <FileText className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
                    <p>No records yet</p>
                    <p className="text-sm">Click "Add Record" to create the first one</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
                <Settings className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
                <p className="text-lg font-medium">Select a Module</p>
                <p className="text-sm">Choose a custom module from the list to view its records</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Record Detail Dialog */}
      <Dialog open={showRecordDetailDialog} onOpenChange={setShowRecordDetailDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Details</DialogTitle>
          </DialogHeader>
          {selectedRecord && selectedModule && (
            <div className="space-y-4">
              {selectedModule.fields.map(field => (
                <div key={field.name}>
                  <Label className="text-[rgba(244,246,240,0.45)]">{field.label}</Label>
                  <p className="font-medium">
                    {field.type === "checkbox" 
                      ? (selectedRecord[field.name] ? "Yes" : "No")
                      : (selectedRecord[field.name] || "-")}
                  </p>
                </div>
              ))}
              <div className="pt-4 border-t">
                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={() => handleDeleteRecord(selectedRecord.record_id)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Record
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

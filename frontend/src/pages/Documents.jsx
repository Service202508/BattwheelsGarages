/**
 * Battwheels OS - Documents Management Page
 * Store and manage receipts, attachments, and service photos
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileText, Folder, FolderPlus, Upload, Search, Grid, List,
  MoreVertical, Download, Trash2, Tag, Image, File, Plus, RefreshCw,
  Receipt, Camera, FileSpreadsheet
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";
import { toast } from "sonner";

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

// Get icon for document type
const getDocIcon = (type, mimeType) => {
  if (mimeType?.startsWith("image/")) return Image;
  switch (type) {
    case "receipt": return Receipt;
    case "invoice": return FileText;
    case "photo": return Camera;
    case "report": return FileSpreadsheet;
    default: return File;
  }
};

// Document type colors
const TYPE_COLORS = {
  receipt: "bg-bw-green/10 text-bw-green",
  invoice: "bg-blue-100 text-blue-800",
  photo: "bg-purple-100 text-purple-800",
  contract: "bg-orange-100 text-orange-800",
  report: "bg-yellow-100 text-yellow-800",
  other: "bg-white/5 text-bw-white"
};

// Document Card Component
const DocumentCard = ({ doc, selected, onSelect, onDelete, viewMode }) => {
  const Icon = getDocIcon(doc.document_type, doc.mime_type);
  
  if (viewMode === "list") {
    return (
      <div 
        className={`flex items-center gap-4 p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors ${selected ? 'bg-primary/10 border-primary' : ''}`}
        onClick={() => onSelect(doc.document_id)}
      >
        <Checkbox checked={selected} onChange={() => {}} />
        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{doc.name}</p>
          <p className="text-xs text-muted-foreground">
            {doc.file_name} • {formatFileSize(doc.file_size)}
          </p>
        </div>
        <Badge className={TYPE_COLORS[doc.document_type] || TYPE_COLORS.other}>
          {doc.document_type}
        </Badge>
        <p className="text-sm text-muted-foreground">
          {new Date(doc.created_at).toLocaleDateString()}
        </p>
        <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); onDelete(doc.document_id); }}>
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
    );
  }
  
  return (
    <Card 
      className={`cursor-pointer transition-colors ${selected ? 'ring-2 ring-primary' : ''}`}
      onClick={() => onSelect(doc.document_id)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center">
            <Icon className="h-6 w-6 text-muted-foreground" />
          </div>
          <Checkbox checked={selected} onChange={() => {}} />
        </div>
        <h4 className="font-medium truncate mb-1">{doc.name}</h4>
        <p className="text-xs text-muted-foreground truncate mb-2">{doc.file_name}</p>
        <div className="flex items-center justify-between">
          <Badge variant="secondary" className="text-xs">
            {doc.document_type}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {formatFileSize(doc.file_size)}
          </span>
        </div>
        {doc.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {doc.tags.slice(0, 2).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Folder Item Component
const FolderItem = ({ folder, onClick }) => (
  <Card 
    className="cursor-pointer hover:border-bw-volt/20 transition-colors"
    onClick={() => onClick(folder.folder_id)}
  >
    <CardContent className="p-4">
      <div className="flex items-center gap-3">
        <div 
          className="h-12 w-12 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: folder.color + "20" }}
        >
          <Folder className="h-6 w-6" style={{ color: folder.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium truncate">{folder.name}</h4>
          <p className="text-xs text-muted-foreground">
            {folder.document_count || 0} documents
          </p>
        </div>
      </div>
    </CardContent>
  </Card>
);

// Upload Dialog
const UploadDialog = ({ open, onClose, onUpload, folders }) => {
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    document_type: "general",
    folder_id: "",
    tags: ""
  });
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!formData.name) {
        setFormData({ ...formData, name: selectedFile.name.split(".")[0] });
      }
    }
  };
  
  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a file");
      return;
    }
    
    setUploading(true);
    
    try {
      // Convert file to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(",")[1];
        
        await onUpload({
          ...formData,
          tags: formData.tags ? formData.tags.split(",").map(t => t.trim()) : [],
          file_content: base64,
          file_name: file.name,
          mime_type: file.type
        });
        
        setFormData({ name: "", description: "", document_type: "general", folder_id: "", tags: "" });
        setFile(null);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>Add a new document to your library</DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div
            className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx"
            />
            {file ? (
              <div>
                <File className="h-10 w-10 mx-auto mb-2 text-primary" />
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-muted-foreground">{formatFileSize(file.size)}</p>
              </div>
            ) : (
              <div>
                <Upload className="h-10 w-10 mx-auto mb-2 text-muted-foreground" />
                <p className="font-medium">Click to select file</p>
                <p className="text-sm text-muted-foreground">or drag and drop</p>
              </div>
            )}
          </div>
          
          <div>
            <Label>Document Name *</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter document name"
            />
          </div>
          
          <div>
            <Label>Type</Label>
            <Select
              value={formData.document_type}
              onValueChange={(v) => setFormData({ ...formData, document_type: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">General</SelectItem>
                <SelectItem value="receipt">Receipt</SelectItem>
                <SelectItem value="invoice">Invoice</SelectItem>
                <SelectItem value="photo">Photo</SelectItem>
                <SelectItem value="contract">Contract</SelectItem>
                <SelectItem value="report">Report</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Folder</Label>
            <Select
              value={formData.folder_id || "__root__"}
              onValueChange={(v) => setFormData({ ...formData, folder_id: v === "__root__" ? "" : v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select folder" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__root__">Root</SelectItem>
                {folders.map((folder) => (
                  <SelectItem key={folder.folder_id} value={folder.folder_id}>
                    {folder.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Tags (comma separated)</Label>
            <Input
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              placeholder="e.g., service, parts, warranty"
            />
          </div>
          
          <div>
            <Label>Description</Label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description"
              rows={2}
            />
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleUpload} disabled={uploading || !file}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// New Folder Dialog
const NewFolderDialog = ({ open, onClose, onCreate }) => {
  const [name, setName] = useState("");
  const [color, setColor] = useState("#3B82F6");
  
  const handleCreate = () => {
    if (!name.trim()) {
      toast.error("Enter folder name");
      return;
    }
    onCreate({ name, color });
    setName("");
    setColor("#3B82F6");
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>New Folder</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <Label>Folder Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter folder name"
            />
          </div>
          
          <div>
            <Label>Color</Label>
            <div className="flex gap-2 mt-2">
              {["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#6B7280"].map((c) => (
                <button
                  key={c}
                  className={`h-8 w-8 rounded-full ${color === c ? 'ring-2 ring-offset-2 ring-primary' : ''}`}
                  style={{ backgroundColor: c }}
                  onClick={() => setColor(c)}
                />
              ))}
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleCreate}>Create Folder</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Main Documents Page
export default function Documents({ user }) {
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [currentFolder, setCurrentFolder] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid");
  const [typeFilter, setTypeFilter] = useState("");
  
  const [showUpload, setShowUpload] = useState(false);
  const [showNewFolder, setShowNewFolder] = useState(false);
  
  const headers = getAuthHeaders();
  
  const fetchData = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (currentFolder) params.append("folder_id", currentFolder);
      if (searchQuery) params.append("search", searchQuery);
      if (typeFilter) params.append("document_type", typeFilter);
      
      const [docsRes, foldersRes, statsRes] = await Promise.all([
        fetch(`${API}/documents/?${params}`, { headers }),
        fetch(`${API}/documents/folders`, { headers }),
        fetch(`${API}/documents/stats/summary`, { headers })
      ]);
      
      if (docsRes.ok) {
        const data = await docsRes.json();
        setDocuments(data.documents || []);
      }
      
      if (foldersRes.ok) {
        const data = await foldersRes.json();
        setFolders(data.folders || []);
      }
      
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data.stats);
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error);
    } finally {
      setLoading(false);
    }
  }, [headers, currentFolder, searchQuery, typeFilter]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  const handleUpload = async (data) => {
    try {
      const res = await fetch(`${API}/documents/`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        toast.success("Document uploaded");
        setShowUpload(false);
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Upload failed");
      }
    } catch (error) {
      toast.error("Upload failed");
    }
  };
  
  const handleCreateFolder = async (data) => {
    try {
      const res = await fetch(`${API}/documents/folders`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        toast.success("Folder created");
        setShowNewFolder(false);
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create folder");
      }
    } catch (error) {
      toast.error("Failed to create folder");
    }
  };
  
  const handleDeleteDocument = async (docId) => {
    if (!confirm("Delete this document?")) return;
    
    try {
      const res = await fetch(`${API}/documents/${docId}`, {
        method: "DELETE",
        headers
      });
      
      if (res.ok) {
        toast.success("Document deleted");
        fetchData();
      }
    } catch (error) {
      toast.error("Failed to delete");
    }
  };
  
  const handleSelectDoc = (docId) => {
    setSelectedDocs((prev) => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };
  
  const handleBulkDelete = async () => {
    if (selectedDocs.length === 0) return;
    if (!confirm(`Delete ${selectedDocs.length} documents?`)) return;
    
    try {
      const res = await fetch(`${API}/documents/bulk/delete`, {
        method: "DELETE",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ document_ids: selectedDocs })
      });
      
      if (res.ok) {
        toast.success(`Deleted ${selectedDocs.length} documents`);
        setSelectedDocs([]);
        fetchData();
      }
    } catch (error) {
      toast.error("Failed to delete");
    }
  };
  
  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6" data-testid="documents-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Documents</h1>
          <p className="text-muted-foreground">Store and manage receipts, photos, and attachments</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={() => setShowNewFolder(true)}>
            <FolderPlus className="h-4 w-4 mr-2" />
            New Folder
          </Button>
          <Button onClick={() => setShowUpload(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload
          </Button>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <FileText className="h-5 w-5 text-bw-blue" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.total_documents || 0}</p>
                <p className="text-sm text-muted-foreground">Total Documents</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-bw-green/10 flex items-center justify-center">
                <Folder className="h-5 w-5 text-bw-green" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.total_folders || 0}</p>
                <p className="text-sm text-muted-foreground">Folders</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <Receipt className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.by_type?.receipt || 0}</p>
                <p className="text-sm text-muted-foreground">Receipts</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-orange-100 flex items-center justify-center">
                <File className="h-5 w-5 text-bw-orange" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.total_size_mb || 0} MB</p>
                <p className="text-sm text-muted-foreground">Storage Used</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Toolbar */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <Select value={typeFilter || "__all__"} onValueChange={(v) => setTypeFilter(v === "__all__" ? "" : v)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All Types</SelectItem>
            <SelectItem value="receipt">Receipts</SelectItem>
            <SelectItem value="invoice">Invoices</SelectItem>
            <SelectItem value="photo">Photos</SelectItem>
            <SelectItem value="contract">Contracts</SelectItem>
            <SelectItem value="report">Reports</SelectItem>
          </SelectContent>
        </Select>
        
        <div className="flex border rounded-lg">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("grid")}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
        
        {selectedDocs.length > 0 && (
          <Button variant="destructive" onClick={handleBulkDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete ({selectedDocs.length})
          </Button>
        )}
      </div>
      
      {/* Breadcrumb */}
      {currentFolder && (
        <div className="flex items-center gap-2 text-sm">
          <Button 
            variant="link" 
            className="p-0 h-auto"
            onClick={() => setCurrentFolder("")}
          >
            Documents
          </Button>
          <span>/</span>
          <span className="text-muted-foreground">
            {folders.find(f => f.folder_id === currentFolder)?.name || "Folder"}
          </span>
        </div>
      )}
      
      {/* Folders */}
      {!currentFolder && folders.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Folders</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {folders.map((folder) => (
              <FolderItem 
                key={folder.folder_id} 
                folder={folder} 
                onClick={setCurrentFolder}
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Documents */}
      <div>
        <h3 className="font-semibold mb-3">
          {currentFolder ? "Files" : "Recent Documents"}
        </h3>
        
        {documents.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <FileText className="h-16 w-16 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No documents yet</h3>
              <p className="text-muted-foreground mb-4">Upload your first document to get started</p>
              <Button onClick={() => setShowUpload(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Upload Document
              </Button>
            </CardContent>
          </Card>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.document_id}
                doc={doc}
                selected={selectedDocs.includes(doc.document_id)}
                onSelect={handleSelectDoc}
                onDelete={handleDeleteDocument}
                viewMode={viewMode}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.document_id}
                doc={doc}
                selected={selectedDocs.includes(doc.document_id)}
                onSelect={handleSelectDoc}
                onDelete={handleDeleteDocument}
                viewMode={viewMode}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Dialogs */}
      <UploadDialog
        open={showUpload}
        onClose={() => setShowUpload(false)}
        onUpload={handleUpload}
        folders={folders}
      />
      
      <NewFolderDialog
        open={showNewFolder}
        onClose={() => setShowNewFolder(false)}
        onCreate={handleCreateFolder}
      />
    </div>
  );
}

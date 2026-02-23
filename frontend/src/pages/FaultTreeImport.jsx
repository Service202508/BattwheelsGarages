import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { 
  Upload, 
  FileSpreadsheet, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Loader2,
  Play,
  RefreshCw,
  Eye,
  Download
} from 'lucide-react';
import { toast } from 'sonner';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const FaultTreeImport = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [executing, setExecuting] = useState(false);

  // Fetch import jobs
  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/import/jobs`, { credentials: 'include' });
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch (err) {
      console.error('Error fetching jobs:', err);
    }
  }, []);

  // Fetch job preview
  const fetchPreview = async (jobId) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/import/jobs/${jobId}/preview`, { credentials: 'include' });
      const data = await res.json();
      setPreview(data);
    } catch (err) {
      console.error('Error fetching preview:', err);
      toast.error('Failed to fetch preview');
    } finally {
      setLoading(false);
    }
  };

  // Quick import from default URL
  const handleQuickImport = async () => {
    setUploading(true);
    try {
      const res = await fetch(`${API_BASE}/api/import/quick`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      toast.success(`Import job created: ${data.job_id}`);
      setSelectedJob(data.job_id);
      fetchJobs();
      
      // Poll for completion
      pollJobStatus(data.job_id);
    } catch (err) {
      console.error('Error starting import:', err);
      toast.error('Failed to start import');
    } finally {
      setUploading(false);
    }
  };

  // Poll job status
  const pollJobStatus = async (jobId) => {
    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/import/jobs/${jobId}`, { credentials: 'include' });
        const data = await res.json();
        
        // Update jobs list
        setJobs(prev => prev.map(j => j.job_id === jobId ? data : j));
        
        if (data.status === 'validated') {
          toast.success('File parsed successfully! Ready for import.');
          fetchPreview(jobId);
        } else if (data.status === 'completed') {
          toast.success(`Import completed! ${data.imported_count} cards created.`);
        } else if (data.status === 'failed') {
          toast.error('Import failed. Check error details.');
        } else if (['validating', 'importing'].includes(data.status)) {
          setTimeout(poll, 2000);
        }
      } catch (err) {
        console.error('Error polling job:', err);
      }
    };
    
    poll();
  };

  // Execute import
  const handleExecuteImport = async (jobId) => {
    setExecuting(true);
    try {
      const res = await fetch(`${API_BASE}/api/import/jobs/${jobId}/execute?skip_duplicates=true`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      toast.info('Import started...');
      pollJobStatus(jobId);
    } catch (err) {
      console.error('Error executing import:', err);
      toast.error('Failed to execute import');
    } finally {
      setExecuting(false);
    }
  };

  // File upload handler
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/import/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      const data = await res.json();
      toast.success(`File uploaded: ${data.job_id}`);
      setSelectedJob(data.job_id);
      fetchJobs();
      pollJobStatus(data.job_id);
    } catch (err) {
      console.error('Error uploading file:', err);
      toast.error('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  useEffect(() => {
    if (selectedJob) {
      fetchPreview(selectedJob);
    }
  }, [selectedJob]);

  const getStatusBadge = (status) => {
    const variants = {
      pending: { variant: 'secondary', icon: Loader2 },
      validating: { variant: 'secondary', icon: Loader2 },
      validated: { variant: 'default', icon: CheckCircle },
      importing: { variant: 'secondary', icon: Loader2 },
      completed: { variant: 'default', icon: CheckCircle },
      failed: { variant: 'destructive', icon: XCircle },
      partial: { variant: 'warning', icon: AlertTriangle },
    };
    
    const config = variants[status] || variants.pending;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className={`h-3 w-3 ${status === 'validating' || status === 'importing' ? 'animate-spin' : ''}`} />
        {status}
      </Badge>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">EFI Master Fault Tree Import</h1>
          <p className="text-gray-500">Import EV failure intelligence from Excel files</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchJobs}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Import Data
          </CardTitle>
          <CardDescription>
            Upload Battwheels Master Fault Tree Excel file or use quick import
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            {/* Quick Import */}
            <Button 
              onClick={handleQuickImport} 
              disabled={uploading}
              className="bg-green-600 hover:bg-green-700"
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Quick Import (Default File)
            </Button>

            <span className="text-gray-400">or</span>

            {/* File Upload */}
            <div className="relative">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploading}
              />
              <Button variant="outline" disabled={uploading}>
                <FileSpreadsheet className="h-4 w-4 mr-2" />
                Upload Excel File
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Jobs List */}
      <Card>
        <CardHeader>
          <CardTitle>Import Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No import jobs yet</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job ID</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Results</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow 
                    key={job.job_id}
                    className={selectedJob === job.job_id ? 'bg-blue-50' : ''}
                  >
                    <TableCell className="font-mono text-sm">{job.job_id}</TableCell>
                    <TableCell>{job.filename}</TableCell>
                    <TableCell>{getStatusBadge(job.status)}</TableCell>
                    <TableCell>
                      <div className="w-24">
                        <Progress value={job.progress_percent} className="h-2" />
                        <span className="text-xs text-gray-500">{job.progress_percent?.toFixed(0)}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {job.status === 'completed' || job.status === 'partial' ? (
                        <div className="text-sm">
                          <span className="text-green-600">{job.imported_count} created</span>
                          {job.updated_count > 0 && (
                            <span className="text-[#3B9EFF] ml-2">{job.updated_count} updated</span>
                          )}
                          {job.skipped_count > 0 && (
                            <span className="text-gray-500 ml-2">{job.skipped_count} skipped</span>
                          )}
                        </div>
                      ) : job.status === 'validated' ? (
                        <div className="text-sm">
                          <span className="text-green-600">{job.valid_rows} valid</span>
                          {job.error_rows > 0 && (
                            <span className="text-red-600 ml-2">{job.error_rows} errors</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => {
                            setSelectedJob(job.job_id);
                            fetchPreview(job.job_id);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {job.status === 'validated' && (
                          <Button 
                            size="sm"
                            onClick={() => handleExecuteImport(job.job_id)}
                            disabled={executing}
                          >
                            {executing ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Preview Section */}
      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>Import Preview</CardTitle>
            <CardDescription>
              Job: {preview.job_id} | Status: {preview.status}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-[#111820] p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-[#F4F6F0]">{preview.total_rows}</div>
                <div className="text-sm text-gray-500">Total Rows</div>
              </div>
              <div className="bg-[rgba(34,197,94,0.08)] p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">{preview.valid_rows}</div>
                <div className="text-sm text-gray-500">Valid</div>
              </div>
              <div className="bg-[rgba(234,179,8,0.08)] p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-[#EAB308]">{preview.warning_rows}</div>
                <div className="text-sm text-gray-500">Warnings</div>
              </div>
              <div className="bg-[rgba(255,59,47,0.08)] p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-red-600">{preview.error_rows}</div>
                <div className="text-sm text-gray-500">Errors</div>
              </div>
            </div>

            {/* Sections Breakdown */}
            <div>
              <h4 className="font-medium mb-2">Data by Category</h4>
              <div className="flex flex-wrap gap-2">
                {preview.sections?.map((section, idx) => (
                  <Badge key={idx} variant="outline" className="text-sm">
                    {section.vehicle_category}/{section.subsystem_type}: {section.count}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Sample Data */}
            {preview.sample_valid?.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Sample Data</h4>
                <div className="space-y-2">
                  {preview.sample_valid.slice(0, 3).map((row, idx) => (
                    <div key={idx} className="bg-[#111820] p-3 rounded text-sm">
                      <div className="font-medium">{row.complaint_description}</div>
                      <div className="text-gray-500 mt-1">
                        Root causes: {row.root_causes?.slice(0, 2).join(', ')}
                      </div>
                      <div className="text-gray-400 text-xs mt-1">
                        {row.vehicle_category} / {row.subsystem_type} | {row.diagnostic_steps?.length || 0} diagnostic steps
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execute Button */}
            {preview.status === 'validated' && (
              <Alert>
                <AlertDescription className="flex justify-between items-center">
                  <span>Ready to import {preview.valid_rows} failure cards</span>
                  <Button onClick={() => handleExecuteImport(preview.job_id)} disabled={executing}>
                    {executing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Importing...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Execute Import
                      </>
                    )}
                  </Button>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FaultTreeImport;

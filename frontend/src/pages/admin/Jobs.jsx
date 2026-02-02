import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { authService } from '../../utils/auth';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Briefcase,
  Plus,
  Edit,
  Trash2,
  X,
  Save,
  MapPin,
  Clock,
  Users
} from 'lucide-react';

const Jobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    location: '',
    employment_type: 'full-time',
    description: '',
    requirements: '',
    responsibilities: '',
    salary_range: '',
    status: 'active'
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/jobs`, { headers });
      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const headers = authService.getAuthHeaders();
      const url = editingJob
        ? `${API_URL}/api/admin/jobs${editingJob.id}`
        : `${API_URL}/api/admin/jobs`;
      const method = editingJob ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        fetchJobs();
        closeModal();
      }
    } catch (error) {
      console.error('Error saving job:', error);
    }
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job posting?')) return;
    try {
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/jobs${jobId}`, {
        method: 'DELETE',
        headers
      });
      if (response.ok) {
        fetchJobs();
      }
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  const openCreateModal = () => {
    setEditingJob(null);
    setFormData({
      title: '',
      department: '',
      location: '',
      employment_type: 'full-time',
      description: '',
      requirements: '',
      responsibilities: '',
      salary_range: '',
      status: 'active'
    });
    setShowModal(true);
  };

  const openEditModal = (job) => {
    setEditingJob(job);
    setFormData({
      title: job.title || '',
      department: job.department || '',
      location: job.location || '',
      employment_type: job.employment_type || 'full-time',
      description: job.description || '',
      requirements: job.requirements || '',
      responsibilities: job.responsibilities || '',
      salary_range: job.salary_range || '',
      status: job.status || 'active'
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingJob(null);
  };

  const departments = ['Engineering', 'Operations', 'Sales', 'Marketing', 'Support', 'HR', 'Finance'];
  const employmentTypes = ['full-time', 'part-time', 'contract', 'internship'];

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Listings</h1>
            <p className="text-gray-600">Manage career opportunities</p>
          </div>
          <Button onClick={openCreateModal} className="mt-4 sm:mt-0 bg-green-600 hover:bg-green-700">
            <Plus className="w-5 h-5 mr-2" />
            Post Job
          </Button>
        </div>

        {/* Jobs List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading...</div>
          ) : jobs.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center text-gray-500">
              No job listings yet. Click "Post Job" to create one.
            </div>
          ) : (
            jobs.map((job) => (
              <div key={job.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="bg-indigo-100 p-3 rounded-lg">
                      <Briefcase className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                      <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
                        <span className="flex items-center">
                          <Users className="w-4 h-4 mr-1" />
                          {job.department}
                        </span>
                        <span className="flex items-center">
                          <MapPin className="w-4 h-4 mr-1" />
                          {job.location}
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {job.employment_type}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 mt-4 md:mt-0">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      job.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {job.status}
                    </span>
                    <button
                      onClick={() => openEditModal(job)}
                      className="text-gray-600 hover:text-blue-600 p-2"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(job.id)}
                      className="text-gray-600 hover:text-red-600 p-2"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                {job.description && (
                  <p className="text-gray-600 mt-4 text-sm line-clamp-2">{job.description}</p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {editingJob ? 'Edit Job Posting' : 'Post New Job'}
              </h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div>
                <Label htmlFor="title">Job Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  className="mt-2"
                  placeholder="e.g., EV Service Technician"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="department">Department</Label>
                  <select
                    id="department"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    <option value="">Select department</option>
                    {departments.map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="mt-2"
                    placeholder="Delhi NCR"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="employment_type">Employment Type</Label>
                  <select
                    id="employment_type"
                    value={formData.employment_type}
                    onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                    className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    {employmentTypes.map(type => (
                      <option key={type} value={type}>
                        {type.charAt(0).toUpperCase() + type.slice(1).replace('-', ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="salary_range">Salary Range</Label>
                  <Input
                    id="salary_range"
                    value={formData.salary_range}
                    onChange={(e) => setFormData({ ...formData, salary_range: e.target.value })}
                    className="mt-2"
                    placeholder="e.g., 4-6 LPA"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="description">Job Description *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  className="mt-2"
                  rows={4}
                  placeholder="Describe the role..."
                />
              </div>

              <div>
                <Label htmlFor="requirements">Requirements</Label>
                <Textarea
                  id="requirements"
                  value={formData.requirements}
                  onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
                  className="mt-2"
                  rows={3}
                  placeholder="Skills and qualifications required..."
                />
              </div>

              <div>
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                  <option value="draft">Draft</option>
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={closeModal}>Cancel</Button>
                <Button type="submit" className="bg-green-600 hover:bg-green-700">
                  <Save className="w-4 h-4 mr-2" />
                  {editingJob ? 'Update Job' : 'Post Job'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default Jobs;

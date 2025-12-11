import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { authService } from '../../utils/auth';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Wrench,
  Plus,
  Edit,
  Trash2,
  X,
  Save,
  Zap,
  Battery,
  Settings,
  Truck,
  AlertCircle
} from 'lucide-react';

const Services = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    short_description: '',
    long_description: '',
    vehicle_segments: [],
    pricing_model: 'inspection_based',
    price: '',
    display_order: 0,
    is_active: true,
    status: 'active',
    icon: 'Wrench',
    features: []
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  const vehicleSegmentOptions = ['2W', '3W', '4W', 'Commercial'];
  const pricingModelOptions = [
    { value: 'fixed', label: 'Fixed Price' },
    { value: 'inspection_based', label: 'Inspection Based' },
    { value: 'contact_for_quote', label: 'Contact for Quote' }
  ];
  const iconOptions = ['Wrench', 'Zap', 'Battery', 'Settings', 'Truck'];

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      setLoading(true);
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/services/`, { headers });
      if (response.ok) {
        const data = await response.json();
        setServices(data.services || []);
      }
    } catch (error) {
      console.error('Error fetching services:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    
    try {
      const headers = authService.getAuthHeaders();
      const url = editingService
        ? `${API_URL}/api/admin/services/${editingService.id}`
        : `${API_URL}/api/admin/services/`;
      const method = editingService ? 'PUT' : 'POST';

      // Prepare data matching backend model
      const submitData = {
        title: formData.title,
        slug: formData.slug,
        short_description: formData.short_description,
        long_description: formData.long_description,
        vehicle_segments: formData.vehicle_segments,
        pricing_model: formData.pricing_model,
        price: formData.price ? parseFloat(formData.price) : null,
        display_order: parseInt(formData.display_order) || 0,
        is_active: formData.is_active,
        icon: formData.icon
      };

      const response = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(submitData)
      });

      if (response.ok) {
        fetchServices();
        closeModal();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to save service');
      }
    } catch (error) {
      console.error('Error saving service:', error);
      setError('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (serviceId) => {
    if (!window.confirm('Are you sure you want to delete this service?')) return;
    try {
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/services/${serviceId}`, {
        method: 'DELETE',
        headers
      });
      if (response.ok) {
        fetchServices();
      }
    } catch (error) {
      console.error('Error deleting service:', error);
    }
  };

  const openCreateModal = () => {
    setEditingService(null);
    setError('');
    setFormData({
      title: '',
      slug: '',
      short_description: '',
      long_description: '',
      vehicle_segments: [],
      pricing_model: 'inspection_based',
      price: '',
      display_order: services.length + 1,
      is_active: true,
      status: 'active',
      icon: 'Wrench',
      features: []
    });
    setShowModal(true);
  };

  const openEditModal = (service) => {
    setEditingService(service);
    setError('');
    setFormData({
      title: service.title || '',
      slug: service.slug || '',
      short_description: service.short_description || '',
      long_description: service.long_description || '',
      vehicle_segments: service.vehicle_segments || [],
      pricing_model: service.pricing_model || 'inspection_based',
      price: service.price || '',
      display_order: service.display_order || 0,
      is_active: service.is_active !== false,
      status: service.status || 'active',
      icon: service.icon || 'Wrench',
      features: service.features || []
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingService(null);
    setError('');
  };

  const generateSlug = (title) => {
    return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
  };

  const toggleVehicleSegment = (segment) => {
    const segments = formData.vehicle_segments.includes(segment)
      ? formData.vehicle_segments.filter(s => s !== segment)
      : [...formData.vehicle_segments, segment];
    setFormData({ ...formData, vehicle_segments: segments });
  };

  const getIcon = (iconName) => {
    const icons = { Wrench, Zap, Battery, Settings, Truck };
    return icons[iconName] || Wrench;
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Services</h1>
            <p className="text-gray-600">Manage service offerings ({services.length} total)</p>
          </div>
          <Button onClick={openCreateModal} className="mt-4 sm:mt-0 bg-green-600 hover:bg-green-700">
            <Plus className="w-5 h-5 mr-2" />
            Add Service
          </Button>
        </div>

        {/* Services Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div className="col-span-full text-center py-12 text-gray-500">Loading...</div>
          ) : services.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              No services yet. Click &quot;Add Service&quot; to create one.
            </div>
          ) : (
            services.map((service) => {
              const Icon = getIcon(service.icon);
              return (
                <div key={service.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="bg-green-100 p-3 rounded-lg">
                      <Icon className="w-6 h-6 text-green-600" />
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      service.is_active || service.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {service.is_active || service.status === 'active' ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{service.title}</h3>
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {service.short_description || service.long_description}
                  </p>
                  {service.vehicle_segments && service.vehicle_segments.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {service.vehicle_segments.map(seg => (
                        <span key={seg} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                          {seg}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => openEditModal(service)}
                      className="flex-1 flex items-center justify-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(service.id)}
                      className="px-3 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {editingService ? 'Edit Service' : 'Add New Service'}
              </h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            {error && (
              <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Title */}
              <div>
                <Label htmlFor="title">Service Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => {
                    setFormData({
                      ...formData,
                      title: e.target.value,
                      slug: generateSlug(e.target.value)
                    });
                  }}
                  required
                  className="mt-1"
                  placeholder="e.g., Battery Health Check"
                />
              </div>

              {/* Slug */}
              <div>
                <Label htmlFor="slug">URL Slug</Label>
                <Input
                  id="slug"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  className="mt-1"
                  placeholder="battery-health-check"
                />
              </div>

              {/* Short Description */}
              <div>
                <Label htmlFor="short_description">Short Description *</Label>
                <Input
                  id="short_description"
                  value={formData.short_description}
                  onChange={(e) => setFormData({ ...formData, short_description: e.target.value })}
                  required
                  className="mt-1"
                  placeholder="Brief description for cards"
                />
              </div>

              {/* Long Description */}
              <div>
                <Label htmlFor="long_description">Full Description *</Label>
                <Textarea
                  id="long_description"
                  value={formData.long_description}
                  onChange={(e) => setFormData({ ...formData, long_description: e.target.value })}
                  required
                  className="mt-1"
                  rows={4}
                  placeholder="Detailed service description..."
                />
              </div>

              {/* Vehicle Segments */}
              <div>
                <Label>Vehicle Segments *</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {vehicleSegmentOptions.map(segment => (
                    <button
                      key={segment}
                      type="button"
                      onClick={() => toggleVehicleSegment(segment)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        formData.vehicle_segments.includes(segment)
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {segment}
                    </button>
                  ))}
                </div>
              </div>

              {/* Pricing Model & Price */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="pricing_model">Pricing Model</Label>
                  <select
                    id="pricing_model"
                    value={formData.pricing_model}
                    onChange={(e) => setFormData({ ...formData, pricing_model: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    {pricingModelOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="price">Price (₹)</Label>
                  <Input
                    id="price"
                    type="number"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="mt-1"
                    placeholder="e.g., 1499"
                    disabled={formData.pricing_model !== 'fixed'}
                  />
                </div>
              </div>

              {/* Icon & Display Order */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="icon">Icon</Label>
                  <select
                    id="icon"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    {iconOptions.map(icon => (
                      <option key={icon} value={icon}>{icon}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label htmlFor="display_order">Display Order</Label>
                  <Input
                    id="display_order"
                    type="number"
                    value={formData.display_order}
                    onChange={(e) => setFormData({ ...formData, display_order: e.target.value })}
                    className="mt-1"
                    placeholder="1"
                  />
                </div>
              </div>

              {/* Active Toggle */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                />
                <Label htmlFor="is_active" className="mb-0">Active (visible on website)</Label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={closeModal}>Cancel</Button>
                <Button type="submit" className="bg-green-600 hover:bg-green-700" disabled={saving}>
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Saving...' : editingService ? 'Update Service' : 'Create Service'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default Services;

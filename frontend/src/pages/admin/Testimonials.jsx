import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { authService } from '../../utils/auth';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Star,
  Plus,
  Edit,
  Trash2,
  X,
  Save,
  Quote,
  AlertCircle
} from 'lucide-react';

const Testimonials = () => {
  const [testimonials, setTestimonials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTestimonial, setEditingTestimonial] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    company: '',
    quote: '',
    rating: 5,
    category: '',
    avatar_url: '',
    status: 'active',
    featured: false
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchTestimonials();
  }, []);

  const fetchTestimonials = async () => {
    try {
      setLoading(true);
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/testimonials`, { headers });
      if (response.ok) {
        const data = await response.json();
        setTestimonials(data.testimonials || []);
      }
    } catch (error) {
      console.error('Error fetching testimonials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const headers = authService.getAuthHeaders();
      const url = editingTestimonial
        ? `${API_URL}/api/admin/testimonials${editingTestimonial.id}`
        : `${API_URL}/api/admin/testimonials`;
      const method = editingTestimonial ? 'PUT' : 'POST';

      // Map to backend model fields
      const submitData = {
        name: formData.name,
        company: formData.company,
        role: formData.role,
        quote: formData.quote,
        rating: parseInt(formData.rating) || 5,
        featured: formData.featured || false,
        category: formData.category,
        status: formData.status,
        avatar: formData.avatar_url || null
      };

      const response = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(submitData)
      });

      if (response.ok) {
        fetchTestimonials();
        closeModal();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to save testimonial');
      }
    } catch (error) {
      console.error('Error saving testimonial:', error);
      setError('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (testimonialId) => {
    if (!window.confirm('Are you sure you want to delete this testimonial?')) return;
    try {
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/testimonials${testimonialId}`, {
        method: 'DELETE',
        headers
      });
      if (response.ok) {
        fetchTestimonials();
      }
    } catch (error) {
      console.error('Error deleting testimonial:', error);
    }
  };

  const openCreateModal = () => {
    setEditingTestimonial(null);
    setError('');
    setFormData({
      name: '',
      role: '',
      company: '',
      quote: '',
      rating: 5,
      category: '',
      avatar_url: '',
      status: 'active',
      featured: false
    });
    setShowModal(true);
  };

  const openEditModal = (testimonial) => {
    setEditingTestimonial(testimonial);
    setError('');
    setFormData({
      name: testimonial.name || '',
      role: testimonial.role || '',
      company: testimonial.company || '',
      quote: testimonial.quote || '',
      rating: testimonial.rating || 5,
      category: testimonial.category || '',
      avatar_url: testimonial.avatar || '',
      status: testimonial.status || 'active',
      featured: testimonial.featured || false
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingTestimonial(null);
    setError('');
  };

  const categories = ['2w-fleet', '3w-fleet', '4w-fleet', 'logistics', 'oem', 'leasing', 'startup', 'individual'];

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Testimonials</h1>
            <p className="text-gray-600">Manage customer reviews</p>
          </div>
          <Button onClick={openCreateModal} className="mt-4 sm:mt-0 bg-green-600 hover:bg-green-700">
            <Plus className="w-5 h-5 mr-2" />
            Add Review
          </Button>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {loading ? (
            <div className="col-span-full text-center py-12 text-gray-500">Loading...</div>
          ) : testimonials.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              No testimonials yet. Click &quot;Add Review&quot; to create one.
            </div>
          ) : (
            testimonials.map((testimonial) => (
              <div key={testimonial.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-semibold">
                      {testimonial.name?.charAt(0) || 'T'}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{testimonial.name}</h3>
                      <p className="text-sm text-gray-500">{testimonial.role}, {testimonial.company}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    {[...Array(testimonial.rating || 5)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                    ))}
                  </div>
                </div>
                <div className="relative">
                  <Quote className="absolute -top-2 -left-2 w-8 h-8 text-gray-200" />
                  <p className="text-gray-700 italic pl-6">&quot;{testimonial.quote}&quot;</p>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                    {testimonial.category || 'General'}
                  </span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => openEditModal(testimonial)}
                      className="text-gray-600 hover:text-blue-600 p-1"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(testimonial.id)}
                      className="text-gray-600 hover:text-red-600 p-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {editingTestimonial ? 'Edit Testimonial' : 'Add New Testimonial'}
              </h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  {error}
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="mt-2"
                    placeholder="Customer name"
                  />
                </div>
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="mt-2"
                    placeholder="Fleet Manager"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="mt-2"
                    placeholder="Company name"
                  />
                </div>
                <div>
                  <Label htmlFor="category">Category</Label>
                  <select
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    <option value="">Select category</option>
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <Label htmlFor="quote">Quote *</Label>
                <Textarea
                  id="quote"
                  value={formData.quote}
                  onChange={(e) => setFormData({ ...formData, quote: e.target.value })}
                  required
                  className="mt-2"
                  rows={4}
                  placeholder="Customer testimonial..."
                />
              </div>

              <div>
                <Label htmlFor="rating">Rating</Label>
                <div className="flex items-center space-x-2 mt-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setFormData({ ...formData, rating: star })}
                      className="focus:outline-none"
                    >
                      <Star className={`w-8 h-8 ${
                        star <= formData.rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                      }`} />
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={closeModal}>Cancel</Button>
                <Button type="submit" className="bg-green-600 hover:bg-green-700" disabled={saving}>
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Saving...' : editingTestimonial ? 'Update' : 'Add Testimonial'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default Testimonials;

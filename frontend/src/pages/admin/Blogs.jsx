import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { authService } from '../../utils/auth';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  FileText,
  Plus,
  Edit,
  Trash2,
  X,
  Save,
  Eye,
  EyeOff
} from 'lucide-react';

const Blogs = () => {
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBlog, setEditingBlog] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    excerpt: '',
    content: '',
    category: '',
    thumbnail_image: '',
    tags: [],
    status: 'draft'
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchBlogs();
  }, []);

  const fetchBlogs = async () => {
    try {
      setLoading(true);
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/blogs`, { headers });
      if (response.ok) {
        const data = await response.json();
        setBlogs(data.blogs || []);
      }
    } catch (error) {
      console.error('Error fetching blogs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const headers = authService.getAuthHeaders();
      const url = editingBlog
        ? `${API_URL}/api/admin/blogs/${editingBlog.id}`
        : `${API_URL}/api/admin/blogs`;
      const method = editingBlog ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        fetchBlogs();
        closeModal();
      }
    } catch (error) {
      console.error('Error saving blog:', error);
    }
  };

  const handleDelete = async (blogId) => {
    if (!window.confirm('Are you sure you want to delete this blog post?')) return;
    try {
      const headers = authService.getAuthHeaders();
      const response = await fetch(`${API_URL}/api/admin/blogs/${blogId}`, {
        method: 'DELETE',
        headers
      });
      if (response.ok) {
        fetchBlogs();
      }
    } catch (error) {
      console.error('Error deleting blog:', error);
    }
  };

  const togglePublish = async (blog) => {
    try {
      const headers = authService.getAuthHeaders();
      const newStatus = blog.status === 'published' ? 'draft' : 'published';
      const response = await fetch(`${API_URL}/api/admin/blogs/${blog.id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ ...blog, status: newStatus })
      });
      if (response.ok) {
        fetchBlogs();
      }
    } catch (error) {
      console.error('Error updating blog status:', error);
    }
  };

  const openCreateModal = () => {
    setEditingBlog(null);
    setFormData({
      title: '',
      slug: '',
      excerpt: '',
      content: '',
      category: '',
      thumbnail_image: '',
      tags: [],
      status: 'draft'
    });
    setShowModal(true);
  };

  const openEditModal = (blog) => {
    setEditingBlog(blog);
    setFormData({
      title: blog.title || '',
      slug: blog.slug || '',
      excerpt: blog.excerpt || '',
      content: blog.content || '',
      category: blog.category || '',
      thumbnail_image: blog.thumbnail_image || '',
      tags: blog.tags || [],
      status: blog.status || 'draft'
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingBlog(null);
  };

  const generateSlug = (title) => {
    return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
  };

  const categories = ['Fleet Ops', 'EV Tech Deep Dive', 'Industry News', 'Company Updates', 'Tips & Guides'];

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Blog Posts</h1>
            <p className="text-gray-600">Manage blog content</p>
          </div>
          <Button onClick={openCreateModal} className="mt-4 sm:mt-0 bg-green-600 hover:bg-green-700">
            <Plus className="w-5 h-5 mr-2" />
            Write Post
          </Button>
        </div>

        {/* Blog Posts Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Post</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500">Loading...</td>
                  </tr>
                ) : blogs.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                      No blog posts yet. Click &quot;Write Post&quot; to create one.
                    </td>
                  </tr>
                ) : (
                  blogs.map((blog) => (
                    <tr key={blog.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-3">
                          <div className="bg-purple-100 p-2 rounded">
                            <FileText className="w-5 h-5 text-purple-600" />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">{blog.title}</div>
                            <div className="text-sm text-gray-500 truncate max-w-xs">{blog.excerpt}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                          {blog.category || 'Uncategorized'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          blog.status === 'published' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {blog.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(blog.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => togglePublish(blog)}
                            className="text-gray-600 hover:text-green-600 p-1"
                            title={blog.status === 'published' ? 'Unpublish' : 'Publish'}
                          >
                            {blog.status === 'published' ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                          </button>
                          <button
                            onClick={() => openEditModal(blog)}
                            className="text-gray-600 hover:text-blue-600 p-1"
                          >
                            <Edit className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(blog.id)}
                            className="text-gray-600 hover:text-red-600 p-1"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {editingBlog ? 'Edit Blog Post' : 'Write New Post'}
              </h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div>
                <Label htmlFor="title">Title *</Label>
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
                  className="mt-2"
                  placeholder="Blog post title"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="slug">URL Slug</Label>
                  <Input
                    id="slug"
                    value={formData.slug}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                    className="mt-2"
                    placeholder="post-url-slug"
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
                <Label htmlFor="excerpt">Excerpt</Label>
                <Textarea
                  id="excerpt"
                  value={formData.excerpt}
                  onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
                  className="mt-2"
                  rows={2}
                  placeholder="Brief summary for previews..."
                />
              </div>

              <div>
                <Label htmlFor="content">Content *</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  required
                  className="mt-2"
                  rows={10}
                  placeholder="Write your blog post content here..."
                />
              </div>

              <div>
                <Label htmlFor="thumbnail_image">Thumbnail Image URL</Label>
                <Input
                  id="thumbnail_image"
                  value={formData.thumbnail_image}
                  onChange={(e) => setFormData({ ...formData, thumbnail_image: e.target.value })}
                  className="mt-2"
                  placeholder="https://example.com/image.jpg"
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
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={closeModal}>Cancel</Button>
                <Button type="submit" className="bg-green-600 hover:bg-green-700">
                  <Save className="w-4 h-4 mr-2" />
                  {editingBlog ? 'Update Post' : 'Publish Post'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default Blogs;

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import AdminLayout from '../../components/admin/AdminLayout';
import { authService } from '../../utils/auth';
import {
  Calendar,
  MessageSquare,
  Wrench,
  FileText,
  Star,
  Briefcase,
  TrendingUp,
  Clock,
  Users,
  CheckCircle
} from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    bookings: { total: 0, pending: 0 },
    contacts: { total: 0, unread: 0 },
    services: { total: 0 },
    blogs: { total: 0, published: 0 },
    testimonials: { total: 0 },
    jobs: { total: 0, active: 0 }
  });
  const [recentBookings, setRecentBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const headers = authService.getAuthHeaders();

      // Fetch bookings
      const bookingsRes = await fetch(`${API_URL}/api/admin/bookings?limit=5`, { headers });
      if (bookingsRes.ok) {
        const bookingsData = await bookingsRes.json();
        setRecentBookings(bookingsData.bookings || []);
        setStats(prev => ({
          ...prev,
          bookings: {
            total: bookingsData.total || 0,
            pending: (bookingsData.bookings || []).filter(b => b.status === 'pending').length
          }
        }));
      }

      // Fetch contacts
      const contactsRes = await fetch(`${API_URL}/api/admin/contacts`, { headers });
      if (contactsRes.ok) {
        const contactsData = await contactsRes.json();
        setStats(prev => ({
          ...prev,
          contacts: {
            total: contactsData.total || 0,
            unread: (contactsData.contacts || []).filter(c => c.status === 'unread').length
          }
        }));
      }

      // Fetch services
      const servicesRes = await fetch(`${API_URL}/api/admin/services`, { headers });
      if (servicesRes.ok) {
        const servicesData = await servicesRes.json();
        setStats(prev => ({
          ...prev,
          services: { total: servicesData.total || 0 }
        }));
      }

      // Fetch blogs
      const blogsRes = await fetch(`${API_URL}/api/admin/blogs`, { headers });
      if (blogsRes.ok) {
        const blogsData = await blogsRes.json();
        setStats(prev => ({
          ...prev,
          blogs: {
            total: blogsData.total || 0,
            published: (blogsData.blogs || []).filter(b => b.is_published === true).length
          }
        }));
      }

      // Fetch testimonials
      const testimonialsRes = await fetch(`${API_URL}/api/admin/testimonials`, { headers });
      if (testimonialsRes.ok) {
        const testimonialsData = await testimonialsRes.json();
        setStats(prev => ({
          ...prev,
          testimonials: { total: testimonialsData.total || 0 }
        }));
      }

      // Fetch jobs
      const jobsRes = await fetch(`${API_URL}/api/admin/jobs`, { headers });
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setStats(prev => ({
          ...prev,
          jobs: {
            total: jobsData.total || 0,
            active: (jobsData.jobs || []).filter(j => j.status === 'active').length
          }
        }));
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Bookings',
      value: stats.bookings.total,
      subtitle: `${stats.bookings.pending} pending`,
      icon: Calendar,
      color: 'bg-blue-500',
      href: '/admin/bookings'
    },
    {
      title: 'Contact Messages',
      value: stats.contacts.total,
      subtitle: `${stats.contacts.unread} unread`,
      icon: MessageSquare,
      color: 'bg-green-500',
      href: '/admin/contacts'
    },
    {
      title: 'Services',
      value: stats.services.total,
      subtitle: 'Active services',
      icon: Wrench,
      color: 'bg-orange-500',
      href: '/admin/services'
    },
    {
      title: 'Blog Posts',
      value: stats.blogs.total,
      subtitle: `${stats.blogs.published} published`,
      icon: FileText,
      color: 'bg-purple-500',
      href: '/admin/blogs'
    },
    {
      title: 'Testimonials',
      value: stats.testimonials.total,
      subtitle: 'Customer reviews',
      icon: Star,
      color: 'bg-yellow-500',
      href: '/admin/testimonials'
    },
    {
      title: 'Job Listings',
      value: stats.jobs.total,
      subtitle: `${stats.jobs.active} active`,
      icon: Briefcase,
      color: 'bg-indigo-500',
      href: '/admin/jobs'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'confirmed': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-purple-100 text-purple-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome to Battwheels Garages Admin Panel</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.title}
                to={card.href}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{card.title}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">
                      {loading ? '...' : card.value}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{card.subtitle}</p>
                  </div>
                  <div className={`${card.color} p-3 rounded-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Recent Bookings */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Bookings</h2>
            <Link to="/admin/bookings" className="text-sm text-green-600 hover:text-green-700 font-medium">
              View All
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {loading ? (
              <div className="p-6 text-center text-gray-500">Loading...</div>
            ) : recentBookings.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No bookings yet</div>
            ) : (
              recentBookings.map((booking) => (
                <div key={booking.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex items-center space-x-4">
                    <div className="bg-gray-100 p-2 rounded-full">
                      <Calendar className="w-5 h-5 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{booking.name}</p>
                      <p className="text-sm text-gray-500">{booking.service_type} - {booking.vehicle_category}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(booking.status)}`}>
                      {booking.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(booking.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link
              to="/admin/services"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Wrench className="w-8 h-8 text-green-600 mb-2" />
              <span className="text-sm font-medium text-gray-700">Add Service</span>
            </Link>
            <Link
              to="/admin/blogs"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <FileText className="w-8 h-8 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-gray-700">Write Blog</span>
            </Link>
            <Link
              to="/admin/jobs"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Briefcase className="w-8 h-8 text-indigo-600 mb-2" />
              <span className="text-sm font-medium text-gray-700">Post Job</span>
            </Link>
            <Link
              to="/admin/testimonials"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Star className="w-8 h-8 text-yellow-600 mb-2" />
              <span className="text-sm font-medium text-gray-700">Add Review</span>
            </Link>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default Dashboard;

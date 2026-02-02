import React, { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { authService } from '../../utils/auth';
import { Button } from '../../components/ui/button';
import {
  MessageSquare,
  Mail,
  Phone,
  Clock,
  Eye,
  X,
  Check,
  Inbox
} from 'lucide-react';

const Contacts = () => {
  const [contacts, setContacts] = useState([]);
  const [fleetEnquiries, setFleetEnquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('contacts');
  const [selectedItem, setSelectedItem] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const headers = authService.getAuthHeaders();

      // Fetch contacts
      const contactsRes = await fetch(`${API_URL}/api/admin/contacts`, { headers });
      if (contactsRes.ok) {
        const data = await contactsRes.json();
        setContacts(data.contacts || []);
      }

      // Fetch fleet enquiries
      const fleetRes = await fetch(`${API_URL}/api/fleet-enquiries/`, { headers });
      if (fleetRes.ok) {
        const data = await fleetRes.json();
        setFleetEnquiries(data.enquiries || data || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateContactStatus = async (contactId, newStatus) => {
    try {
      const headers = authService.getAuthHeaders();
      const response = await fetch(
        `${API_URL}/api/admin/contacts${contactId}`,
        {
          method: 'PUT',
          headers,
          body: JSON.stringify({ status: newStatus })
        }
      );
      if (response.ok) {
        fetchData();
      }
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const viewItem = (item) => {
    setSelectedItem(item);
    setShowModal(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'unread': return 'bg-yellow-100 text-yellow-800';
      case 'read': return 'bg-blue-100 text-blue-800';
      case 'responded': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contacts & Enquiries</h1>
          <p className="text-gray-600">Manage contact messages and fleet enquiries</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('contacts')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'contacts'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <MessageSquare className="w-5 h-5 inline mr-2" />
              Contact Messages ({contacts.length})
            </button>
            <button
              onClick={() => setActiveTab('fleet')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'fleet'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Inbox className="w-5 h-5 inline mr-2" />
              Fleet Enquiries ({fleetEnquiries.length})
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeTab === 'contacts' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-gray-500">Loading...</td>
                    </tr>
                  ) : contacts.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-gray-500">No contact messages yet</td>
                    </tr>
                  ) : (
                    contacts.map((contact) => (
                      <tr key={contact.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{contact.name}</div>
                          <div className="text-sm text-gray-500">{contact.email}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900 truncate max-w-xs">{contact.message}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(contact.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(contact.status)}`}>
                            {contact.status || 'unread'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => viewItem(contact)}
                              className="text-gray-600 hover:text-green-600 p-1"
                            >
                              <Eye className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => updateContactStatus(contact.id, 'responded')}
                              className="text-gray-600 hover:text-green-600 p-1"
                              title="Mark as Responded"
                            >
                              <Check className="w-5 h-5" />
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
        )}

        {activeTab === 'fleet' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fleet Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-gray-500">Loading...</td>
                    </tr>
                  ) : fleetEnquiries.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-gray-500">No fleet enquiries yet</td>
                    </tr>
                  ) : (
                    fleetEnquiries.map((enquiry) => (
                      <tr key={enquiry.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{enquiry.company_name}</div>
                          <div className="text-sm text-gray-500">{enquiry.industry}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{enquiry.contact_name}</div>
                          <div className="text-sm text-gray-500">{enquiry.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {enquiry.fleet_size}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(enquiry.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => viewItem(enquiry)}
                            className="text-gray-600 hover:text-green-600 p-1"
                          >
                            <Eye className="w-5 h-5" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showModal && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {activeTab === 'contacts' ? 'Contact Message' : 'Fleet Enquiry'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-medium">{selectedItem.name || selectedItem.contact_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{selectedItem.email}</p>
                </div>
                {selectedItem.phone && (
                  <div>
                    <p className="text-sm text-gray-500">Phone</p>
                    <p className="font-medium">{selectedItem.phone}</p>
                  </div>
                )}
                {selectedItem.company_name && (
                  <div>
                    <p className="text-sm text-gray-500">Company</p>
                    <p className="font-medium">{selectedItem.company_name}</p>
                  </div>
                )}
                {selectedItem.fleet_size && (
                  <div>
                    <p className="text-sm text-gray-500">Fleet Size</p>
                    <p className="font-medium">{selectedItem.fleet_size}</p>
                  </div>
                )}
              </div>
              {selectedItem.message && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Message</p>
                  <p className="bg-gray-50 p-4 rounded-lg text-gray-700">{selectedItem.message}</p>
                </div>
              )}
              {selectedItem.requirements && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Requirements</p>
                  <p className="bg-gray-50 p-4 rounded-lg text-gray-700">{selectedItem.requirements}</p>
                </div>
              )}
              <div className="text-sm text-gray-500">
                Submitted: {new Date(selectedItem.created_at).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default Contacts;

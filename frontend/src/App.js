import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { Toaster } from './components/ui/toaster';
import FloatingWhatsApp from './components/common/FloatingWhatsApp';

// Public Pages
import Home from './pages/Home';
import About from './pages/About';
import Services from './pages/Services';
import ServiceDetail from './pages/ServiceDetail';
import BattwheelsOS from './pages/BattwheelsOS';
import Industries from './pages/Industries';
import Plans from './pages/Plans';
import Blog from './pages/Blog';
import BlogPost from './pages/BlogPost';
import Careers from './pages/Careers';
import Contact from './pages/Contact';
import BookService from './pages/BookService';
import FleetOEM from './pages/FleetOEM';
import FAQ from './pages/FAQ';

// Admin Pages
import AdminLogin from './pages/admin/Login';
import AdminDashboard from './pages/admin/Dashboard';
import AdminBookings from './pages/admin/Bookings';
import AdminContacts from './pages/admin/Contacts';
import AdminServices from './pages/admin/Services';
import AdminBlogs from './pages/admin/Blogs';
import AdminTestimonials from './pages/admin/Testimonials';
import AdminJobs from './pages/admin/Jobs';

// Admin Route Protection
import ProtectedRoute from './components/admin/ProtectedRoute';

// Placeholder pages (Privacy & Terms)
const PlaceholderPage = ({ title }) => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">{title}</h1>
      <p className="text-gray-600">Page under construction...</p>
    </div>
  </div>
);

function App() {
  return (
    <HelmetProvider>
      <div className="App">
        <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/services" element={<Services />} />
          <Route path="/services/:slug" element={<ServiceDetail />} />
          <Route path="/battwheels-os" element={<BattwheelsOS />} />
          <Route path="/industries" element={<Industries />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/blog/:slug" element={<BlogPost />} />
          <Route path="/careers" element={<Careers />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/book-service" element={<BookService />} />
          <Route path="/fleet-oem" element={<FleetOEM />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/privacy" element={<PlaceholderPage title="Privacy Policy" />} />
          <Route path="/terms" element={<PlaceholderPage title="Terms of Service" />} />
          
          {/* Admin Routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/bookings" element={<ProtectedRoute><AdminBookings /></ProtectedRoute>} />
          <Route path="/admin/contacts" element={<ProtectedRoute><AdminContacts /></ProtectedRoute>} />
          <Route path="/admin/services" element={<ProtectedRoute><AdminServices /></ProtectedRoute>} />
          <Route path="/admin/blogs" element={<ProtectedRoute><AdminBlogs /></ProtectedRoute>} />
          <Route path="/admin/testimonials" element={<ProtectedRoute><AdminTestimonials /></ProtectedRoute>} />
          <Route path="/admin/jobs" element={<ProtectedRoute><AdminJobs /></ProtectedRoute>} />
        </Routes>
        </BrowserRouter>
        <Toaster />
        <FloatingWhatsApp />
      </div>
    </HelmetProvider>
  );
}

export default App;
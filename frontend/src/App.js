import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui/toaster';

// Pages
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
    <div className="App">
      <BrowserRouter>
        <Routes>
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
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
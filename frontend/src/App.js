import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';

// Placeholder pages (will build these next)
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
          <Route path="/about" element={<PlaceholderPage title="About Us" />} />
          <Route path="/services" element={<PlaceholderPage title="All Services" />} />
          <Route path="/services/:slug" element={<PlaceholderPage title="Service Detail" />} />
          <Route path="/battwheels-os" element={<PlaceholderPage title="Battwheels OS" />} />
          <Route path="/industries" element={<PlaceholderPage title="Industries We Serve" />} />
          <Route path="/plans" element={<PlaceholderPage title="Subscription Plans" />} />
          <Route path="/blog" element={<PlaceholderPage title="Blog" />} />
          <Route path="/blog/:slug" element={<PlaceholderPage title="Blog Post" />} />
          <Route path="/careers" element={<PlaceholderPage title="Careers" />} />
          <Route path="/contact" element={<PlaceholderPage title="Contact Us" />} />
          <Route path="/book-service" element={<PlaceholderPage title="Book EV Service" />} />
          <Route path="/fleet-oem" element={<PlaceholderPage title="Fleet & OEM Enquiry" />} />
          <Route path="/faq" element={<PlaceholderPage title="FAQ" />} />
          <Route path="/privacy" element={<PlaceholderPage title="Privacy Policy" />} />
          <Route path="/terms" element={<PlaceholderPage title="Terms of Service" />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
import React from 'react';
import { Link } from 'react-router-dom';
import { Phone, Mail, MapPin, Clock, Facebook, Instagram, Linkedin, MessageCircle, ChevronRight, Zap } from 'lucide-react';
import { companyInfo } from '../../data/mockData';

const Footer = () => {
  // Operational cities data - easily maintainable
  const operationalCities = [
    { city: "New Delhi", area: "Okhla Phase 2 (HQ)", state: "Delhi" },
    { city: "New Delhi", area: "Dwarka Sector 28", state: "Delhi" },
    { city: "Noida", area: "Sector 68", state: "Uttar Pradesh" },
    { city: "Gurugram", area: "Pace City I", state: "Haryana" },
    { city: "Bengaluru", area: "Nelamangala", state: "Karnataka" },
    { city: "Chennai", area: "Thiruverkadu", state: "Tamil Nadu" },
    { city: "Hyderabad", area: "Kompally", state: "Telangana" },
    { city: "Jaipur", area: "Vishwakarma IA", state: "Rajasthan" },
    { city: "Lucknow", area: "Ashiyana", state: "Uttar Pradesh" },
    { city: "Ulhasnagar", area: "", state: "Maharashtra" },
    { city: "Pamarru", area: "Arandal Peta", state: "Andhra Pradesh" },
  ];

  return (
    <footer className="bg-gray-900 text-white">
      {/* Main Footer Content */}
      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-12 lg:gap-8">
          
          {/* Company Info - Wider */}
          <div className="lg:col-span-4">
            <div className="mb-8">
              <img 
                src="/assets/battwheels-logo-new-transparent.png" 
                alt="Battwheels Garages" 
                className="h-14 w-auto brightness-0 invert"
              />
            </div>
            <p className="text-gray-400 leading-relaxed mb-6">
              {companyInfo.tagline}
            </p>
            <p className="text-sm text-gray-500 mb-8">
              India's #1 onsite EV after-sales & maintenance partner
            </p>
            
            {/* Social Media */}
            <div className="flex items-center gap-3">
              <a 
                href="https://wa.me/918076331607" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#25D366] transition-all duration-300"
                aria-label="WhatsApp"
              >
                <MessageCircle className="w-5 h-5" />
              </a>
              <a 
                href="https://www.facebook.com/battwheelsgarages" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-blue-600 transition-all duration-300"
                aria-label="Facebook"
              >
                <Facebook className="w-5 h-5" />
              </a>
              <a 
                href="https://www.instagram.com/battwheelsgarages" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-gradient-to-br hover:from-purple-600 hover:to-pink-500 transition-all duration-300"
                aria-label="Instagram"
              >
                <Instagram className="w-5 h-5" />
              </a>
              <a 
                href="https://www.linkedin.com/company/battwheels-garages" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-blue-700 transition-all duration-300"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div className="lg:col-span-2">
            <h3 className="text-white font-semibold text-lg mb-6">Quick Links</h3>
            <ul className="space-y-3">
              {[
                { to: "/", label: "Home" },
                { to: "/about", label: "About Us" },
                { to: "/battwheels-os", label: "Battwheels OS™" },
                { to: "/services", label: "Services" },
                { to: "/industries", label: "Industries" },
                { to: "/plans", label: "Subscriptions" },
                { to: "/blog", label: "Blog" },
                { to: "/careers", label: "Careers" },
              ].map((link) => (
                <li key={link.to}>
                  <Link 
                    to={link.to} 
                    className="text-gray-400 hover:text-[#12B76A] transition-colors flex items-center gap-2 group"
                  >
                    <ChevronRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Services */}
          <div className="lg:col-span-3">
            <h3 className="text-white font-semibold text-lg mb-6">Our Services</h3>
            <ul className="space-y-3">
              {[
                { to: "/services/periodic", label: "Periodic EV Service" },
                { to: "/services/motor-controller", label: "Motor & Controller" },
                { to: "/services/battery-bms", label: "Battery & BMS" },
                { to: "/services/roadside", label: "Roadside Assistance" },
                { to: "/services/fleet", label: "Fleet Programs" },
              ].map((link) => (
                <li key={link.to}>
                  <Link 
                    to={link.to} 
                    className="text-gray-400 hover:text-[#12B76A] transition-colors flex items-center gap-2 group"
                  >
                    <ChevronRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
            
            {/* Featured Articles */}
            <h3 className="text-white font-semibold text-lg mt-8 mb-4">Featured Articles</h3>
            <ul className="space-y-3">
              <li>
                <Link to="/blog/onsite-ev-repair-near-me-delhi-ncr" className="text-gray-400 hover:text-[#12B76A] transition-colors text-sm">
                  Onsite EV Repair Delhi NCR
                </Link>
              </li>
              <li>
                <Link to="/blog/ev-battery-health-check-diagnostics-costs" className="text-gray-400 hover:text-[#12B76A] transition-colors text-sm">
                  EV Battery Health Guide
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="lg:col-span-3">
            <h3 className="text-white font-semibold text-lg mb-6">Contact Us</h3>
            
            <div className="space-y-5">
              {/* Address */}
              <div className="flex gap-3">
                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-5 h-5 text-[#12B76A]" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Head Office</p>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    A 19 G/F FIEE Complex, Okhla Phase 2, Delhi 110020
                  </p>
                </div>
              </div>
              
              {/* Phone */}
              <div className="flex gap-3">
                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Phone className="w-5 h-5 text-[#12B76A]" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Helpline</p>
                  <a href="tel:+917696965096" className="text-gray-300 hover:text-[#12B76A] transition-colors block">
                    +91 7696 965 096
                  </a>
                  <a href="tel:+918076331607" className="text-gray-300 hover:text-[#12B76A] transition-colors block text-sm">
                    +91 8076 331 607
                  </a>
                </div>
              </div>
              
              {/* Email */}
              <div className="flex gap-3">
                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Mail className="w-5 h-5 text-[#12B76A]" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Email</p>
                  <a href={`mailto:${companyInfo.email}`} className="text-gray-300 hover:text-[#12B76A] transition-colors text-sm">
                    {companyInfo.email}
                  </a>
                </div>
              </div>
              
              {/* Hours */}
              <div className="flex gap-3">
                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Clock className="w-5 h-5 text-[#12B76A]" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Working Hours</p>
                  <p className="text-gray-300 text-sm">Open 365 days</p>
                  <p className="text-gray-400 text-sm">09:00 AM – 11:00 PM</p>
                </div>
              </div>
            </div>
            
            {/* WhatsApp CTA */}
            <a 
              href="https://wa.me/918076331607" 
              target="_blank" 
              rel="noopener noreferrer"
              className="mt-6 flex items-center gap-3 bg-[#12B76A] hover:bg-[#0F9F5F] transition-colors rounded-xl p-4"
            >
              <MessageCircle className="w-6 h-6" />
              <div>
                <p className="font-semibold text-sm">Chat on WhatsApp</p>
                <p className="text-xs text-white/80">Quick response guaranteed</p>
              </div>
            </a>
          </div>
        </div>
      </div>

      {/* Service Locations Section */}
      <div className="border-t border-gray-800">
        <div className="container mx-auto px-4 py-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-[#12B76A]/10 text-[#12B76A] px-4 py-2 rounded-full text-sm font-medium mb-4">
              <Zap className="w-4 h-4" />
              Pan-India Network
            </div>
            <h3 className="text-xl font-bold text-white">Service Locations</h3>
          </div>

          <div className="flex flex-wrap justify-center gap-3 max-w-5xl mx-auto">
            {operationalCities.map((location, index) => (
              <div
                key={index}
                className="flex items-center gap-2 bg-gray-800/50 hover:bg-gray-800 transition-colors rounded-full px-4 py-2"
              >
                <MapPin className="w-3 h-3 text-[#12B76A]" />
                <span className="text-gray-300 text-sm">
                  {location.city}
                  {location.area && <span className="text-gray-500"> • {location.area}</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800 bg-gray-950">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-gray-500 text-sm">
              © {new Date().getFullYear()} {companyInfo.name}. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <Link to="/privacy" className="text-gray-500 hover:text-[#12B76A] transition-colors text-sm">
                Privacy Policy
              </Link>
              <Link to="/terms" className="text-gray-500 hover:text-[#12B76A] transition-colors text-sm">
                Terms of Service
              </Link>
              <Link to="/faq" className="text-gray-500 hover:text-[#12B76A] transition-colors text-sm">
                FAQ
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

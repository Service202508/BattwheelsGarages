import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, Phone, Mail, MapPin, Linkedin, Twitter } from 'lucide-react';

const Footer = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* About */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="bg-gray-800 p-2 rounded">
                <Zap className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <span className="text-base font-bold text-white">Battwheels Garages</span>
                <p className="text-xs text-gray-400">EV Aftersales Infrastructure</p>
              </div>
            </div>
            <p className="text-sm mb-4 text-gray-400">
              India's first EV-only onsite roadside assistance and aftersales service company. No towing first — we diagnose and repair on the spot.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Company</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#about" className="hover:text-green-500 transition-colors">About Us</a>
              </li>
              <li>
                <a href="#services" className="hover:text-green-500 transition-colors">Services</a>
              </li>
              <li>
                <a href="#fleet" className="hover:text-green-500 transition-colors">Fleet Solutions</a>
              </li>
              <li>
                <a href="#why" className="hover:text-green-500 transition-colors">Why Battwheels</a>
              </li>
              <li>
                <a href="#contact" className="hover:text-green-500 transition-colors">Contact</a>
              </li>
            </ul>
          </div>

          {/* Solutions */}
          <div>
            <h3 className="text-white font-semibold mb-4">Solutions</h3>
            <ul className="space-y-2 text-sm">
              <li className="hover:text-green-500 transition-colors cursor-pointer">AMC Contracts</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Fleet Maintenance</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Onsite RSA</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Spare Parts Logistics</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Franchise Partnership</li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-white font-semibold mb-4">Contact</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start space-x-2">
                <MapPin className="w-4 h-4 mt-1 flex-shrink-0 text-green-500" />
                <span>Dwarka Sector 23, Delhi, India</span>
              </li>
              <li className="flex items-center space-x-2">
                <Phone className="w-4 h-4 flex-shrink-0 text-green-500" />
                <span>+91 9876543210</span>
              </li>
              <li className="flex items-center space-x-2">
                <Mail className="w-4 h-4 flex-shrink-0 text-green-500" />
                <span className="text-xs">partnerships@battwheelsgarages.in</span>
              </li>
            </ul>
            <div className="flex space-x-3 mt-4">
              <a href="#" className="bg-gray-800 p-2 rounded hover:bg-green-600 transition-colors">
                <Linkedin className="w-4 h-4" />
              </a>
              <a href="#" className="bg-gray-800 p-2 rounded hover:bg-green-600 transition-colors">
                <Twitter className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 text-center text-sm">
          <p className="text-gray-400">&copy; {new Date().getFullYear()} Battwheels Garages. All rights reserved.</p>
          <p className="text-gray-500 text-xs mt-2">Built for India's EV Revolution</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
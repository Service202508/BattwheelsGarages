import React from 'react';
import { Link } from 'react-router-dom';
import { Battery, Phone, Mail, MapPin, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';

const Footer = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* About */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="bg-green-500 p-2 rounded-lg">
                <Battery className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-white">Battwheels Garages</span>
            </div>
            <p className="text-sm mb-4">
              Your trusted partner for onsite EV repair & maintenance. Fast, reliable & expert service at your location.
            </p>
            <div className="flex space-x-3">
              <a href="#" className="bg-gray-800 p-2 rounded-full hover:bg-green-600 transition-colors">
                <Facebook className="w-4 h-4" />
              </a>
              <a href="#" className="bg-gray-800 p-2 rounded-full hover:bg-green-600 transition-colors">
                <Twitter className="w-4 h-4" />
              </a>
              <a href="#" className="bg-gray-800 p-2 rounded-full hover:bg-green-600 transition-colors">
                <Instagram className="w-4 h-4" />
              </a>
              <a href="#" className="bg-gray-800 p-2 rounded-full hover:bg-green-600 transition-colors">
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#" onClick={scrollToTop} className="hover:text-green-500 transition-colors">Home</a>
              </li>
              <li>
                <a href="#services" className="hover:text-green-500 transition-colors">Services</a>
              </li>
              <li>
                <a href="#about" className="hover:text-green-500 transition-colors">About Us</a>
              </li>
              <li>
                <a href="#contact" className="hover:text-green-500 transition-colors">Contact</a>
              </li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-white font-semibold mb-4">Our Services</h3>
            <ul className="space-y-2 text-sm">
              <li className="hover:text-green-500 transition-colors cursor-pointer">Battery Diagnostics</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Motor Repair</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Software Updates</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">Brake System Repair</li>
              <li className="hover:text-green-500 transition-colors cursor-pointer">EV Charger Repair</li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-white font-semibold mb-4">Contact Us</h3>
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
                <span>info@battwheelsgarages.in</span>
              </li>
            </ul>
            <div className="mt-4">
              <span className="inline-block bg-green-600 text-white text-xs px-3 py-1 rounded-full">
                24x7 Service Available
              </span>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
          <p>&copy; {new Date().getFullYear()} Battwheels Garages. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
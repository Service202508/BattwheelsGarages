import React from 'react';
import { Link } from 'react-router-dom';
import { Phone, Mail, MapPin, Clock, Facebook, Instagram, Linkedin } from 'lucide-react';
import { companyInfo } from '../../data/mockData';

const Footer = () => {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Company Info */}
          <div>
            <div className="mb-4">
              <img 
                src="/assets/battwheels-logo-white.svg" 
                alt="Battwheels Garages" 
                className="h-10 md:h-12 w-auto mb-3"
              />
            </div>
            <p className="text-sm mb-4 text-gray-400">
              {companyInfo.tagline}
            </p>
            <p className="text-sm text-gray-400">
              India's onsite EV after-sales & maintenance leader
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/" className="hover:text-green-500 transition-colors">Home</Link></li>
              <li><Link to="/about" className="hover:text-green-500 transition-colors">About Us</Link></li>
              <li><Link to="/services" className="hover:text-green-500 transition-colors">Services</Link></li>
              <li><Link to="/industries" className="hover:text-green-500 transition-colors">Industries</Link></li>
              <li><Link to="/battwheels-os" className="hover:text-green-500 transition-colors">Battwheels OS</Link></li>
              <li><Link to="/plans" className="hover:text-green-500 transition-colors">Subscription Plans</Link></li>
              <li><Link to="/blog" className="hover:text-green-500 transition-colors">Blog</Link></li>
              <li><Link to="/careers" className="hover:text-green-500 transition-colors">Careers</Link></li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-white font-semibold mb-4">Our Services</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/services/periodic" className="hover:text-green-500 transition-colors">Periodic EV Service</Link></li>
              <li><Link to="/services/motor-controller" className="hover:text-green-500 transition-colors">Motor & Controller</Link></li>
              <li><Link to="/services/battery-bms" className="hover:text-green-500 transition-colors">Battery & BMS</Link></li>
              <li><Link to="/services/roadside" className="hover:text-green-500 transition-colors">Roadside Assistance</Link></li>
              <li><Link to="/services/fleet" className="hover:text-green-500 transition-colors">Fleet Programs</Link></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-white font-semibold mb-4">Contact Us</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start space-x-2">
                <MapPin className="w-4 h-4 mt-1 flex-shrink-0 text-green-500" />
                <span>{companyInfo.address}</span>
              </li>
              <li className="flex items-center space-x-2">
                <Phone className="w-4 h-4 flex-shrink-0 text-green-500" />
                <a href={`tel:${companyInfo.phone}`} className="hover:text-green-500">{companyInfo.phone}</a>
              </li>
              <li className="flex items-center space-x-2">
                <Mail className="w-4 h-4 flex-shrink-0 text-green-500" />
                <a href={`mailto:${companyInfo.email}`} className="hover:text-green-500">{companyInfo.email}</a>
              </li>
              <li className="flex items-start space-x-2">
                <Clock className="w-4 h-4 mt-1 flex-shrink-0 text-green-500" />
                <span>{companyInfo.hours}</span>
              </li>
            </ul>
            <div className="flex space-x-3 mt-4">
              <a href={companyInfo.social.facebook} className="bg-gray-800 p-2 rounded hover:bg-green-600 transition-colors">
                <Facebook className="w-4 h-4" />
              </a>
              <a href={companyInfo.social.instagram} className="bg-gray-800 p-2 rounded hover:bg-green-600 transition-colors">
                <Instagram className="w-4 h-4" />
              </a>
              <a href={companyInfo.social.linkedin} className="bg-gray-800 p-2 rounded hover:bg-green-600 transition-colors">
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 text-center text-sm">
          <p className="text-gray-400">&copy; {new Date().getFullYear()} {companyInfo.name}. All rights reserved.</p>
          <div className="mt-2 space-x-4">
            <Link to="/privacy" className="hover:text-green-500 transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-green-500 transition-colors">Terms of Service</Link>
            <Link to="/faq" className="hover:text-green-500 transition-colors">FAQ</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
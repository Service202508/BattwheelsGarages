import React from 'react';
import { Link } from 'react-router-dom';
import { Phone, Mail, MapPin, Clock, Facebook, Instagram, Linkedin, MessageCircle } from 'lucide-react';
import { companyInfo } from '../../data/mockData';

const Footer = () => {
  // Operational cities data - easily maintainable
  const operationalCities = [
    { city: "Ulhasnagar", area: "", state: "Maharashtra" },
    { city: "Bengaluru", area: "Nelamangala / Yentaganahalli", state: "Karnataka" },
    { city: "Chennai", area: "Thiruverkadu / Poonamallee", state: "Tamil Nadu" },
    { city: "Pamarru", area: "Arandal Peta", state: "Andhra Pradesh" },
    { city: "New Delhi", area: "Dwarka Sector 28 (Bamnoli)", state: "Delhi" },
    { city: "New Delhi", area: "Okhla Phase 2 (Head Office)", state: "Delhi" },
    { city: "Noida", area: "Sector 68 (Garhi Chaukhandi)", state: "Uttar Pradesh" },
    { city: "Lucknow", area: "Ashiyana / Mansarovar Yojana", state: "Uttar Pradesh" },
    { city: "Gurugram", area: "Pace City I (Sector 37)", state: "Haryana" },
    { city: "Jaipur", area: "Vishwakarma Industrial Area", state: "Rajasthan" },
    { city: "Hyderabad", area: "Kompally / Petbasheerabad", state: "Telangana" },
  ];

  return (
    <footer className="bg-gradient-to-br from-[#005E4C] via-[#004D3F] to-[#003D32] text-white">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Company Info */}
          <div>
            <div className="mb-4">
              <img 
                src="/assets/battwheels-logo-main.png" 
                alt="Battwheels Garages" 
                className="h-10 md:h-12 w-auto mb-3 brightness-0 invert"
              />
            </div>
            <p className="text-sm mb-4 text-gray-300 leading-relaxed">
              {companyInfo.tagline}
            </p>
            <p className="text-sm text-gray-300">
              India's onsite EV after-sales & maintenance leader
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/" className="text-gray-300 hover:text-[#12B76A] transition-colors">Home</Link></li>
              <li><Link to="/about" className="text-gray-300 hover:text-[#12B76A] transition-colors">About Us</Link></li>
              <li><Link to="/services" className="text-gray-300 hover:text-[#12B76A] transition-colors">Services</Link></li>
              <li><Link to="/industries" className="text-gray-300 hover:text-[#12B76A] transition-colors">Industries</Link></li>
              <li><Link to="/battwheels-os" className="text-gray-300 hover:text-[#12B76A] transition-colors">Battwheels OS</Link></li>
              <li><Link to="/plans" className="text-gray-300 hover:text-[#12B76A] transition-colors">Subscription Plans</Link></li>
              <li><Link to="/blog" className="text-gray-300 hover:text-[#12B76A] transition-colors">Blog</Link></li>
              <li><Link to="/careers" className="text-gray-300 hover:text-[#12B76A] transition-colors">Careers</Link></li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-white font-semibold mb-4">Our Services</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/services/periodic" className="text-gray-300 hover:text-[#12B76A] transition-colors">Periodic EV Service</Link></li>
              <li><Link to="/services/motor-controller" className="text-gray-300 hover:text-[#12B76A] transition-colors">Motor & Controller</Link></li>
              <li><Link to="/services/battery-bms" className="text-gray-300 hover:text-[#12B76A] transition-colors">Battery & BMS</Link></li>
              <li><Link to="/services/roadside" className="text-gray-300 hover:text-[#12B76A] transition-colors">Roadside Assistance</Link></li>
              <li><Link to="/services/fleet" className="text-gray-300 hover:text-[#12B76A] transition-colors">Fleet Programs</Link></li>
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
            
            {/* WhatsApp CTA */}
            <div className="mt-6 p-4 bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
              <a 
                href="https://wa.me/918076331607" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center space-x-3 text-white"
                aria-label="Chat with us on WhatsApp - +91 80763 31607"
              >
                <MessageCircle className="w-5 h-5" />
                <div>
                  <div className="font-semibold text-sm">Chat with us on WhatsApp</div>
                  <div className="text-xs text-green-100">+91 80763 31607</div>
                </div>
              </a>
            </div>

            {/* Social Media Icons */}
            <div className="mt-6">
              <h4 className="text-white font-semibold mb-3 text-sm">Connect With Us</h4>
              <div className="flex space-x-3">
                <a 
                  href="https://wa.me/918076331607" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="bg-gray-800 p-2.5 rounded-lg hover:bg-green-600 hover:scale-110 transition-all duration-300"
                  aria-label="WhatsApp - Chat with Battwheels Garages"
                >
                  <MessageCircle className="w-5 h-5" />
                </a>
                <a 
                  href="https://www.facebook.com/battwheelsgarages" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="bg-gray-800 p-2.5 rounded-lg hover:bg-blue-600 hover:scale-110 transition-all duration-300"
                  aria-label="Facebook - Battwheels Garages"
                >
                  <Facebook className="w-5 h-5" />
                </a>
                <a 
                  href="https://www.instagram.com/battwheelsgarages" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="bg-gray-800 p-2.5 rounded-lg hover:bg-pink-600 hover:scale-110 transition-all duration-300"
                  aria-label="Instagram - Battwheels Garages"
                >
                  <Instagram className="w-5 h-5" />
                </a>
                <a 
                  href="https://www.linkedin.com/company/battwheels-garages" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="bg-gray-800 p-2.5 rounded-lg hover:bg-blue-700 hover:scale-110 transition-all duration-300"
                  aria-label="LinkedIn - Battwheels Garages"
                >
                  <Linkedin className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Operational Cities Section */}
        <div className="border-t border-gray-800 pt-8 mb-8">
          <div className="text-center mb-6">
            <h3 className="text-white text-xl font-bold mb-2">Pan-India Service Locations</h3>
            <p className="text-gray-400 text-sm">Serving EV fleets and owners across these operational cities</p>
          </div>

          <div 
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            role="list"
            aria-label="Operational cities across India"
          >
            {operationalCities.map((location, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 p-3 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
                role="listitem"
              >
                <MapPin className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium text-sm truncate">
                    {location.city}
                    {location.area && <span className="text-gray-400 font-normal"> – {location.area}</span>}
                  </p>
                  <p className="text-gray-400 text-xs">{location.state}</p>
                </div>
              </div>
            ))}
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
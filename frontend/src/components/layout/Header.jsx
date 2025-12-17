import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Menu, X, Phone } from 'lucide-react';
import { companyInfo } from '../../data/mockData';

const Header = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Battwheels OS™', path: '/battwheels-os' },
    {
      name: 'Services',
      path: '/services',
      dropdown: [
        { name: 'All Services', path: '/services' },
        { name: 'Periodic EV Service', path: '/services/periodic' },
        { name: 'Motor & Controller', path: '/services/motor-controller' },
        { name: 'Battery & BMS', path: '/services/battery-bms' },
        { name: 'Chargers & Connectors', path: '/services/charger' },
        { name: 'Brakes & Tyres', path: '/services/brakes-tyres' },
        { name: 'Body & Paint', path: '/services/body-paint' },
        { name: 'Roadside Assistance', path: '/services/roadside' },
        { name: 'Fleet Programs', path: '/services/fleet' }
      ]
    },
    { name: 'Industries', path: '/industries' },
    { name: 'Subscriptions', path: '/plans' },
    { name: 'Blog', path: '/blog' },
    { name: 'Careers', path: '/careers' },
    { name: 'Contact', path: '/contact' }
  ];

  return (
    <header className="bg-white/95 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <nav className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center">
            <img 
              src="/assets/battwheels-logo-main.png" 
              alt="Battwheels Garages" 
              className="h-12 md:h-14 lg:h-16 w-auto transition-all"
            />
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-6">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className="text-gray-700 hover:text-[#0B8A44] transition-colors text-sm font-medium"
              >
                {link.name}
              </Link>
            ))}
          </div>

          {/* Desktop CTAs */}
          <div className="hidden lg:flex items-center space-x-3">
            <Button
              variant="outline"
              className="border-[#0B8A44] text-[#0B8A44] hover:bg-green-50 hover:border-[#12B76A] transition-all duration-300"
              onClick={() => navigate('/book-service')}
            >
              Book Service
            </Button>
            <Button
              className="bg-gradient-to-r from-[#0B8A44] to-[#12B76A] hover:from-[#0A7A3D] hover:to-[#10A35F] text-white shadow-md hover:shadow-lg transition-all duration-300"
              onClick={() => navigate('/fleet-oem')}
            >
              <Phone className="w-4 h-4 mr-2" />
              Fleet Expert
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="lg:hidden text-gray-700 hover:text-[#0B8A44] transition-colors"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="lg:hidden mt-4 pb-4 border-t border-gray-100 pt-4 space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setIsOpen(false)}
                className="block py-2 text-gray-700 hover:text-[#0B8A44] transition-colors font-medium"
              >
                {link.name}
              </Link>
            ))}
            <div className="flex flex-col gap-2 mt-4">
              <Button
                className="w-full bg-gradient-to-r from-[#0B8A44] to-[#12B76A] hover:from-[#0A7A3D] hover:to-[#10A35F] text-white"
                onClick={() => {
                  navigate('/book-service');
                  setIsOpen(false);
                }}
              >
                Book Service
              </Button>
              <Button
                variant="outline"
                className="w-full border-[#0B8A44] text-[#0B8A44] hover:bg-green-50"
                onClick={() => {
                  navigate('/fleet-oem');
                  setIsOpen(false);
                }}
              >
                Talk to Fleet Expert
              </Button>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
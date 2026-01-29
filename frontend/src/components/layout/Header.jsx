import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Menu, X, Phone, ChevronDown } from 'lucide-react';

const Header = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const navigate = useNavigate();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Services', path: '/services' },
    { name: 'Subscriptions', path: '/plans' },
    { name: 'Industries', path: '/industries' },
    { name: 'Blog', path: '/blog' },
    { name: 'Contact', path: '/contact' }
  ];

  return (
    <>
      {/* Main Header */}
      <header className="bg-white/95 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50 shadow-sm">
        <nav className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center">
              <img 
                src="/assets/battwheels-logo-new-transparent.png" 
                alt="Battwheels Garages" 
                className="h-12 md:h-14 w-auto"
              />
            </Link>

            {/* Desktop Navigation - Centered */}
            <div className="hidden lg:flex items-center space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  className="text-gray-700 hover:text-green-600 transition-colors text-sm font-medium relative group"
                >
                  {link.name}
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-green-600 group-hover:w-full transition-all duration-300" />
                </Link>
              ))}
            </div>

            {/* Desktop CTAs */}
            <div className="hidden lg:flex items-center space-x-3">
              <Button
                variant="outline"
                size="sm"
                className="border-green-600 text-green-600 hover:bg-green-50 font-semibold"
                onClick={() => navigate('/book-service')}
              >
                Book Service
              </Button>
              <Button
                size="sm"
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold shadow-md"
                onClick={() => navigate('/fleet-oem')}
              >
                <Phone className="w-4 h-4 mr-1.5" />
                Fleet Expert
              </Button>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="lg:hidden text-gray-700 hover:text-green-600 transition-colors p-2"
              onClick={() => setIsOpen(!isOpen)}
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {isOpen && (
            <div className="lg:hidden py-4 border-t border-gray-100 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={() => setIsOpen(false)}
                  className="block py-2.5 px-3 text-gray-700 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors font-medium"
                >
                  {link.name}
                </Link>
              ))}
              <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-gray-100">
                <Button
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold"
                  onClick={() => {
                    navigate('/book-service');
                    setIsOpen(false);
                  }}
                >
                  Book Service
                </Button>
                <Button
                  variant="outline"
                  className="w-full border-green-600 text-green-600 font-semibold"
                  onClick={() => {
                    navigate('/fleet-oem');
                    setIsOpen(false);
                  }}
                >
                  <Phone className="w-4 h-4 mr-2" />
                  Talk to Fleet Expert
                </Button>
              </div>
            </div>
          )}
        </nav>
      </header>

      {/* Sticky CTA Bar - Shows on scroll */}
      <div className="fixed bottom-0 left-0 right-0 z-40 lg:hidden bg-white border-t border-gray-200 shadow-lg px-4 py-2 flex gap-2">
        <Button
          className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-semibold"
          onClick={() => navigate('/book-service')}
        >
          Book Service
        </Button>
        <Button
          variant="outline"
          className="flex-1 border-green-600 text-green-600 text-sm font-semibold"
          onClick={() => navigate('/fleet-oem')}
        >
          <Phone className="w-4 h-4 mr-1" />
          Fleet Expert
        </Button>
      </div>
    </>
  );
};

export default Header;

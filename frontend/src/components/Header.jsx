import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Menu, X, Phone, Battery } from 'lucide-react';

const Header = () => {
  const [isOpen, setIsOpen] = useState(false);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Services', path: '#services' },
    { name: 'About', path: '#about' },
    { name: 'Contact', path: '#contact' }
  ];

  const scrollToSection = (e, path) => {
    if (path.startsWith('#')) {
      e.preventDefault();
      const element = document.querySelector(path);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
      setIsOpen(false);
    }
  };

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <nav className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="bg-green-500 p-2 rounded-lg">
              <Battery className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">Battwheels Garages</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.path}
                onClick={(e) => scrollToSection(e, link.path)}
                className="text-gray-700 hover:text-green-600 transition-colors font-medium"
              >
                {link.name}
              </a>
            ))}
            <Button className="bg-green-600 hover:bg-green-700 text-white">
              <Phone className="w-4 h-4 mr-2" />
              Call Now
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-gray-700"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden mt-4 pb-4 border-t pt-4">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.path}
                onClick={(e) => scrollToSection(e, link.path)}
                className="block py-2 text-gray-700 hover:text-green-600 transition-colors font-medium"
              >
                {link.name}
              </a>
            ))}
            <Button className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white">
              <Phone className="w-4 h-4 mr-2" />
              Call Now
            </Button>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
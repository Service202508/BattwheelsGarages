import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Menu, X, Zap } from 'lucide-react';

const Header = () => {
  const [isOpen, setIsOpen] = useState(false);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '#about' },
    { name: 'Services', path: '#services' },
    { name: 'Fleet Solutions', path: '#fleet' },
    { name: 'Why Battwheels', path: '#why' },
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
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <nav className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="bg-gray-900 p-2 rounded">
              <Zap className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <span className="text-lg font-bold text-gray-900">Battwheels Garages</span>
              <p className="text-xs text-gray-600">India's EV Aftersales Infrastructure</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-6">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.path}
                onClick={(e) => scrollToSection(e, link.path)}
                className="text-gray-700 hover:text-green-600 transition-colors text-sm font-medium"
              >
                {link.name}
              </a>
            ))}
            <Button className="bg-green-600 hover:bg-green-700 text-white">
              Request Demo
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="lg:hidden text-gray-700"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="lg:hidden mt-4 pb-4 border-t pt-4">
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
              Request Demo
            </Button>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
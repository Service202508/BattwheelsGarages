import React from 'react';
import { Button } from './ui/button';
import { ArrowRight, Zap, Clock, MapPin } from 'lucide-react';

const HeroSection = () => {
  const scrollToContact = () => {
    const element = document.querySelector('#contact');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative bg-gradient-to-br from-green-50 via-white to-green-50 overflow-hidden">
      <div className="container mx-auto px-4 py-20 md:py-28">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-6 animate-fade-in">
            <div className="inline-block">
              <span className="bg-green-100 text-green-700 text-sm font-semibold px-4 py-2 rounded-full">
                🌱 100% Eco-Friendly EV Services
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
              EV Maintenance Services
              <span className="block text-green-600 mt-2">
                Keeping Your EV Clean, Green & Smooth
              </span>
            </h1>
            <p className="text-lg text-gray-600 leading-relaxed">
              Your 100% Onsite EV Issues Resolution Partner. Expert electric vehicle repair and maintenance services available 24x7 at your location.
            </p>

            {/* Features */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
              <div className="flex items-center space-x-2">
                <div className="bg-green-100 p-2 rounded-lg">
                  <Zap className="w-5 h-5 text-green-600" />
                </div>
                <span className="text-sm font-medium text-gray-700">Fast Service</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="bg-green-100 p-2 rounded-lg">
                  <Clock className="w-5 h-5 text-green-600" />
                </div>
                <span className="text-sm font-medium text-gray-700">24x7 Available</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="bg-green-100 p-2 rounded-lg">
                  <MapPin className="w-5 h-5 text-green-600" />
                </div>
                <span className="text-sm font-medium text-gray-700">Onsite Service</span>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button 
                size="lg" 
                className="bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl transition-all"
                onClick={scrollToContact}
              >
                Book Service Now
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-green-600 text-green-600 hover:bg-green-50"
              >
                Call: +91 9876543210
              </Button>
            </div>
          </div>

          {/* Right Image/Illustration */}
          <div className="relative">
            <div className="relative z-10">
              <img 
                src="https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&h=600&fit=crop" 
                alt="Electric Vehicle Service" 
                className="rounded-2xl shadow-2xl"
              />
              {/* Floating Card */}
              <div className="absolute -bottom-6 -left-6 bg-white p-6 rounded-xl shadow-xl">
                <div className="flex items-center space-x-4">
                  <div className="bg-green-100 p-3 rounded-full">
                    <Zap className="w-8 h-8 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">5000+</p>
                    <p className="text-sm text-gray-600">Happy Customers</p>
                  </div>
                </div>
              </div>
            </div>
            {/* Background Decoration */}
            <div className="absolute top-10 right-10 w-72 h-72 bg-green-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
            <div className="absolute -bottom-10 left-10 w-72 h-72 bg-green-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" style={{ animationDelay: '1s' }}></div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
import React from 'react';
import { Button } from './ui/button';
import { ArrowRight, TrendingUp, Wrench, Clock } from 'lucide-react';

const HeroSection = () => {
  const scrollToContact = () => {
    const element = document.querySelector('#contact');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative bg-gradient-to-br from-gray-50 to-white py-20 md:py-28">
      <div className="container mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 bg-green-50 border border-green-200 px-4 py-2 rounded-full">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm font-semibold text-green-700">₹1 Crore Revenue in Year 1</span>
            </div>

            {/* Main Heading */}
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-4">
                India's First EV-Only Onsite Aftersales Infrastructure
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                EVs don't need towing first. They need diagnosis and repair on the spot.
              </p>
            </div>

            {/* Problem - Solution */}
            <div className="bg-gray-900 text-white p-6 rounded-lg border-l-4 border-green-500">
              <p className="text-sm uppercase tracking-wider text-green-400 font-semibold mb-2">The Actual Roadside Assistance By Battwheels</p>
              <p className="text-lg font-semibold">No Towing First → Diagnose → Repair Onsite → Resume Operations</p>
              <p className="text-gray-300 text-sm mt-2">85% issues resolved on field. Maximum uptime for your fleet.</p>
            </div>

            {/* Key Features */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-green-600">85%</div>
                <div className="text-xs text-gray-600 mt-1">Onsite Resolution</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-green-600">2hr</div>
                <div className="text-xs text-gray-600 mt-1">Avg TAT</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-green-600">145+</div>
                <div className="text-xs text-gray-600 mt-1">EV Models</div>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg" 
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={scrollToContact}
              >
                Partner with Us
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-gray-300 text-gray-700 hover:bg-gray-50"
                onClick={() => {
                  const element = document.querySelector('#fleet');
                  if (element) element.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Fleet Solutions
              </Button>
            </div>
          </div>

          {/* Right Content - Image */}
          <div className="relative">
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1615906655593-ad0386982a0f?w=800&h=600&fit=crop" 
                alt="EV Technician at Work" 
                className="rounded-lg shadow-2xl"
              />
              {/* Overlay Stats */}
              <div className="absolute bottom-6 left-6 right-6 bg-white/95 backdrop-blur p-4 rounded-lg shadow-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="bg-green-100 p-2 rounded">
                      <Wrench className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-900">Field-First Operations</p>
                      <p className="text-xs text-gray-600">Operator-led, not MBA-led</p>
                    </div>
                  </div>
                  <div className="bg-green-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                    Live
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
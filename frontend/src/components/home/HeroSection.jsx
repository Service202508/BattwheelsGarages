import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { ArrowRight, Phone } from 'lucide-react';

const HeroSection = () => {
  const navigate = useNavigate();

  return (
    <section className="relative bg-gradient-to-br from-gray-50 via-white to-green-50 py-20 md:py-28 overflow-hidden">
      <div className="container mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8">
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
                India's Onsite EV After-Sales & Maintenance Leader
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                We keep your 2W, 3W, 4W and commercial EVs running with no-towing-first onsite diagnostics, expert repairs, and fleet-grade uptime.
              </p>
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg" 
                className="bg-green-600 hover:bg-green-700 text-white shadow-lg"
                onClick={() => navigate('/book-service')}
              >
                Book EV Service Now
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-green-600 text-green-600 hover:bg-green-50"
                onClick={() => navigate('/fleet-oem')}
              >
                <Phone className="mr-2 w-5 h-5" />
                Talk to Fleet & OEM Team
              </Button>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap items-center gap-6 pt-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600 font-medium">Open 365 Days</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600 font-medium">24/7 Emergency Support</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600 font-medium">Pan-India Coverage</span>
              </div>
            </div>
          </div>

          {/* Right Image */}
          <div className="relative">
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&h=600&fit=crop" 
                alt="EV Service" 
                className="rounded-2xl shadow-2xl"
              />
              <div className="absolute -bottom-6 -left-6 bg-white p-6 rounded-xl shadow-xl">
                <div className="flex items-center space-x-4">
                  <div className="bg-green-100 p-3 rounded-full">
                    <ArrowRight className="w-8 h-8 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">10,000+</p>
                    <p className="text-sm text-gray-600">EVs Serviced</p>
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
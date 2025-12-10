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
            {/* Problem Statement Badge */}
            <div className="inline-block">
              <div className="bg-red-50 border border-red-200 px-4 py-2 rounded-lg text-sm">
                <span className="text-red-700 font-semibold">⚠️ Traditional RSA is broken for EVs</span>
              </div>
            </div>

            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
                EVs Don't Need Towing First. They Need Diagnosis & Repair Onsite.
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed mb-6">
                India's first <span className="font-semibold text-gray-900">no-towing-first</span> EV service model. We diagnose and fix your 2W, 3W, 4W & commercial EVs where they stop—maximizing uptime, minimizing costs.
              </p>

              {/* Key Differentiator - Visual Process Flow */}
              <div className="bg-gradient-to-r from-green-600 to-green-500 text-white p-8 rounded-2xl">
                <p className="text-sm font-semibold text-green-100 mb-6 text-center">The Battwheels Difference</p>
                
                <div className="grid grid-cols-4 gap-4 mb-6">
                  {/* Step 1: No Towing */}
                  <div className="text-center">
                    <div className="bg-white/20 backdrop-blur rounded-xl p-4 mb-3 h-24 flex items-center justify-center">
                      <div className="text-5xl">🚫</div>
                    </div>
                    <p className="text-xs font-semibold">No Towing First</p>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center justify-center">
                    <div className="text-3xl text-white/80">→</div>
                  </div>

                  {/* Step 2: Diagnose */}
                  <div className="text-center">
                    <div className="bg-white/20 backdrop-blur rounded-xl p-4 mb-3 h-24 flex items-center justify-center">
                      <div className="text-5xl">🔍</div>
                    </div>
                    <p className="text-xs font-semibold">Diagnose Onsite</p>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center justify-center">
                    <div className="text-3xl text-white/80">→</div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 mb-4">
                  {/* Step 3: Repair */}
                  <div className="text-center">
                    <div className="bg-white/20 backdrop-blur rounded-xl p-4 mb-3 h-24 flex items-center justify-center">
                      <div className="text-5xl">🔧</div>
                    </div>
                    <p className="text-xs font-semibold">Repair On-Spot</p>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center justify-center">
                    <div className="text-3xl text-white/80">→</div>
                  </div>

                  {/* Step 4: Resume */}
                  <div className="text-center">
                    <div className="bg-white/20 backdrop-blur rounded-xl p-4 mb-3 h-24 flex items-center justify-center">
                      <div className="text-5xl">✅</div>
                    </div>
                    <p className="text-xs font-semibold">Resume Operations</p>
                  </div>

                  {/* Empty space for alignment */}
                  <div></div>
                </div>

                <div className="text-center pt-4 border-t border-white/20">
                  <p className="text-lg font-bold">80-90% issues resolved on field</p>
                  <p className="text-sm text-green-100 mt-1">Maximum uptime for your fleet</p>
                </div>
              </div>
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
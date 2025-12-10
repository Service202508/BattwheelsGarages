import React from 'react';
import { X, Check, TrendingDown, TrendingUp } from 'lucide-react';

const RSAExplainedSection = () => {
  return (
    <section className="relative py-20 bg-gradient-to-b from-green-900 via-green-800 to-green-900 text-white overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 left-10 w-72 h-72 bg-green-400 rounded-full filter blur-3xl" />
        <div className="absolute bottom-20 right-10 w-72 h-72 bg-emerald-400 rounded-full filter blur-3xl" />
      </div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-white">
            Why Traditional RSA is Broken for EVs
          </h2>
          <p className="text-green-100 max-w-3xl mx-auto text-lg">
            Towing-first models waste time, increase costs, and kill vehicle uptime—especially for high-utilization EV fleets running 10-14 hours daily
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Traditional RSA - Problem */}
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/20 border-2 border-red-700/50 rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-red-600 p-3 rounded-lg">
                <X className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-red-400">Traditional RSA</h3>
                <p className="text-red-300 text-sm">Towing-First Model</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <TrendingDown className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Hours of Downtime</p>
                  <p className="text-gray-400 text-sm">Towing adds 3-6 hours before diagnosis even begins</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingDown className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Higher Costs</p>
                  <p className="text-gray-400 text-sm">Towing charges + workshop delays = inflated bills</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingDown className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Limited EV Knowledge</p>
                  <p className="text-gray-400 text-sm">ICE-focused mechanics with minimal EV expertise</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingDown className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">No Fleet Understanding</p>
                  <p className="text-gray-400 text-sm">Generic service model ignores fleet uptime economics</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingDown className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Days of Wait Time</p>
                  <p className="text-gray-400 text-sm">Long queue times at workshops mean lost revenue</p>
                </div>
              </div>
            </div>
          </div>

          {/* Battwheels Model - Solution */}
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border-2 border-green-600 rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-green-600 p-3 rounded-lg">
                <Check className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-green-400">Battwheels Model</h3>
                <p className="text-green-300 text-sm">No-Towing-First Approach</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <TrendingUp className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Onsite Resolution</p>
                  <p className="text-gray-300 text-sm">80-90% issues fixed on-spot. Vehicle back on road in &lt;2hrs</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingUp className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Lower Total Cost</p>
                  <p className="text-gray-300 text-sm">No towing charges + faster resolution = predictable costs</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingUp className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">EV-Only Specialists</p>
                  <p className="text-gray-300 text-sm">Trained on motors, BMS, controllers & EV electronics</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingUp className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Fleet-First DNA</p>
                  <p className="text-gray-300 text-sm">Built for fleets running 10-14hrs daily. Uptime is priority #1</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <TrendingUp className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-white font-semibold mb-1">Same-Day Resolution</p>
                  <p className="text-gray-300 text-sm">Sub-2 hour response, most repairs completed same day</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Impact Statement */}
        <div className="text-center mt-12 max-w-4xl mx-auto">
          <div className="bg-green-600/20 border border-green-600 p-6 rounded-xl">
            <p className="text-green-400 text-lg font-bold mb-2">
              Time is Money in Fleet Operations
            </p>
            <p className="text-gray-300">
              Every hour of downtime costs fleet operators revenue, customer trust, and competitive advantage. 
              Battwheels eliminates the &quot;towing tax&quot; and gets your vehicles back on the road faster.
            </p>
          </div>
        </div>
      </div>
      
      {/* Bottom wave transition to white background */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg className="w-full h-16 md:h-24" viewBox="0 0 1440 100" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
          <path d="M0,50 C360,80 720,20 1080,50 C1260,65 1350,35 1440,50 L1440,100 L0,100 Z" fill="white" />
        </svg>
      </div>
    </section>
  );
};

export default RSAExplainedSection;

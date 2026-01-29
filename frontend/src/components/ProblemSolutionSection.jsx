import React from 'react';
import { X, Check } from 'lucide-react';

const ProblemSolutionSection = () => {
  return (
    <section className="py-16 bg-gray-900 text-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Traditional RSA is Broken for EVs
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Towing-first models waste time, inflate costs, and kill vehicle uptime - especially for high-utilization fleets
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Traditional Model */}
          <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-red-600 p-2 rounded">
                <X className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-xl font-bold text-red-400">Traditional RSA</h3>
            </div>
            <ul className="space-y-3">
              <li className="flex items-start space-x-2">
                <X className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">Towing-first approach adds hours of downtime</span>
              </li>
              <li className="flex items-start space-x-2">
                <X className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">ICE-focused mechanics with limited EV knowledge</span>
              </li>
              <li className="flex items-start space-x-2">
                <X className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">No understanding of fleet uptime economics</span>
              </li>
              <li className="flex items-start space-x-2">
                <X className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">Generic parts network, no EV specialization</span>
              </li>
              <li className="flex items-start space-x-2">
                <X className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">Days of wait time for resolution</span>
              </li>
            </ul>
          </div>

          {/* Battwheels Model */}
          <div className="bg-green-900/20 border border-green-800/30 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-green-600 p-2 rounded">
                <Check className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-xl font-bold text-green-400">The Actual Roadside Assistance By Battwheels</h3>
            </div>
            <ul className="space-y-3">
              <li className="flex items-start space-x-2">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">Diagnose and repair onsite, 85% issues resolved on field</span>
              </li>
              <li className="flex items-start space-x-2">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">EV-only trained technicians and electricians</span>
              </li>
              <li className="flex items-start space-x-2">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">Fleet-first DNA, built for 10–14 hr daily operations</span>
              </li>
              <li className="flex items-start space-x-2">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">EV-specific dark stores and parts logistics</span>
              </li>
              <li className="flex items-start space-x-2">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm">Sub-2 hour response, same-day resolution</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-12">
          <p className="text-green-400 text-lg font-semibold mb-4">
            Time is Money in Fleet Operations
          </p>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Every hour of downtime costs fleet operators revenue, customer trust, and competitive advantage. 
            Battwheels eliminates the towing tax and gets your vehicles back on the road faster.
          </p>
        </div>
      </div>
    </section>
  );
};

export default ProblemSolutionSection;
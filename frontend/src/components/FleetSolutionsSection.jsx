import React from 'react';
import { fleetSolutions } from '../mockData';
import { FileText, ClipboardCheck, Package, Clipboard, Check } from 'lucide-react';

const iconMap = {
  FileText,
  ClipboardCheck,
  Package,
  Clipboard
};

const FleetSolutionsSection = () => {
  return (
    <section id="fleet" className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-block bg-green-100 text-green-700 px-4 py-2 rounded-full text-sm font-semibold mb-4">
            B2B Fleet Solutions
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Built for Fleet Operations
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Comprehensive service programs designed for high-utilization EV fleets running 10-14 hours daily. 
            Maximum uptime, predictable costs, guaranteed TAT.
          </p>
        </div>

        {/* Solutions Grid */}
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto mb-12">
          {fleetSolutions.map((solution) => {
            const Icon = iconMap[solution.icon];
            return (
              <div key={solution.id} className="bg-gray-50 border border-gray-200 rounded-lg p-8 hover:shadow-lg transition-shadow">
                <div className="flex items-start space-x-4 mb-4">
                  <div className="bg-green-600 p-3 rounded-lg flex-shrink-0">
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{solution.title}</h3>
                    <p className="text-gray-600 text-sm">{solution.description}</p>
                  </div>
                </div>
                <ul className="space-y-2 mt-4">
                  {solution.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start space-x-2 text-sm">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* CTA Box */}
        <div className="bg-gradient-to-r from-green-600 to-green-500 text-white p-8 md:p-12 rounded-lg text-center max-w-4xl mx-auto">
          <h3 className="text-2xl md:text-3xl font-bold mb-4">
            Scale Your EV Fleet with Confidence
          </h3>
          <p className="text-green-50 mb-6 max-w-2xl mx-auto">
            Partner with India's only EV-focused aftersales infrastructure. AMC/SLA contracts with guaranteed uptime, 
            dedicated service managers, and monthly performance reports.
          </p>
          <button 
            className="bg-white text-green-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            onClick={() => {
              const element = document.querySelector('#contact');
              if (element) element.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Request Fleet Partnership
          </button>
        </div>
      </div>
    </section>
  );
};

export default FleetSolutionsSection;
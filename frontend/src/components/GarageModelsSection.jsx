import React from 'react';
import { garageModels } from '../mockData';
import { Building2, Handshake, Network, Check } from 'lucide-react';

const iconMap = {
  Building2,
  Handshake,
  Network
};

const GarageModelsSection = () => {
  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Scalable Garage Models
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Pan-India expansion through three proven models: COCO, FOCO, and FOFO. 
            Built for rapid scaling while maintaining service standards.
          </p>
        </div>

        {/* Models Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {garageModels.map((model) => {
            const Icon = iconMap[model.icon];
            return (
              <div key={model.id} className="bg-gray-50 border-2 border-gray-200 rounded-lg p-8 hover:border-green-500 transition-colors">
                <div className="bg-gray-900 w-16 h-16 rounded-lg flex items-center justify-center mb-6">
                  <Icon className="w-8 h-8 text-green-500" />
                </div>
                <div className="mb-4">
                  <h3 className="text-2xl font-bold text-gray-900 mb-1">{model.model}</h3>
                  <p className="text-sm text-gray-600 font-medium">{model.fullForm}</p>
                </div>
                <p className="text-gray-700 mb-6 text-sm">{model.description}</p>
                <ul className="space-y-2">
                  {model.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-start space-x-2 text-sm">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-12">
          <p className="text-gray-600 mb-4">
            Interested in franchise partnership or expanding our network to your city?
          </p>
          <button 
            className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
            onClick={() => {
              const element = document.querySelector('#contact');
              if (element) element.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Explore Partnership Opportunities
          </button>
        </div>
      </div>
    </section>
  );
};

export default GarageModelsSection;
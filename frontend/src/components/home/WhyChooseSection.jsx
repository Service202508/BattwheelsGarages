import React from 'react';
import { whyChooseUs } from '../../data/mockData';
import { MapPin, Zap, Car, Monitor } from 'lucide-react';

const iconMap = {
  MapPin,
  Zap,
  Car,
  Monitor
};

const WhyChooseSection = () => {
  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why EV Owners & Fleets Choose Battwheels
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Specialized EV expertise with onsite-first service model designed for maximum uptime
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {whyChooseUs.map((feature) => {
            const Icon = iconMap[feature.icon];
            return (
              <div key={feature.id} className="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-shadow">
                <div className="bg-green-100 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                  <Icon className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default WhyChooseSection;
import React from 'react';
import { partners } from '../mockData';

const PartnersSection = () => {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
            Working with India's Leading EV Ecosystem
          </h2>
          <p className="text-gray-600">
            Fleet operators, OEMs, battery swapping platforms, and mobility companies
          </p>
        </div>

        {/* Partners Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 max-w-6xl mx-auto">
          {partners.map((partner) => (
            <div 
              key={partner.id} 
              className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center hover:shadow-md hover:border-green-500 transition-all group"
            >
              <p className="font-semibold text-gray-900 text-sm mb-1 group-hover:text-green-600 transition-colors">
                {partner.name}
              </p>
              <p className="text-xs text-gray-500">{partner.category}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PartnersSection;
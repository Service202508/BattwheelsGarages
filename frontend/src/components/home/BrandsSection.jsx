import React from 'react';
import { evBrands } from '../../data/mockData';

const BrandsSection = () => {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
            We Serve These EV Brands
          </h2>
          <p className="text-gray-600">
            Expert service for all major electric vehicle brands across 2W, 3W, 4W segments
          </p>
        </div>

        {/* Brands Grid */}
        <div className="grid grid-cols-3 md:grid-cols-5 gap-6">
          {evBrands.map((brand, index) => (
            <div 
              key={index} 
              className="bg-gray-50 border border-gray-200 p-4 rounded-lg flex items-center justify-center hover:border-green-500 hover:shadow-md transition-all group"
            >
              <span className="text-sm font-semibold text-gray-700 group-hover:text-green-600 transition-colors text-center">
                {brand}
              </span>
            </div>
          ))}
        </div>

        <div className="text-center mt-8 text-sm text-gray-600">
          <p>And many more... Contact us for your specific EV brand</p>
        </div>
      </div>
    </section>
  );
};

export default BrandsSection;
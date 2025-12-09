import React from 'react';
import { brands } from '../mockData';

const BrandsSection = () => {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            We Serve These EV Brands
          </h2>
          <p className="text-lg text-gray-600">
            Expert service for all major electric vehicle brands
          </p>
        </div>

        {/* Brands Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {brands.map((brand) => (
            <div 
              key={brand.id} 
              className="bg-gray-50 p-6 rounded-lg flex items-center justify-center hover:bg-green-50 hover:shadow-md transition-all cursor-pointer group"
            >
              <img 
                src={brand.logo} 
                alt={brand.name} 
                className="max-w-full h-12 object-contain grayscale group-hover:grayscale-0 transition-all"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BrandsSection;
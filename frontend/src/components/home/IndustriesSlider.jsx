import React from 'react';
import { industries } from '../../data/mockData';
import { Building, Truck, BatteryCharging, Package, User, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const iconMap = {
  Building,
  Truck,
  BatteryCharging,
  Package,
  User
};

const IndustriesSlider = () => {
  const navigate = useNavigate();

  return (
    <section className="py-20 bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Who We Serve
          </h2>
          <p className="text-gray-300 max-w-3xl mx-auto">
            From individual EV owners to large fleet operators and OEMs - we support the entire EV ecosystem
          </p>
        </div>

        {/* Industries Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {industries.map((industry) => {
            const Icon = iconMap[industry.icon];
            return (
              <div 
                key={industry.id} 
                className="bg-gray-800 border border-gray-700 p-8 rounded-xl hover:border-green-500 transition-all cursor-pointer group"
              >
                <div className="bg-green-600 w-16 h-16 rounded-xl flex items-center justify-center mb-6 group-hover:bg-green-500 transition-colors">
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3">{industry.title}</h3>
                <p className="text-gray-400 leading-relaxed">{industry.description}</p>
              </div>
            );
          })}
        </div>

        {/* CTA */}
        <div className="text-center">
          <button 
            onClick={() => navigate('/industries')}
            className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-semibold inline-flex items-center transition-colors"
          >
            See How We Support You
            <ArrowRight className="w-5 h-5 ml-2" />
          </button>
        </div>
      </div>
    </section>
  );
};

export default IndustriesSlider;
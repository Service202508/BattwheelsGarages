import React from 'react';
import { features } from '../mockData';
import { Users, Award, CheckCircle, Shield, Search, Heart } from 'lucide-react';

const iconMap = {
  Users,
  Award,
  CheckCircle,
  Shield,
  Search,
  Heart
};

const FeaturesSection = () => {
  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why Choose Us
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            When it comes to EV maintenance services, trust an expert service provider with years of expertise and knowledge
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = iconMap[feature.icon];
            return (
              <div 
                key={feature.id} 
                className="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-shadow group"
              >
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mb-4 group-hover:bg-green-600 transition-colors">
                  <Icon className="w-8 h-8 text-green-600 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
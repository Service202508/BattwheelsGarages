import React from 'react';
import { useNavigate } from 'react-router-dom';
import { serviceCategories } from '../../data/mockData';
import { Wrench, Cpu, Battery, Plug, CircleSlash, Paintbrush, AlertCircle, ClipboardCheck, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

const iconMap = {
  Wrench,
  Cpu,
  Battery,
  Plug,
  CircleSlash,
  Paintbrush,
  AlertCircle,
  ClipboardCheck
};

const ServiceCategoriesSection = () => {
  const navigate = useNavigate();

  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Popular EV Services
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Comprehensive service catalog for all EV segments - from periodic maintenance to emergency roadside assistance
          </p>
        </div>

        {/* Service Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {serviceCategories.map((service) => {
            const Icon = iconMap[service.icon];
            return (
              <Card 
                key={service.id} 
                className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer border-none"
                onClick={() => navigate(service.link)}
              >
                <CardHeader>
                  <div className="bg-green-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-600 transition-colors">
                    <Icon className="w-7 h-7 text-green-600 group-hover:text-white transition-colors" />
                  </div>
                  <CardTitle className="text-lg">{service.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600 mb-4">
                    {service.description}
                  </CardDescription>
                  <div className="flex items-center text-green-600 font-medium text-sm group-hover:text-green-700">
                    Learn More
                    <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* View All CTA */}
        <div className="text-center mt-12">
          <button 
            onClick={() => navigate('/services')}
            className="text-green-600 font-semibold hover:text-green-700 transition-colors inline-flex items-center"
          >
            View All Services
            <ArrowRight className="w-5 h-5 ml-2" />
          </button>
        </div>
      </div>
    </section>
  );
};

export default ServiceCategoriesSection;
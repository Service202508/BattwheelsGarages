import React from 'react';
import { services } from '../mockData';
import { Wrench, Monitor, CircleSlash, Cpu, Zap, Paintbrush, Battery, Plug } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

const iconMap = {
  Wrench,
  Monitor,
  CircleSlash,
  Cpu,
  Zap,
  Paintbrush,
  Battery,
  Plug
};

const ServicesSection = () => {
  return (
    <section id="services" className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Our Services
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Comprehensive EV maintenance and repair services to keep your electric vehicle running smoothly
          </p>
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {services.map((service) => {
            const Icon = iconMap[service.icon];
            return (
              <Card 
                key={service.id} 
                className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-2 cursor-pointer border-none"
              >
                <CardHeader>
                  <div className="bg-green-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-600 transition-colors">
                    <Icon className="w-7 h-7 text-green-600 group-hover:text-white transition-colors" />
                  </div>
                  <CardTitle className="text-lg">{service.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600">
                    {service.description}
                  </CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <a 
            href="#contact" 
            className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 transition-colors shadow-lg"
          >
            Get a Free Quote
          </a>
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
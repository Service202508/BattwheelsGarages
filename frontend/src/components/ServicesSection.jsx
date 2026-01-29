import React from 'react';
import { servicesByType } from '../mockData';
import { Bike, TramFront, Car, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

const iconMap = {
  Bike,
  TramFront,
  Car
};

const ServicesSection = () => {
  return (
    <section id="services" className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Services by EV Type
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Specialized onsite diagnostics and repair for all electric vehicle categories - from 2-wheelers to commercial 4-wheelers
          </p>
        </div>

        {/* Services Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {servicesByType.map((category) => {
            const Icon = iconMap[category.icon];
            return (
              <Card key={category.id} className="border-none shadow-lg hover:shadow-xl transition-shadow">
                <CardHeader>
                  <div className="bg-green-100 w-16 h-16 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-8 h-8 text-green-600" />
                  </div>
                  <CardTitle className="text-xl">{category.category}</CardTitle>
                  <CardDescription className="text-gray-600">
                    {category.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {category.services.map((service, idx) => (
                      <li key={idx} className="flex items-start space-x-2 text-sm">
                        <ArrowRight className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700">{service}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Bottom Note */}
        <div className="text-center bg-gray-900 text-white p-8 rounded-lg max-w-3xl mx-auto">
          <p className="text-lg font-semibold mb-2">
            🚫 We Do Not Service ICE Vehicles
          </p>
          <p className="text-gray-300 text-sm">
            100% focus on electric vehicle systems, battery technology, and EV electronics. Zero distraction from conventional vehicles.
          </p>
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
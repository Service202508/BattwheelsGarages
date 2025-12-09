import React from 'react';
import { Users, Wrench, TrendingUp, Building } from 'lucide-react';

const AboutSection = () => {
  return (
    <section id="about" className="py-20 bg-white">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              About Battwheels Garages
            </h2>
            <p className="text-xl text-gray-600">
              Operator-Led Company, Not MBA-Led
            </p>
          </div>

          {/* Main Content */}
          <div className="prose prose-lg max-w-none mb-12">
            <p className="text-gray-700 leading-relaxed mb-6">
              Battwheels Garages is India's first EV-only, onsite roadside assistance (RSA) and aftersales service company. 
              We exist to solve one core problem: <strong>EVs don't need towing first—they need diagnosis and repair on the spot.</strong>
            </p>
            
            <p className="text-gray-700 leading-relaxed mb-6">
              Traditional RSA models are fundamentally broken for electric vehicles. Towing wastes time, increases operational costs, 
              and kills vehicle uptime—especially critical for high-utilization fleets running 10-14 hours daily.
            </p>

            <p className="text-gray-700 leading-relaxed mb-6">
              We're not a marketing company running ads. We're an operations-first company with <strong>₹1 Crore revenue in Year 1</strong>, 
              a strong field engineering backbone, and real expertise in EV systems, battery technology, and fleet operations.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Wrench className="w-6 h-6 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">10,000+</div>
              <div className="text-sm text-gray-600">Vehicles Serviced</div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">90%</div>
              <div className="text-sm text-gray-600">Onsite Fix Rate</div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">50+</div>
              <div className="text-sm text-gray-600">EV Technicians</div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Building className="w-6 h-6 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">₹1Cr+</div>
              <div className="text-sm text-gray-600">Revenue Y1</div>
            </div>
          </div>

          {/* Vision Box */}
          <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-8 rounded-lg">
            <h3 className="text-2xl font-bold mb-4">Our Vision</h3>
            <p className="text-gray-300 leading-relaxed mb-4">
              To build India's EV Aftersales Infrastructure—a scalable, tech-enabled platform that supports the EV revolution 
              with onsite diagnostics, rapid response, and fleet-grade reliability.
            </p>
            <p className="text-gray-300 leading-relaxed">
              We're building for the next 5-7 years: COCO, FOCO, and FOFO garage models, AI-assisted diagnostics, 
              digital ticketing systems, and API-ready architecture for seamless OEM and fleet integrations.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
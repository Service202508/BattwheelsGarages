import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { serviceCategories } from '../data/mockData';
import { Wrench, Cpu, Battery, Plug, CircleSlash, Paintbrush, AlertCircle, ClipboardCheck, ArrowRight } from 'lucide-react';

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

const Services = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Complete EV After-Sales Services
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                End-to-end EV maintenance and repair for 2W, 3W, 4W & Commercial EVs. From periodic services to emergency roadside assistance.
              </p>
            </div>
          </div>
        </section>

        {/* Service Categories */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {serviceCategories.map((service) => {
                const Icon = iconMap[service.icon];
                return (
                  <div 
                    key={service.id}
                    className="bg-gray-50 border-2 border-gray-200 p-8 rounded-xl hover:border-green-500 hover:shadow-lg transition-all cursor-pointer group"
                    onClick={() => navigate(service.link)}
                  >
                    <div className="bg-green-100 w-16 h-16 rounded-xl flex items-center justify-center mb-6 group-hover:bg-green-600 transition-colors">
                      <Icon className="w-8 h-8 text-green-600 group-hover:text-white transition-colors" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-3">{service.title}</h3>
                    <p className="text-gray-600 mb-4">{service.description}</p>
                    <div className="flex items-center text-green-600 font-medium text-sm group-hover:text-green-700">
                      Learn More
                      <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-gradient-to-r from-green-600 to-green-500 text-white">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Book Your EV Service?</h2>
            <p className="text-green-50 mb-8">Open 365 days • 09:00 AM – 11:00 PM</p>
            <button 
              onClick={() => navigate('/book-service')}
              className="bg-white text-green-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Book Service Now
            </button>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Services;
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import SEO from '../components/common/SEO';
import GearBackground from '../components/common/GearBackground';
import { servicesApi } from '../utils/api';
import { serviceCategories as mockServices } from '../data/mockData';
import { Wrench, ArrowRight, Loader2, Zap, Battery, Settings, Truck } from 'lucide-react';

const Services = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      setLoading(true);
      const data = await servicesApi.getAll();
      
      if (data.services && data.services.length > 0) {
        setServices(data.services);
      } else {
        // Fallback to mock data if no services in DB
        console.log('No services from API, using mock data');
        setServices(mockServices);
      }
    } catch (err) {
      console.error('Error fetching services:', err);
      // Fallback to mock data on error
      setServices(mockServices);
      setError(null); // Don't show error, just use fallback
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (iconName) => {
    const icons = {
      Wrench: Wrench,
      Zap: Zap,
      Battery: Battery,
      Settings: Settings,
      Truck: Truck,
    };
    return icons[iconName] || Wrench;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <SEO 
        title="EV Services | Battwheels Garages - Onsite EV Repair & Maintenance"
        description="Comprehensive EV services including onsite repair, battery diagnostics, motor servicing, and fleet maintenance. 85% issues resolved on field."
        url="/services"
      />
      
      <Header />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-green-600 to-emerald-700 py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Our EV Services
          </h1>
          <p className="text-xl text-green-100 max-w-3xl mx-auto">
            Comprehensive onsite diagnostics, repair, and maintenance for all electric vehicle categories — from 2-wheelers to commercial fleets
          </p>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <Loader2 className="w-8 h-8 text-green-600 animate-spin" />
              <span className="ml-3 text-gray-600">Loading services...</span>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {services.map((service) => {
                const Icon = getIcon(service.icon);
                return (
                  <div
                    key={service.id}
                    className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 group"
                  >
                    {/* Service Header */}
                    <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-6">
                      <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center mb-4">
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-white">{service.title || service.name}</h3>
                    </div>

                    {/* Service Body */}
                    <div className="p-6">
                      <p className="text-gray-600 mb-6 line-clamp-3">
                        {service.short_description || service.description}
                      </p>

                      {/* Features */}
                      {service.features && service.features.length > 0 && (
                        <ul className="space-y-2 mb-6">
                          {service.features.slice(0, 3).map((feature, idx) => (
                            <li key={idx} className="flex items-center text-sm text-gray-600">
                              <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                      )}

                      {/* CTA */}
                      <div className="flex items-center justify-between">
                        <Link
                          to={`/book-service?service=${service.slug || service.id}`}
                          className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                          Book Service
                          <ArrowRight className="w-4 h-4 ml-2" />
                        </Link>
                        {service.slug && (
                          <Link
                            to={`/services/${service.slug}`}
                            className="text-green-600 hover:text-green-700 text-sm font-medium"
                          >
                            Learn More
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* CTA Section */}
          <div className="mt-16 bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 text-center">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Need a Custom Solution for Your Fleet?
            </h2>
            <p className="text-orange-100 mb-6 max-w-2xl mx-auto">
              We offer tailored maintenance programs for fleet operators, OEMs, and mobility platforms
            </p>
            <Link
              to="/fleet-oem"
              className="inline-flex items-center px-8 py-3 bg-white text-orange-600 font-bold rounded-xl hover:bg-orange-50 transition-colors"
            >
              Talk to Fleet Team
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Services;

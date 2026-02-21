import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import { Button } from '../components/ui/button';
import { periodicService, motorControllerService, batteryBMSService, chargerService, brakesTyresService, bodyPaintService, roadsideService, fleetService } from '../data/servicesData';
import { CheckCircle } from 'lucide-react';

const serviceMap = {
  'periodic': periodicService,
  'motor-controller': motorControllerService,
  'battery-bms': batteryBMSService,
  'charger': chargerService,
  'brakes-tyres': brakesTyresService,
  'body-paint': bodyPaintService,
  'roadside': roadsideService,
  'fleet': fleetService
};

const ServiceDetail = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const service = serviceMap[slug];

  if (!service) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Service Not Found</h1>
          <Button onClick={() => navigate('/services')}>Back to Services</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <GearBackground variant="default" />
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                {service.title}
              </h1>
              <p className="text-xl text-gray-600 mb-6">{service.subtitle}</p>
              <p className="text-lg text-gray-700 leading-relaxed">{service.description}</p>
            </div>
          </div>
        </section>

        {/* Service Details */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              {/* Segments (for periodic service) */}
              {service.segments && (
                <div className="space-y-12">
                  {service.segments.map((segment, index) => (
                    <div key={index}>
                      <h2 className="text-3xl font-bold text-gray-900 mb-6">{segment.name}</h2>
                      <div className="grid md:grid-cols-2 gap-6">
                        {segment.packages.map((pkg, pkgIndex) => (
                          <div key={pkgIndex} className="bg-gray-50 border-2 border-gray-200 p-8 rounded-xl hover:border-green-500 transition-colors">
                            <h3 className="text-xl font-bold text-gray-900 mb-2">{pkg.name}</h3>
                            <p className="text-green-600 font-semibold mb-4">{pkg.price}</p>
                            <ul className="space-y-2">
                              {pkg.includes.map((item, itemIndex) => (
                                <li key={itemIndex} className="flex items-start space-x-2 text-sm">
                                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                                  <span className="text-gray-700">{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Services List */}
              {service.services && (
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-6">What's Included</h2>
                  <div className="grid md:grid-cols-2 gap-4">
                    {service.services.map((item, index) => (
                      <div key={index} className="flex items-start space-x-3 bg-gray-50 p-4 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Ideal For */}
              {service.idealFor && (
                <div className="mt-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Ideal For</h2>
                  <div className="flex flex-wrap gap-3">
                    {service.idealFor.map((item, index) => (
                      <span key={index} className="bg-green-100 text-green-700 px-4 py-2 rounded-full font-medium">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA */}
              <div className="mt-12 bg-gradient-to-r from-green-600 to-green-500 text-white p-8 rounded-xl text-center">
                <h3 className="text-2xl font-bold mb-4">Ready to Book This Service?</h3>
                <p className="text-green-50 mb-6">Get your EV serviced by our expert technicians</p>
                <Button 
                  size="lg"
                  className="bg-white text-green-600 hover:bg-gray-100"
                  onClick={() => window.open('https://cloud-finance-suite.preview.emergentagent.com/submit-ticket', '_blank')}
                >
                  Book Service Now
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default ServiceDetail;
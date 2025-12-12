import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import { Button } from '../components/ui/button';
import { industries } from '../data/mockData';
import { Building, Truck, BatteryCharging, Package, User } from 'lucide-react';

const iconMap = {
  Building,
  Truck,
  BatteryCharging,
  Package,
  User
};

const Industries = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative">
      {/* Rotating Gears Background */}
      <GearBackground variant="industries" />
      
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Industries We Serve
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                From individual EV owners to large fleet operators and OEMs - we support the entire EV ecosystem with specialized services
              </p>
            </div>
          </div>
        </section>

        {/* Industries Detail */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-5xl mx-auto space-y-16">
              {industries.map((industry) => {
                const Icon = iconMap[industry.icon];
                // Use custom images for specific industries
                let industryImage;
                if (industry.id === 1) {
                  industryImage = '/assets/ev-oems.jpeg';
                } else if (industry.id === 2) {
                  industryImage = '/assets/fleet-operators.png';
                } else if (industry.id === 3) {
                  industryImage = '/assets/battery-swapping.jpg';
                } else if (industry.id === 4) {
                  industryImage = '/assets/hyperlocal-delivery.png';
                } else if (industry.id === 5) {
                  industryImage = '/assets/individual-ev-owners.webp';
                } else {
                  industryImage = `https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=600&h=400&fit=crop`;
                }
                
                return (
                  <div key={industry.id} className="grid md:grid-cols-2 gap-12 items-center">
                    <div className={industry.id % 2 === 0 ? 'md:order-2' : ''}>
                      <div className="bg-green-100 w-20 h-20 rounded-2xl flex items-center justify-center mb-6">
                        <Icon className="w-10 h-10 text-green-600" />
                      </div>
                      <h2 className="text-3xl font-bold text-gray-900 mb-4">{industry.title}</h2>
                      <p className="text-gray-700 leading-relaxed mb-6">{industry.description}</p>
                      
                      {/* Pain points and solutions */}
                      <div className="bg-gray-50 p-6 rounded-xl">
                        <h3 className="font-semibold text-gray-900 mb-3">How We Help:</h3>
                        <ul className="space-y-2 text-sm text-gray-700">
                          <li>• Fast onsite response minimizes downtime</li>
                          <li>• Specialized EV expertise for accurate diagnostics</li>
                          <li>• Custom SLAs and preventive maintenance programs</li>
                          <li>• Real-time tracking and reporting via Battwheels OS™</li>
                        </ul>
                      </div>
                    </div>
                    <div className={industry.id % 2 === 0 ? 'md:order-1' : ''}>
                      <img 
                        src={industryImage}
                        alt={industry.title}
                        className="rounded-2xl shadow-xl w-full h-auto object-cover"
                      />
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
            <h2 className="text-3xl font-bold mb-4">Want to Partner with Us?</h2>
            <p className="text-green-50 mb-8 max-w-2xl mx-auto">
              Whether you're a fleet operator, OEM, or individual owner - we have the right solution for your EV maintenance needs.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg"
                className="bg-white text-green-600 hover:bg-gray-100"
                onClick={() => navigate('/fleet-oem')}
              >
                Talk to Our Team
              </Button>
              <Button 
                size="lg"
                variant="outline"
                className="border-white text-white hover:bg-green-700"
                onClick={() => navigate('/book-service')}
              >
                Book Service
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Industries;
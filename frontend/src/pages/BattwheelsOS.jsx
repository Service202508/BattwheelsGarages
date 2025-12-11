import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import { Button } from '../components/ui/button';
import { Monitor, Smartphone, BarChart3, Zap, Bell, Link as LinkIcon, CheckCircle } from 'lucide-react';

const BattwheelsOS = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Monitor,
      title: 'Digital Job Cards & Workflows',
      description: 'Create, assign, and close digital job cards for every service and repair with complete tracking.'
    },
    {
      icon: Zap,
      title: 'EV Diagnostics Integration',
      description: 'OBD/diagnostic integration for controllers, BMS, motors, and other EV systems with GaragePRO-grade diagnostics.'
    },
    {
      icon: Smartphone,
      title: 'Technician Mobile App',
      description: 'Mobile app for technicians to receive jobs, access checklists, capture photos, and log parts and time.'
    },
    {
      icon: BarChart3,
      title: 'Fleet Dashboard',
      description: 'For OEMs and fleet operators: view fleet health, upcoming services, breakdown history, and download reports.'
    },
    {
      icon: Bell,
      title: 'Real-time Tracking & Notifications',
      description: 'Job status updates from Scheduled → In Progress → Completed with automatic SMS/email/WhatsApp notifications.'
    },
    {
      icon: LinkIcon,
      title: 'Seamless Integrations',
      description: 'Integration with telematics partners, OEM systems, and battery swap platforms for complete ecosystem connectivity.'
    }
  ];

  return (
    <div className="min-h-screen relative">
      {/* Rotating Gears Background */}
      <GearBackground variant="battwheels-os" />
      
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-gray-900 to-gray-800 text-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-block bg-green-600 text-white px-4 py-2 rounded-full text-sm font-semibold mb-6">
                Tech Platform
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Battwheels OS – The EV Aftersales Command Center
              </h1>
              <p className="text-xl text-gray-300 leading-relaxed mb-8">
                GaragePRO-grade diagnostics + field-force management + fleet dashboards in one EV-native platform.
              </p>
              <Button 
                size="lg"
                className="bg-green-600 hover:bg-green-700"
                onClick={() => navigate('/fleet-oem')}
              >
                Schedule a Demo
              </Button>
            </div>
          </div>
        </section>

        {/* Key Features */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Key Features
              </h2>
              <p className="text-lg text-gray-600 max-w-3xl mx-auto">
                Complete EV service management platform built for modern operations
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="bg-gray-50 p-8 rounded-xl">
                    <div className="bg-green-100 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                      <Icon className="w-8 h-8 text-green-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                    <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-20 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Who Benefits from Battwheels OS?</h2>
              
              <div className="space-y-6">
                <div className="bg-white p-8 rounded-xl border-l-4 border-green-600">
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Fleet Operators</h3>
                  <ul className="space-y-2">
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Monitor entire fleet health in real-time</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Reduce downtime with predictive maintenance</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Access detailed cost and performance reports</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-white p-8 rounded-xl border-l-4 border-blue-600">
                  <h3 className="text-xl font-bold text-gray-900 mb-3">EV OEMs</h3>
                  <ul className="space-y-2">
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Streamline warranty and aftersales management</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Integrate with existing systems via API</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Gain insights into vehicle performance across fleet</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-white p-8 rounded-xl border-l-4 border-purple-600">
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Service Centers</h3>
                  <ul className="space-y-2">
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Digitize operations with paperless workflows</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Improve technician efficiency and accountability</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">Track inventory and parts usage in real-time</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-gradient-to-r from-green-600 to-green-500 text-white">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Transform Your EV Operations?</h2>
            <p className="text-green-50 mb-8 max-w-2xl mx-auto">
              Schedule a personalized demo of Battwheels OS and see how we can optimize your fleet management and service operations.
            </p>
            <Button 
              size="lg"
              className="bg-white text-green-600 hover:bg-gray-100"
              onClick={() => navigate('/fleet-oem')}
            >
              Schedule Demo Now
            </Button>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default BattwheelsOS;
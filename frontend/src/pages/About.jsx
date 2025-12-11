import React from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { Wrench, Target, Eye, Leaf, Users, Building, TrendingUp } from 'lucide-react';

const About = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                About Battwheels Garages
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                India's first EV-only, onsite roadside assistance (RSA) and aftersales service company, built to solve one core problem: EVs don't need towing first—they need diagnosis and repair on the spot.
              </p>
            </div>
          </div>
        </section>

        {/* Story & Mission */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <div className="grid md:grid-cols-2 gap-12 mb-16">
                <div className="bg-green-50 p-8 rounded-xl">
                  <div className="bg-green-600 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                    <Target className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-4">Our Mission</h3>
                  <p className="text-gray-700 leading-relaxed">
                    Support India's EV revolution with high-uptime onsite after-sales service. Since our inception in 2024, we have served thousands of businesses and individual owners by offering reliable, swift, and expert services.
                  </p>
                </div>

                <div className="bg-blue-50 p-8 rounded-xl">
                  <div className="bg-blue-600 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                    <Eye className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-4">Our Vision</h3>
                  <p className="text-gray-700 leading-relaxed">
                    Nationwide onsite EV repair & maintenance network with COCO, FOCO, and FOFO garages plus a tech-driven field team to build India's EV aftersales infrastructure.
                  </p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
                <div className="text-center p-6 bg-gray-50 rounded-lg">
                  <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Wrench className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">10,000+</div>
                  <div className="text-sm text-gray-600">EVs Serviced</div>
                </div>

                <div className="text-center p-6 bg-gray-50 rounded-lg">
                  <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">85%</div>
                  <div className="text-sm text-gray-600">Onsite Resolution</div>
                </div>

                <div className="text-center p-6 bg-gray-50 rounded-lg">
                  <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Users className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">5,000+</div>
                  <div className="text-sm text-gray-600">Happy Customers</div>
                </div>

                <div className="text-center p-6 bg-gray-50 rounded-lg">
                  <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Building className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">11</div>
                  <div className="text-sm text-gray-600">Cities Covered</div>
                </div>
              </div>

              {/* What Makes Us Different */}
              <div className="mb-16">
                <h2 className="text-3xl font-bold text-gray-900 mb-8">What Makes Us Different</h2>
                <div className="space-y-6">
                  <div className="flex items-start space-x-4">
                    <div className="bg-green-100 p-3 rounded-lg flex-shrink-0">
                      <Wrench className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">Skilled EV Engineers</h3>
                      <p className="text-gray-600">Our engineers are specially trained in cutting-edge facilities, equipped with the latest technologies to deliver the highest quality EV service.</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="bg-green-100 p-3 rounded-lg flex-shrink-0">
                      <Target className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">Proven EV Expertise</h3>
                      <p className="text-gray-600">With our wealth of skills and experience, we can address any problem your EV may encounter, from battery issues to motor diagnostics.</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="bg-green-100 p-3 rounded-lg flex-shrink-0">
                      <TrendingUp className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">Fast Turnaround Time</h3>
                      <p className="text-gray-600">With our expansive workforce and network, we guarantee reliable service and faster turnaround time for maximum uptime.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sustainability */}
              <div className="bg-gradient-to-r from-green-600 to-green-500 text-white p-8 md:p-12 rounded-2xl">
                <div className="flex items-center space-x-4 mb-6">
                  <Leaf className="w-12 h-12" />
                  <h2 className="text-3xl font-bold">Sustainability That Serves You Better</h2>
                </div>
                <p className="text-green-50 leading-relaxed">
                  Sustainability is the main factor in whatever we deliver to our customers. By choosing our eco-friendly EV repair and servicing, we conserve energy and create a greener future. Our commitment to creating a greener planet delivers better products, smarter services, and happy customers—because a healthier earth means a healthy life for everyone.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default About;
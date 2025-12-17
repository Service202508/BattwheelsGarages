import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import SEO from '../components/common/SEO';
import { Button } from '../components/ui/button';
import { subscriptionPlans } from '../data/mockData';
import { CheckCircle, Star } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

const Plans = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative">
      <SEO 
        title="Subscription Plans - EV Service Packages"
        description="Choose from our range of EV subscription plans. Get priority service, roadside assistance, and annual maintenance packages for your electric vehicle."
        url="/plans"
      />
      <GearBackground variant="default" />
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Subscription Plans
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Choose the perfect maintenance plan for your EV needs - from individual owners to large fleet operations
              </p>
            </div>
          </div>
        </section>

        {/* Plans */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {subscriptionPlans.map((plan) => (
                <Card 
                  key={plan.id} 
                  className={`relative ${
                    plan.popular 
                      ? 'border-2 border-green-500 shadow-2xl' 
                      : 'border-gray-200'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <span className="bg-green-600 text-white px-4 py-1 rounded-full text-sm font-semibold flex items-center">
                        <Star className="w-4 h-4 mr-1 fill-current" />
                        Most Popular
                      </span>
                    </div>
                  )}
                  <CardHeader className="text-center pb-8 pt-8">
                    <CardTitle className="text-2xl mb-2">{plan.name}</CardTitle>
                    <CardDescription>{plan.subtitle}</CardDescription>
                    <div className="mt-4">
                      <div className="text-sm text-gray-500 mb-1">Starting from</div>
                      <div className="flex items-baseline justify-center gap-1">
                        <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                        <span className="text-sm text-gray-600">{plan.priceUnit}</span>
                      </div>
                      <div className="mt-2 text-sm text-green-600 font-medium">
                        or {plan.annualPrice}{plan.annualUnit}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start space-x-2 text-sm">
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button 
                      className={`w-full ${
                        plan.popular 
                          ? 'bg-green-600 hover:bg-green-700 text-white' 
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                      }`}
                      onClick={() => navigate('/fleet-oem')}
                    >
                      {plan.cta}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Enterprise Note */}
            <div className="mt-12 text-center bg-gray-50 p-8 rounded-xl max-w-4xl mx-auto">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Need a Custom Enterprise Plan?</h3>
              <p className="text-gray-600 mb-6">
                For large fleets (50+ vehicles), custom SLAs, dedicated onsite teams, or OEM partnerships, contact our sales team for a tailored solution.
              </p>
              <Button 
                size="lg"
                onClick={() => navigate('/fleet-oem')}
              >
                Contact Sales Team
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Plans;
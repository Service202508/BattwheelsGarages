import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import SEO from '../components/common/SEO';
import { Button } from '../components/ui/button';
import { CheckCircle, Star, Bike, Car, Truck } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

// Plan data by vehicle category
const plansByCategory = {
  '2wheeler': {
    starter: {
      name: 'Starter',
      subtitle: 'Perfect for individual EV owners',
      monthlyPrice: '₹499',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹4,499',
      annualUnit: '/annually/vehicle',
      features: [
        'Coverage for 1 vehicle',
        '1 periodic service per month',
        '6 periodic services (annual)',
        '2 breakdown visits per month',
        'Unlimited breakdown visits (annual)',
        'Standard OEM support',
        'Digital service history',
        'Standard diagnostics'
      ],
      cta: 'Get Started',
      popular: false
    },
    fleetEssential: {
      name: 'Fleet Essential',
      subtitle: 'For growing fleet operations',
      monthlyPrice: '₹699',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹5,599',
      annualUnit: '/annually/vehicle',
      features: [
        'Everything in Starter, plus:',
        'Priority support (30-minute response)',
        'Fleet dashboard access',
        'Preventive maintenance scheduling',
        'Centralized invoicing',
        'Dedicated service manager'
      ],
      cta: 'Get Started',
      popular: true
    },
    fleetPro: {
      name: 'Fleet Essential Pro',
      subtitle: 'Enterprise-grade fleet management',
      monthlyPrice: '₹799',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹6,499',
      annualUnit: '/annually/vehicle',
      features: [
        'Everything in Fleet Essential, plus:',
        'Custom SLAs and uptime guarantees',
        'Battwheels OS™ integration',
        'Telematics integration',
        'Monthly performance reports',
        'Onsite dedicated team option'
      ],
      cta: 'Contact Sales',
      popular: false
    }
  },
  '3wheeler': {
    starter: {
      name: 'Starter',
      subtitle: 'Perfect for individual EV owners',
      monthlyPrice: '₹799',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹6,699',
      annualUnit: '/annually/vehicle',
      features: [
        'Coverage for 1 vehicle',
        '1 periodic service per month',
        '6 periodic services (annual)',
        '2 breakdown visits per month',
        'Unlimited breakdown visits (annual)',
        'Standard OEM support',
        'Digital service history',
        'Standard diagnostics'
      ],
      cta: 'Get Started',
      popular: false
    },
    fleetEssential: {
      name: 'Fleet Essential',
      subtitle: 'For growing fleet operations',
      monthlyPrice: '₹1,099',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹7,599',
      annualUnit: '/annually/vehicle',
      features: [
        'Everything in Starter, plus:',
        'Priority support (30-minute response)',
        'Fleet dashboard access',
        'Preventive maintenance scheduling',
        'Centralized invoicing',
        'Dedicated service manager'
      ],
      cta: 'Get Started',
      popular: true
    },
    fleetPro: {
      name: 'Fleet Essential Pro',
      subtitle: 'Enterprise-grade fleet management',
      monthlyPrice: '₹1,199',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹8,499',
      annualUnit: '/annually/vehicle',
      features: [
        'Everything in Fleet Essential, plus:',
        'Custom SLAs and uptime guarantees',
        'Battwheels OS™ integration',
        'Telematics integration',
        'Monthly performance reports',
        'Onsite dedicated team option'
      ],
      cta: 'Contact Sales',
      popular: false
    }
  },
  '4wheeler': {
    starter: {
      name: 'Starter',
      subtitle: 'Perfect for individual EV owners',
      monthlyPrice: '₹1,299',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹8,699',
      annualUnit: '/annually/vehicle',
      features: [
        'Coverage for 1 vehicle',
        '1 periodic service per month',
        '6 periodic services (annual)',
        '2 breakdown visits per month',
        'Unlimited breakdown visits (annual)',
        'Standard OEM support',
        'Digital service history',
        'Standard diagnostics'
      ],
      cta: 'Get Started',
      popular: false
    },
    fleetEssential: {
      name: 'Fleet Essential',
      subtitle: 'For growing fleet operations',
      monthlyPrice: '₹1,399',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹9,599',
      annualUnit: '/annually/vehicle',
      features: [
        'Everything in Starter, plus:',
        'Priority support (30-minute response)',
        'Fleet dashboard access',
        'Preventive maintenance scheduling',
        'Centralized invoicing',
        'Dedicated service manager'
      ],
      cta: 'Get Started',
      popular: true
    },
    fleetPro: {
      name: 'Fleet Essential Pro',
      subtitle: 'Enterprise-grade fleet management',
      monthlyPrice: '₹1,599',
      monthlyUnit: '/month/vehicle',
      annualPrice: '₹10,199',
      annualUnit: '/annually/vehicle',
      features: [
        'Everything in Fleet Essential, plus:',
        'Custom SLAs and uptime guarantees',
        'Battwheels OS™ integration',
        'Telematics integration',
        'Monthly performance reports',
        'Onsite dedicated team option'
      ],
      cta: 'Contact Sales',
      popular: false
    }
  }
};

const vehicleCategories = [
  { id: '2wheeler', label: '2 Wheeler', icon: Bike },
  { id: '3wheeler', label: '3 Wheeler', icon: Truck },
  { id: '4wheeler', label: '4 Wheeler', icon: Car }
];

const Plans = () => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('2wheeler');
  const [billingCycle, setBillingCycle] = useState('monthly');

  const currentPlans = plansByCategory[selectedCategory];
  const plansArray = [currentPlans.starter, currentPlans.fleetEssential, currentPlans.fleetPro];

  return (
    <div className="min-h-screen relative">
      <SEO 
        title="Subscription Plans - EV Service Packages"
        description="Choose from our range of EV subscription plans for 2-wheelers, 3-wheelers, and 4-wheelers. Get priority service, roadside assistance, and annual maintenance packages."
        url="/plans"
      />
      <GearBackground variant="default" />
      <Header />
      <main>
        {/* Hero */}
        <section className="py-16 md:py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Subscription Plans
              </h1>
              <p className="text-lg md:text-xl text-gray-600 leading-relaxed mb-10">
                Choose the perfect maintenance plan for your EV needs - from individual owners to large fleet operations
              </p>

              {/* Vehicle Category Selector */}
              <div className="flex flex-col items-center space-y-6">
                <p className="text-sm font-medium text-gray-700">Select your vehicle type:</p>
                <div className="inline-flex bg-gray-100 rounded-xl p-1.5 shadow-inner">
                  {vehicleCategories.map((category) => {
                    const IconComponent = category.icon;
                    const isSelected = selectedCategory === category.id;
                    return (
                      <button
                        key={category.id}
                        onClick={() => setSelectedCategory(category.id)}
                        className={`
                          flex items-center space-x-2 px-5 py-3 rounded-lg font-medium text-sm
                          transition-all duration-300 ease-in-out
                          ${isSelected 
                            ? 'bg-green-600 text-white shadow-lg transform scale-105' 
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
                          }
                        `}
                      >
                        <IconComponent className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-gray-500'}`} />
                        <span>{category.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Billing Cycle Toggle */}
                <div className="inline-flex bg-gray-100 rounded-lg p-1 mt-4">
                  <button
                    onClick={() => setBillingCycle('monthly')}
                    className={`
                      px-4 py-2 rounded-md text-sm font-medium transition-all duration-200
                      ${billingCycle === 'monthly' 
                        ? 'bg-white text-gray-900 shadow-sm' 
                        : 'text-gray-600 hover:text-gray-900'
                      }
                    `}
                  >
                    Monthly
                  </button>
                  <button
                    onClick={() => setBillingCycle('annual')}
                    className={`
                      px-4 py-2 rounded-md text-sm font-medium transition-all duration-200
                      ${billingCycle === 'annual' 
                        ? 'bg-white text-gray-900 shadow-sm' 
                        : 'text-gray-600 hover:text-gray-900'
                      }
                    `}
                  >
                    Annual <span className="text-green-600 text-xs ml-1">Save 25%</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Plans */}
        <section className="py-16 md:py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-3 gap-6 lg:gap-8 max-w-6xl mx-auto">
              {plansArray.map((plan, index) => (
                <div
                  key={`${selectedCategory}-${index}`}
                  className="transform transition-all duration-500 ease-out"
                  style={{
                    animation: 'fadeInUp 0.5s ease-out forwards',
                    animationDelay: `${index * 0.1}s`
                  }}
                >
                  <Card 
                    className={`relative h-full flex flex-col ${
                      plan.popular 
                        ? 'border-2 border-green-500 shadow-2xl scale-105 z-10' 
                        : 'border border-gray-200 hover:border-green-300 hover:shadow-lg'
                    } transition-all duration-300`}
                  >
                    {plan.popular && (
                      <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                        <span className="bg-green-600 text-white px-4 py-1.5 rounded-full text-sm font-semibold flex items-center shadow-lg">
                          <Star className="w-4 h-4 mr-1 fill-current" />
                          Most Popular
                        </span>
                      </div>
                    )}
                    <CardHeader className="text-center pb-6 pt-8">
                      <CardTitle className="text-2xl font-bold mb-2">{plan.name}</CardTitle>
                      <CardDescription className="text-gray-500">{plan.subtitle}</CardDescription>
                      <div className="mt-6">
                        <div className="text-sm text-gray-500 mb-2">Starting from</div>
                        <div className="flex items-baseline justify-center gap-1">
                          <span className="text-4xl font-bold text-gray-900">
                            {billingCycle === 'monthly' ? plan.monthlyPrice : plan.annualPrice}
                          </span>
                        </div>
                        <span className="text-sm text-gray-600">
                          {billingCycle === 'monthly' ? plan.monthlyUnit : plan.annualUnit}
                        </span>
                        {billingCycle === 'monthly' && (
                          <div className="mt-3 text-sm text-green-600 font-medium">
                            or {plan.annualPrice} {plan.annualUnit}
                          </div>
                        )}
                        {billingCycle === 'annual' && (
                          <div className="mt-3">
                            <span className="inline-block bg-green-100 text-green-700 text-xs font-semibold px-2 py-1 rounded-full">
                              Best Value
                            </span>
                          </div>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="flex-grow flex flex-col">
                      <ul className="space-y-3 mb-8 flex-grow">
                        {plan.features.map((feature, featureIndex) => (
                          <li key={featureIndex} className="flex items-start space-x-3 text-sm">
                            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                            <span className="text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      <Button 
                        className={`w-full py-3 text-base font-semibold ${
                          plan.popular 
                            ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl' 
                            : 'bg-gray-100 hover:bg-gray-200 text-gray-900 hover:text-green-700'
                        } transition-all duration-200`}
                        onClick={() => navigate('/fleet-oem')}
                      >
                        {plan.cta}
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>

            {/* Enterprise Note */}
            <div className="mt-16 text-center bg-gradient-to-br from-gray-50 to-green-50 p-8 md:p-12 rounded-2xl max-w-4xl mx-auto border border-gray-100">
              <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">Need a Custom Enterprise Plan?</h3>
              <p className="text-gray-600 mb-8 text-lg">
                For large fleets (50+ vehicles), custom SLAs, dedicated onsite teams, or OEM partnerships, contact our sales team for a tailored solution.
              </p>
              <Button 
                size="lg"
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg font-semibold shadow-lg hover:shadow-xl transition-all"
                onClick={() => navigate('/fleet-oem')}
              >
                Contact Sales Team
              </Button>
            </div>

            {/* Trust Badges */}
            <div className="mt-16 text-center">
              <p className="text-sm text-gray-500 mb-6">Trusted by leading EV brands and fleet operators</p>
              <div className="flex flex-wrap justify-center items-center gap-6 opacity-70">
                <div className="text-gray-400 font-semibold text-sm">Indofast Energy</div>
                <div className="text-gray-400 font-semibold text-sm">Magenta Mobility</div>
                <div className="text-gray-400 font-semibold text-sm">Lithium</div>
                <div className="text-gray-400 font-semibold text-sm">Exponent Energy</div>
                <div className="text-gray-400 font-semibold text-sm">Omega Seiki</div>
                <div className="text-gray-400 font-semibold text-sm">Sun Mobility</div>
                <div className="text-gray-400 font-semibold text-sm">Zypp Electric</div>
                <div className="text-gray-400 font-semibold text-sm">Driveo Electric</div>
                <div className="text-gray-400 font-semibold text-sm">Indus Green</div>
                <div className="text-gray-400 font-semibold text-sm">Turno</div>
                <div className="text-gray-500 font-medium text-sm">and many more...</div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />

      {/* Animation Keyframes */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Plans;

/**
 * Marketplace Landing Page - Premium Design
 * Matches Battwheels website design language
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import GearBackground from '../../components/common/GearBackground';
import { useMarketplace } from '../../context/MarketplaceContext';
import {
  Wrench,
  Car,
  Zap,
  ArrowRight,
  ShoppingCart,
  Battery,
  Truck,
  Bike,
  CheckCircle,
  Shield,
  Package,
  Clock,
  MapPin,
  BadgeCheck,
  Sparkles
} from 'lucide-react';

const MarketplaceLanding = () => {
  const { getCartCount } = useMarketplace();

  const features = [
    {
      icon: BadgeCheck,
      title: 'Battwheels Certified',
      description: 'All products tested & verified by our technicians'
    },
    {
      icon: Shield,
      title: 'Warranty Included',
      description: 'Up to 36 months coverage on vehicles & parts'
    },
    {
      icon: Truck,
      title: 'Pan-India Delivery',
      description: 'Fast shipping across 11 cities'
    },
    {
      icon: Clock,
      title: 'Quick Support',
      description: '24/7 technical assistance available'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 relative">
      <GearBackground variant="services" />
      
      <Helmet>
        <title>EV Marketplace | Battwheels Garages - Parts & Vehicles</title>
        <meta name="description" content="Shop genuine EV spare parts, batteries, diagnostic tools, and certified electric vehicles. New & refurbished 2W, 3W, 4W EVs from top OEMs." />
      </Helmet>

      <Header />

      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-green-600 to-emerald-700 py-16 md:py-24 relative overflow-hidden">
          {/* Decorative Elements */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-10 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
            <div className="absolute bottom-10 right-10 w-96 h-96 bg-emerald-300 rounded-full blur-3xl" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm text-white px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Zap className="w-4 h-4" />
                Powered by Battwheels OS
              </div>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
                EV <span className="text-emerald-200">Marketplace</span>
              </h1>
              
              <p className="text-xl text-green-100 max-w-2xl mx-auto mb-8">
                Your one-stop destination for certified EV spare parts, components, and electric vehicles
              </p>
              
              {/* Cart Badge */}
              {getCartCount() > 0 && (
                <Link
                  to="/marketplace/cart"
                  className="inline-flex items-center gap-2 bg-white text-green-700 hover:bg-green-50 px-6 py-3 rounded-full font-semibold transition-all shadow-lg hover:shadow-xl"
                >
                  <ShoppingCart className="w-5 h-5" />
                  View Cart ({getCartCount()} items)
                  <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>
          </div>
        </section>

        {/* Main Categories Section */}
        <section className="py-16 md:py-20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                What are you looking for?
              </h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Browse our curated collection of certified EV products
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
              {/* Spares & Components Card */}
              <Link
                to="/marketplace/spares"
                className="group relative bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-2"
              >
                {/* Top Gradient Bar */}
                <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500" />
                
                {/* Decorative Background */}
                <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-green-50 to-transparent rounded-bl-full opacity-50" />
                
                <div className="p-8 relative">
                  {/* Icon */}
                  <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Wrench className="w-10 h-10 text-white" />
                  </div>
                  
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">
                    Spares & Components
                  </h3>
                  
                  <p className="text-gray-600 mb-6 leading-relaxed">
                    Certified EV spare parts, batteries, controllers, motors, and professional diagnostic tools.
                  </p>
                  
                  {/* Categories Pills */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    {['Controllers', 'Motors', 'Batteries', 'Diagnostics'].map((cat) => (
                      <span key={cat} className="bg-green-50 text-green-700 px-3 py-1.5 rounded-full text-sm font-medium">
                        {cat}
                      </span>
                    ))}
                  </div>

                  {/* Vehicle Types */}
                  <div className="flex items-center gap-6 mb-6 text-sm text-gray-500">
                    <span className="flex items-center gap-1.5">
                      <Bike className="w-4 h-4" /> 2-Wheeler
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Truck className="w-4 h-4" /> 3-Wheeler
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Car className="w-4 h-4" /> 4-Wheeler
                    </span>
                  </div>

                  {/* CTA */}
                  <div className="flex items-center text-green-600 font-semibold group-hover:text-green-700">
                    Browse Parts
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-2 transition-transform" />
                  </div>
                </div>
              </Link>

              {/* Electric Vehicles Card */}
              <Link
                to="/marketplace/vehicles"
                className="group relative bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-2"
              >
                {/* Top Gradient Bar */}
                <div className="h-2 bg-gradient-to-r from-blue-500 to-indigo-500" />
                
                {/* Decorative Background */}
                <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-blue-50 to-transparent rounded-bl-full opacity-50" />
                
                <div className="p-8 relative">
                  {/* Icon */}
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Car className="w-10 h-10 text-white" />
                  </div>
                  
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">
                    Electric Vehicles
                  </h3>
                  
                  <p className="text-gray-600 mb-6 leading-relaxed">
                    New and certified refurbished electric vehicles from India&apos;s top OEMs. 2W, 3W, and 4W options.
                  </p>
                  
                  {/* Condition Badges */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    <span className="bg-green-50 text-green-700 px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> New
                    </span>
                    <span className="bg-purple-50 text-purple-700 px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1">
                      <Shield className="w-3 h-3" /> Certified Refurbished
                    </span>
                  </div>

                  {/* OEM Brands */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    {['Ather', 'Ola', 'TVS', 'Tata', 'Mahindra'].map((oem) => (
                      <span key={oem} className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm">
                        {oem}
                      </span>
                    ))}
                    <span className="bg-gray-100 text-gray-500 px-3 py-1 rounded-full text-sm">+3 more</span>
                  </div>

                  {/* CTA */}
                  <div className="flex items-center text-blue-600 font-semibold group-hover:text-blue-700">
                    Browse Vehicles
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-2 transition-transform" />
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 bg-white">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-4 gap-8 max-w-5xl mx-auto">
              {features.map((feature, idx) => (
                <div key={idx} className="text-center group">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-50 to-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                    <feature.icon className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Technician CTA Section */}
        <section className="py-12 bg-gradient-to-r from-gray-900 to-gray-800">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 max-w-5xl mx-auto">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Zap className="w-7 h-7 text-white" />
                </div>
                <div className="text-white">
                  <h3 className="font-bold text-lg">Are you a technician?</h3>
                  <p className="text-gray-400 text-sm">Get 20% off with Technician Quick-Order Mode</p>
                </div>
              </div>
              <Link
                to="/marketplace/technician"
                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-8 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
              >
                <Wrench className="w-5 h-5" />
                Quick-Order Mode
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default MarketplaceLanding;

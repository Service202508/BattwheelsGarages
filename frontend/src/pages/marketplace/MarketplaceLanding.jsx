/**
 * Marketplace Landing Page - Main Entry Point
 * Bifurcated into: Spares & Components | Electric Vehicles
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { useMarketplace } from '../../context/MarketplaceContext';
import {
  Wrench,
  Car,
  Zap,
  ArrowRight,
  ShoppingCart,
  Battery,
  Settings,
  Truck,
  Bike,
  CheckCircle,
  Shield,
  Package
} from 'lucide-react';

const MarketplaceLanding = () => {
  const { getCartCount } = useMarketplace();

  return (
    <>
      <Helmet>
        <title>EV Marketplace | Battwheels Garages</title>
        <meta name="description" content="Shop genuine EV spare parts, batteries, diagnostic tools, and certified electric vehicles. New & refurbished 2W, 3W, 4W EVs from top OEMs." />
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white py-16 md:py-24">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 bg-[#12B76A]/20 text-[#12B76A] px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Zap className="w-4 h-4" />
                Powered by Battwheels OS
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
                EV <span className="text-[#12B76A]">Marketplace</span>
              </h1>
              <p className="text-gray-300 text-lg md:text-xl mb-8 max-w-2xl mx-auto">
                Your one-stop destination for certified EV spare parts, components, and electric vehicles
              </p>
              
              {/* Cart Link */}
              {getCartCount() > 0 && (
                <Link
                  to="/marketplace/cart"
                  className="inline-flex items-center gap-2 bg-[#12B76A] hover:bg-[#0F9F5F] text-white px-6 py-3 rounded-lg font-medium transition-colors mb-8"
                >
                  <ShoppingCart className="w-5 h-5" />
                  View Cart ({getCartCount()} items)
                </Link>
              )}
            </div>
          </div>
        </section>

        {/* Main Categories Section */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
              
              {/* Spares & Components */}
              <Link
                to="/marketplace/spares"
                className="group relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-[#12B76A] to-[#0B8A44]" />
                <div className="p-8">
                  <div className="w-16 h-16 bg-[#12B76A]/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Wrench className="w-8 h-8 text-[#12B76A]" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-3">
                    Spares & Components
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Certified EV spare parts, batteries, controllers, motors, and diagnostic tools for all vehicle types.
                  </p>
                  
                  {/* Sub-categories */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    {['Controllers', 'Motors', 'Batteries', 'Throttles', 'Displays', 'Diagnostic Tools'].map((cat) => (
                      <span key={cat} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                        {cat}
                      </span>
                    ))}
                  </div>

                  {/* Vehicle Types */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Bike className="w-4 h-4" />
                      2W
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Truck className="w-4 h-4" />
                      3W
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Car className="w-4 h-4" />
                      4W
                    </div>
                  </div>

                  <div className="flex items-center text-[#12B76A] font-medium group-hover:gap-3 transition-all">
                    Browse Parts
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Link>

              {/* Electric Vehicles */}
              <Link
                to="/marketplace/vehicles"
                className="group relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-500 to-blue-600" />
                <div className="p-8">
                  <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Car className="w-8 h-8 text-blue-500" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-3">
                    Electric Vehicles
                  </h2>
                  <p className="text-gray-600 mb-6">
                    New and certified refurbished electric vehicles from top OEMs. 2-wheelers, 3-wheelers, and 4-wheelers.
                  </p>
                  
                  {/* Vehicle Conditions */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      New
                    </span>
                    <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      Certified Refurbished
                    </span>
                  </div>

                  {/* OEMs */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    {['Ather', 'Ola', 'TVS', 'Bajaj', 'Tata', 'Mahindra'].map((oem) => (
                      <span key={oem} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                        {oem}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center text-blue-500 font-medium group-hover:gap-3 transition-all">
                    Browse Vehicles
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
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
              <div className="text-center">
                <div className="w-12 h-12 bg-[#12B76A]/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-6 h-6 text-[#12B76A]" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Battwheels Certified</h3>
                <p className="text-sm text-gray-600">All products tested & verified</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-[#12B76A]/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-6 h-6 text-[#12B76A]" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Warranty Included</h3>
                <p className="text-sm text-gray-600">Up to 36 months coverage</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-[#12B76A]/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Truck className="w-6 h-6 text-[#12B76A]" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Pan-India Delivery</h3>
                <p className="text-sm text-gray-600">Fast shipping across 11 cities</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-[#12B76A]/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Package className="w-6 h-6 text-[#12B76A]" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Easy Returns</h3>
                <p className="text-sm text-gray-600">7-day return policy</p>
              </div>
            </div>
          </div>
        </section>

        {/* Technician Mode CTA */}
        <section className="py-12 bg-gray-900 text-white">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 max-w-5xl mx-auto">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#12B76A] rounded-xl flex items-center justify-center">
                  <Wrench className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Are you a technician?</h3>
                  <p className="text-gray-400 text-sm">Get 20% off with Technician Quick-Order Mode</p>
                </div>
              </div>
              <Link
                to="/marketplace/technician"
                className="bg-[#12B76A] hover:bg-[#0F9F5F] text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <Zap className="w-5 h-5" />
                Quick-Order Mode
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
};

export default MarketplaceLanding;

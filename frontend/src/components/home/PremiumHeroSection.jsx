import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Phone, CheckCircle2, Search, Wrench, Ban } from 'lucide-react';
import { Button } from '../ui/button';

const PremiumHeroSection = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const vehicleTypes = [
    {
      id: '2w',
      name: '2-Wheeler EVs',
      category: 'Scooters & Bikes',
      count: '50+ Models',
      image: '/assets/2w-ev.png',
      emoji: '🛵'
    },
    {
      id: '3w',
      name: '3-Wheeler EVs',
      category: 'Auto Rickshaws',
      count: '30+ Models',
      image: '/assets/3w-ev.jpeg',
      emoji: '🛺'
    },
    {
      id: '4w',
      name: '4-Wheeler EVs',
      category: 'Cars & SUVs',
      count: '40+ Models',
      image: '/assets/4w-car.webp',
      emoji: '🚗'
    },
    {
      id: 'commercial',
      name: 'Commercial EVs',
      category: 'Trucks & Vans',
      count: '25+ Models',
      image: '/assets/commercial-ev.png',
      emoji: '🚚'
    }
  ];

  const processSteps = [
    {
      icon: Ban,
      title: 'No Towing First',
      description: 'We come to you',
      gradient: 'from-red-500 to-pink-500'
    },
    {
      icon: Search,
      title: 'Diagnose Onsite',
      description: 'Advanced diagnostics',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: Wrench,
      title: 'Repair On-Spot',
      description: 'Fix where you are',
      gradient: 'from-orange-500 to-yellow-500'
    },
    {
      icon: CheckCircle2,
      title: 'Resume Operations',
      description: 'Back on the road',
      gradient: 'from-green-500 to-emerald-500'
    }
  ];

  return (
    <section className="relative min-h-screen overflow-hidden bg-gradient-to-br from-green-50 via-white to-green-50">
      {/* Animated Background Mesh - Subtle Green Tones */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 left-0 w-96 h-96 bg-green-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-300 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000" />
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-green-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000" />
      </div>
      
      {/* Top accent gradient */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-emerald-400 to-green-500" />

      <div className="relative container mx-auto px-4 py-12 lg:py-20">
        <div className="grid lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Section - Premium Floating Card */}
          <div className={`lg:col-span-5 transform transition-all duration-1000 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}>
            <div className="relative">
              {/* Glassmorphic Card */}
              <div className="relative backdrop-blur-2xl bg-white/95 rounded-3xl p-8 lg:p-10 shadow-2xl border border-white/50">
                {/* Glow Effect */}
                <div className="absolute -inset-1 bg-gradient-to-r from-green-600 to-orange-600 rounded-3xl blur-2xl opacity-20 animate-pulse" />
                
                <div className="relative z-10">
                  {/* Main Headline */}
                  <h1 className="text-4xl lg:text-5xl font-extrabold text-gray-900 leading-tight mb-4" style={{ letterSpacing: '-0.5px' }}>
                    EVs Don't Need Towing First.
                  </h1>
                  
                  <h2 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-500 bg-clip-text text-transparent mb-6">
                    They Need Diagnosis & Repair Onsite.
                  </h2>

                  <div className="h-px bg-gradient-to-r from-green-500/50 via-green-500 to-transparent mb-6" />

                  {/* Supporting Text */}
                  <p className="text-lg text-gray-700 mb-8 leading-relaxed">
                    India's first <span className="font-semibold text-gray-900">no-towing-first</span> EV service model. 
                    We diagnose and fix your 2W, 3W, 4W & commercial EVs where they stop—maximizing uptime, minimizing costs.
                  </p>

                  {/* The Battwheels Difference */}
                  <div className="mb-8">
                    <h3 className="text-center text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6">
                      The Battwheels Difference
                    </h3>
                    
                    {/* Process Flow */}
                    <div className="grid grid-cols-4 gap-3 mb-6">
                      {processSteps.map((step, index) => {
                        const Icon = step.icon;
                        return (
                          <div
                            key={step.title}
                            className="flex flex-col items-center text-center group cursor-pointer"
                            style={{ animationDelay: `${index * 150}ms` }}
                          >
                            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.gradient} p-0.5 mb-2 transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 shadow-lg`}>
                              <div className="w-full h-full rounded-2xl bg-white flex items-center justify-center">
                                <Icon className="w-7 h-7 text-gray-700" />
                              </div>
                            </div>
                            <p className="text-xs font-semibold text-gray-800">{step.title}</p>
                            <p className="text-xs text-gray-500">{step.description}</p>
                          </div>
                        );
                      })}
                    </div>

                    {/* Connecting Line */}
                    <div className="relative h-1 bg-gradient-to-r from-red-500 via-blue-500 via-orange-500 to-green-500 rounded-full mb-6 opacity-30" />
                  </div>

                  {/* Stats Badges */}
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 p-4 border border-green-200/50">
                      <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent mb-1">80-90%</div>
                      <div className="h-1 w-3/4 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full mb-2" />
                      <div className="text-xs font-medium text-gray-700">Issues Resolved</div>
                      <div className="text-xs text-gray-500">On Field</div>
                    </div>
                    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-50 to-yellow-50 p-4 border border-orange-200/50">
                      <div className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-yellow-600 bg-clip-text text-transparent mb-1">10,000+</div>
                      <div className="h-1 w-3/4 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-full mb-2" />
                      <div className="text-xs font-medium text-gray-700">Maximum Uptime</div>
                      <div className="text-xs text-gray-500">For Your Fleet</div>
                    </div>
                  </div>

                  {/* Premium CTA Buttons */}
                  <div className="space-y-3 mb-8">
                    <Link to="/book-service" className="block">
                      <button className="relative w-full group overflow-hidden rounded-2xl bg-gradient-to-r from-orange-500 to-orange-600 p-0.5 transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/50 hover:-translate-y-0.5">
                        <div className="relative bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl px-8 py-4 text-white font-bold text-lg flex items-center justify-center gap-3">
                          {/* Shine effect */}
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                          <Calendar className="w-5 h-5" />
                          <span>Book EV Service Now</span>
                        </div>
                      </button>
                    </Link>

                    <Link to="/fleet-oem" className="block">
                      <button className="relative w-full group overflow-hidden rounded-2xl bg-white border-2 border-orange-500 transition-all duration-300 hover:bg-orange-500 hover:shadow-xl hover:-translate-y-0.5">
                        <div className="px-8 py-4 font-semibold text-lg flex items-center justify-center gap-3 text-orange-600 group-hover:text-white transition-colors">
                          <Phone className="w-5 h-5 transition-transform group-hover:rotate-12" />
                          <span>Talk to Fleet & OEM Team</span>
                        </div>
                      </button>
                    </Link>
                  </div>

                  {/* Trust Badges */}
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { icon: '🗓️', text: 'Open 365 Days' },
                      { icon: '⚡', text: '24/7 Emergency' },
                      { icon: '🇮🇳', text: 'Pan-India' }
                    ].map((badge) => (
                      <div
                        key={badge.text}
                        className="flex flex-col items-center p-3 bg-white/80 border border-gray-200 rounded-xl hover:shadow-md hover:-translate-y-1 transition-all duration-300 cursor-pointer"
                      >
                        <span className="text-2xl mb-1">{badge.icon}</span>
                        <span className="text-xs font-medium text-gray-700 text-center">{badge.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Section - Vehicle Showcase */}
          <div className={`lg:col-span-7 transform transition-all duration-1000 delay-300 ${
            isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'
          }`}>
            <div className="mb-6 text-center lg:text-left">
              <h3 className="text-gray-900 text-2xl lg:text-3xl font-bold mb-2">We Service All EV Types</h3>
              <p className="text-gray-700 text-lg">From 2-wheelers to commercial fleets</p>
            </div>

            <div className="grid grid-cols-2 gap-4 lg:gap-6">
              {vehicleTypes.map((vehicle, index) => (
                <div
                  key={vehicle.id}
                  className="group relative overflow-hidden rounded-2xl bg-white shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* Vehicle Image */}
                  <div className="relative h-40 lg:h-48 overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100">
                    <img
                      src={vehicle.image}
                      alt={vehicle.name}
                      className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700"
                      loading="lazy"
                    />
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>

                  {/* Card Content */}
                  <div className="p-5">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="text-lg font-bold text-gray-900 mb-1">{vehicle.name}</h4>
                        <p className="text-sm text-gray-600">{vehicle.category}</p>
                      </div>
                      <span className="text-3xl">{vehicle.emoji}</span>
                    </div>
                    
                    {/* Stats Chip */}
                    <div className="inline-flex items-center px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-semibold border border-green-200">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      {vehicle.count}
                    </div>
                  </div>

                  {/* Hover Glow Effect */}
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-green-500/20 to-orange-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Gradient Fade - Smooth transition to next section */}
      <div className="absolute bottom-0 left-0 right-0 h-64 bg-gradient-to-t from-green-900 via-green-800/50 to-transparent" />
      
      {/* Decorative wave transition */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg className="w-full h-24 md:h-32" viewBox="0 0 1440 100" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
          <path d="M0,50 C240,80 480,20 720,50 C960,80 1200,20 1440,50 L1440,100 L0,100 Z" fill="url(#gradient)" />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#064e3b" />
              <stop offset="50%" stopColor="#065f46" />
              <stop offset="100%" stopColor="#064e3b" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </section>
  );
};

export default PremiumHeroSection;

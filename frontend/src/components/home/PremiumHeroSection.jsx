import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Phone, Ban, Search, Wrench, CheckCircle2, Clock, MapPin, Target, Zap } from 'lucide-react';

const PremiumHeroSection = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const flipIntervalRef = useRef(null);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  // Auto-flip every 6 seconds
  useEffect(() => {
    const startFlipInterval = () => {
      flipIntervalRef.current = setInterval(() => {
        if (!isPaused) {
          setIsFlipped(prev => !prev);
        }
      }, 6000);
    };

    startFlipInterval();

    return () => {
      if (flipIntervalRef.current) {
        clearInterval(flipIntervalRef.current);
      }
    };
  }, [isPaused]);

  const handleMouseEnter = () => {
    setIsPaused(true);
  };

  const handleMouseLeave = () => {
    setIsPaused(false);
  };

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

  // Stats Cards Data
  const statsCards = [
    {
      id: 'calendar',
      icon: Calendar,
      metric: '365',
      unit: 'Days',
      label: 'Open Year-Round',
      gradient: 'from-orange-500 via-red-500 to-pink-500',
      iconBg: 'from-orange-400 to-red-500'
    },
    {
      id: 'speed',
      icon: Zap,
      metric: '2',
      unit: 'Hrs',
      label: 'Avg Response TAT',
      gradient: 'from-yellow-400 via-amber-500 to-orange-500',
      iconBg: 'from-yellow-400 to-amber-500'
    },
    {
      id: 'cities',
      icon: MapPin,
      metric: '11',
      unit: 'Cities',
      label: 'Pan-India Coverage',
      gradient: 'from-blue-500 via-indigo-500 to-purple-500',
      iconBg: 'from-blue-400 to-indigo-500'
    },
    {
      id: 'resolution',
      icon: Target,
      metric: '85',
      unit: '%',
      label: 'Onsite Resolution',
      gradient: 'from-green-500 via-emerald-500 to-teal-500',
      iconBg: 'from-green-400 to-emerald-500'
    }
  ];

  return (
    <section className="relative min-h-[90vh] overflow-hidden bg-gradient-to-br from-green-50 via-white to-emerald-50/30 flex items-center">
      {/* Enhanced Background Mesh - Battwheels Green Tones */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Primary green blob - top left */}
        <div className="absolute -top-20 -left-20 w-[700px] h-[700px] bg-gradient-to-br from-[#0FA958]/30 to-[#16B364]/20 rounded-full mix-blend-multiply filter blur-3xl animate-blob" />
        {/* Secondary emerald blob - top right */}
        <div className="absolute top-10 -right-20 w-[600px] h-[600px] bg-gradient-to-bl from-[#16B364]/25 to-emerald-200/30 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000" />
        {/* Tertiary green blob - bottom center */}
        <div className="absolute -bottom-40 left-1/4 w-[650px] h-[650px] bg-gradient-to-tr from-[#0FA958]/20 to-green-300/25 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000" />
        {/* Additional white blend */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-white/40 rounded-full filter blur-3xl" />
        {/* Extended bottom gradient for seamless flow */}
        <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[#0FA958]/10 via-white/50 to-transparent" />
      </div>
      
      {/* Top accent gradient */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#0FA958] via-[#16B364] to-[#0FA958]" />

      {/* Full-Width Container */}
      <div className="relative w-full">
        <div className="container mx-auto px-4 py-12 lg:py-16">
          {/* Two-Column Layout */}
          <div className={`grid lg:grid-cols-2 gap-8 lg:gap-16 items-center transform transition-all duration-1000 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}>
            
            {/* LEFT COLUMN - Text Content */}
            <div className="flex flex-col justify-center space-y-6 order-2 lg:order-1">
              {/* Main Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight" style={{ letterSpacing: '-0.5px' }}>
                EVs Don&apos;t Need Towing First.
              </h1>
              
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#0FA958] to-[#16B364] bg-clip-text text-transparent">
                They Need Diagnosis & Repair Onsite.
              </h2>

              <div className="h-px bg-gradient-to-r from-[#0FA958] via-[#16B364] to-transparent w-24" />

              {/* Supporting Text */}
              <p className="text-base lg:text-lg text-gray-700 leading-relaxed max-w-xl">
                India&apos;s first <span className="font-semibold text-gray-900">no-towing-first</span> EV service model. 
                We come to you — diagnosing and fixing your 2W, 3W, 4W and commercial EVs right where they stop. More uptime, lower costs.
              </p>

              {/* Premium CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Link to="/book-service?utm_source=hero&utm_medium=cta&utm_campaign=book_service" className="flex-1 sm:flex-initial">
                  <button className="relative w-full group overflow-hidden rounded-2xl bg-gradient-to-r from-orange-500 to-orange-600 p-0.5 transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/50 hover:-translate-y-1">
                    <div className="relative bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl px-8 py-4 text-white font-bold text-lg flex items-center justify-center gap-3">
                      {/* Shine effect */}
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                      <Calendar className="w-5 h-5" />
                      <span>Book EV Service Now</span>
                    </div>
                  </button>
                </Link>

                <Link to="/fleet-oem?utm_source=hero&utm_medium=cta&utm_campaign=fleet_enquiry" className="flex-1 sm:flex-initial">
                  <button className="relative w-full group overflow-hidden rounded-2xl bg-white border-2 border-orange-500 transition-all duration-300 hover:bg-orange-500 hover:shadow-xl hover:-translate-y-1">
                    <div className="px-8 py-4 font-semibold text-lg flex items-center justify-center gap-3 text-orange-600 group-hover:text-white transition-colors">
                      <Phone className="w-5 h-5 transition-transform group-hover:rotate-12" />
                      <span>Talk to Fleet Team</span>
                    </div>
                  </button>
                </Link>
              </div>
            </div>

            {/* RIGHT COLUMN - Flipping Stats Card */}
            <div 
              className="order-1 lg:order-2 perspective-1000"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              <div 
                className={`relative w-full transition-transform duration-700 ease-in-out transform-style-3d ${
                  isFlipped ? 'rotate-y-180' : ''
                }`}
                style={{
                  transformStyle: 'preserve-3d',
                  transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                  transition: 'transform 0.7s ease-in-out'
                }}
              >
                {/* FRONT SIDE - Stats Card */}
                <div 
                  className="relative w-full backface-hidden"
                  style={{ backfaceVisibility: 'hidden' }}
                >
                  <div className="flex flex-col justify-center space-y-6 bg-white/80 backdrop-blur-sm rounded-3xl p-6 lg:p-8 border border-green-100 shadow-xl">
                    
                    {/* The Real Road Side Assistance Header */}
                    <h3 className="text-center text-sm font-semibold text-gray-500 uppercase tracking-wider">
                      The Real Road Side Assistance
                    </h3>
                    
                    {/* Process Flow - 4 Steps */}
                    <div className="grid grid-cols-4 gap-2 sm:gap-4">
                      {processSteps.map((step, index) => {
                        const Icon = step.icon;
                        return (
                          <div
                            key={step.title}
                            className="flex flex-col items-center text-center group cursor-pointer"
                            style={{ animationDelay: `${index * 150}ms` }}
                          >
                            <div className={`w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-2xl bg-gradient-to-br ${step.gradient} p-0.5 mb-2 transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 shadow-lg`}>
                              <div className="w-full h-full rounded-2xl bg-white flex items-center justify-center">
                                <Icon className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-gray-700" />
                              </div>
                            </div>
                            <p className="text-xs font-semibold text-gray-800 leading-tight">{step.title}</p>
                            <p className="text-xs text-gray-500 hidden sm:block">{step.description}</p>
                          </div>
                        );
                      })}
                    </div>

                    {/* Connecting Line */}
                    <div className="relative h-1 bg-gradient-to-r from-red-500 via-blue-500 via-orange-500 to-green-500 rounded-full opacity-40" />

                    {/* Stats Cards - 2x2 Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {statsCards.map((stat) => {
                        const Icon = stat.icon;
                        return (
                          <div
                            key={stat.id}
                            className="group relative overflow-hidden rounded-xl p-3 sm:p-4 bg-gradient-to-br from-gray-50 to-white border border-gray-100 hover:border-green-200 transition-all duration-300 hover:shadow-lg"
                          >
                            {/* Content */}
                            <div className="relative z-10 flex items-start gap-3">
                              {/* Icon Container */}
                              <div className={`relative w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br ${stat.iconBg} p-0.5 shadow-md group-hover:shadow-lg transition-all duration-300 group-hover:scale-105 flex-shrink-0`}>
                                <div className="w-full h-full rounded-xl bg-white/90 flex items-center justify-center">
                                  <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-gray-700" />
                                </div>
                              </div>
                              
                              {/* Metric & Label */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-baseline gap-1">
                                  <span className={`text-xl sm:text-2xl font-bold bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent`}>
                                    {stat.metric}
                                  </span>
                                  <span className="text-xs sm:text-sm font-semibold text-gray-600">{stat.unit}</span>
                                </div>
                                <p className="text-xs font-medium text-gray-500 mt-0.5 truncate">{stat.label}</p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* BACK SIDE - Technician Image */}
                <div 
                  className="absolute top-0 left-0 w-full h-full backface-hidden rotate-y-180"
                  style={{ 
                    backfaceVisibility: 'hidden',
                    transform: 'rotateY(180deg)'
                  }}
                >
                  <div className="relative w-full h-full min-h-[400px] lg:min-h-[450px] rounded-3xl overflow-hidden shadow-xl border border-green-100">
                    {/* Technician Image */}
                    <img 
                      src="https://customer-assets.emergentagent.com/job_battwheels-ev/artifacts/dbsgrks6_Gemini_Generated_Image_ain6amain6amain6%20%281%29.png"
                      alt="Battwheels onsite EV roadside assistance - technician on scooter with service vehicle"
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                    
                    {/* Soft Green Overlay Gradient */}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0FA958]/30 via-transparent to-[#16B364]/10" />
                    
                    {/* Bottom Text Overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/60 to-transparent">
                      <p className="text-white font-bold text-lg">Onsite EV RSA</p>
                      <p className="text-white/80 text-sm">Real technicians. Real service. On your location.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom fade transition - extended for seamless flow */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white via-white/80 to-transparent" />
    </section>
  );
};

export default PremiumHeroSection;

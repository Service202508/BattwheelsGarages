import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Phone, Search, Wrench, Ban, CheckCircle2 } from 'lucide-react';

const PremiumHeroSection = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

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
    <section className="relative min-h-screen overflow-hidden bg-gradient-to-br from-green-50 via-emerald-50/50 to-green-50 flex items-center">
      {/* Background Mesh - Smooth Green Gradient */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-10 w-[500px] h-[500px] bg-green-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob" />
        <div className="absolute top-40 right-20 w-[600px] h-[600px] bg-emerald-300 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000" />
        <div className="absolute bottom-20 left-1/3 w-[550px] h-[550px] bg-green-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000" />
      </div>
      
      {/* Top accent gradient */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-emerald-400 to-green-500" />

      <div className="relative container mx-auto px-4 py-12 lg:py-20 w-full">
        {/* Full-Width Rectangular Hero Container */}
        <div className={`transform transition-all duration-1000 ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
        }`}>
          <div className="relative backdrop-blur-xl bg-white/90 rounded-3xl shadow-2xl border border-white/60 overflow-hidden">
            {/* Subtle Inner Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-green-500/10 to-emerald-500/10 blur-xl" />
            
            {/* Two-Column Layout */}
            <div className="relative z-10 grid lg:grid-cols-2 gap-8 lg:gap-12 p-8 lg:p-12">
              
              {/* LEFT COLUMN - Text Content */}
              <div className="flex flex-col justify-center space-y-6">
                {/* Main Headline */}
                <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-gray-900 leading-tight" style={{ letterSpacing: '-0.5px' }}>
                  EVs Don&apos;t Need Towing First.
                </h1>
                
                <h2 className="text-3xl lg:text-4xl xl:text-5xl font-bold bg-gradient-to-r from-green-600 to-emerald-500 bg-clip-text text-transparent">
                  They Need Diagnosis & Repair Onsite.
                </h2>

                <div className="h-px bg-gradient-to-r from-green-500 via-green-400 to-transparent w-24" />

                {/* Supporting Text */}
                <p className="text-lg text-gray-700 leading-relaxed">
                  India&apos;s first <span className="font-semibold text-gray-900">no-towing-first</span> EV service model. 
                  We come to you — diagnosing and fixing your 2W, 3W, 4W and commercial EVs right where they stop. More uptime, lower costs.
                </p>

                {/* Premium CTA Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 pt-4">
                  <Link to="/book-service" className="flex-1">
                    <button className="relative w-full group overflow-hidden rounded-2xl bg-gradient-to-r from-orange-500 to-orange-600 p-0.5 transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/50 hover:-translate-y-1">
                      <div className="relative bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl px-8 py-4 text-white font-bold text-lg flex items-center justify-center gap-3">
                        {/* Shine effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                        <Calendar className="w-5 h-5" />
                        <span>Book EV Service Now</span>
                      </div>
                    </button>
                  </Link>

                  <Link to="/fleet-oem" className="flex-1">
                    <button className="relative w-full group overflow-hidden rounded-2xl bg-white border-2 border-orange-500 transition-all duration-300 hover:bg-orange-500 hover:shadow-xl hover:-translate-y-1">
                      <div className="px-8 py-4 font-semibold text-lg flex items-center justify-center gap-3 text-orange-600 group-hover:text-white transition-colors">
                        <Phone className="w-5 h-5 transition-transform group-hover:rotate-12" />
                        <span>Talk to Fleet Team</span>
                      </div>
                    </button>
                  </Link>
                </div>
              </div>

              {/* RIGHT COLUMN - Battwheels Difference Card */}
              <div className="flex flex-col justify-center space-y-6 bg-gradient-to-br from-green-50/80 to-emerald-50/50 rounded-2xl p-6 lg:p-8 border border-green-100/80">
                
                {/* The Battwheels Difference Header */}
                <h3 className="text-center text-sm font-semibold text-gray-500 uppercase tracking-wider">
                  The Battwheels Difference
                </h3>
                
                {/* Process Flow - 4 Steps */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {processSteps.map((step, index) => {
                    const Icon = step.icon;
                    return (
                      <div
                        key={step.title}
                        className="flex flex-col items-center text-center group cursor-pointer"
                        style={{ animationDelay: `${index * 150}ms` }}
                      >
                        <div className={`w-14 h-14 lg:w-16 lg:h-16 rounded-2xl bg-gradient-to-br ${step.gradient} p-0.5 mb-2 transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 shadow-lg`}>
                          <div className="w-full h-full rounded-2xl bg-white flex items-center justify-center">
                            <Icon className="w-6 h-6 lg:w-7 lg:h-7 text-gray-700" />
                          </div>
                        </div>
                        <p className="text-xs font-semibold text-gray-800">{step.title}</p>
                        <p className="text-xs text-gray-500">{step.description}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Connecting Line */}
                <div className="relative h-1 bg-gradient-to-r from-red-500 via-blue-500 via-orange-500 to-green-500 rounded-full opacity-40" />

                {/* Stats Badges */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 p-4 border border-green-200/50">
                    <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent mb-1">85%</div>
                    <div className="h-1 w-3/4 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full mb-2" />
                    <div className="text-xs font-medium text-gray-700">Onsite Resolution</div>
                    <div className="text-xs text-gray-500">Rate</div>
                  </div>
                  <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-50 to-yellow-50 p-4 border border-orange-200/50">
                    <div className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-yellow-600 bg-clip-text text-transparent mb-1">105+</div>
                    <div className="h-1 w-3/4 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-full mb-2" />
                    <div className="text-xs font-medium text-gray-700">EV Models</div>
                    <div className="text-xs text-gray-500">Serviced</div>
                  </div>
                </div>

                {/* Trust Badges */}
                <div className="flex flex-wrap justify-center gap-3">
                  {[
                    { icon: '🗓️', text: 'Open 365 Days' },
                    { icon: '⚡', text: '2 hrs Avg TAT' },
                    { icon: '🇮🇳', text: '11 Cities' },
                    { icon: '✅', text: '85% Onsite Resolution' }
                  ].map((badge) => (
                    <div
                      key={badge.text}
                      className="flex items-center gap-2 px-3 py-2 bg-white/80 border border-gray-200 rounded-xl hover:shadow-md hover:-translate-y-1 transition-all duration-300 cursor-pointer"
                    >
                      <span className="text-lg">{badge.icon}</span>
                      <span className="text-xs font-medium text-gray-700">{badge.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Gradient Fade - Smooth transition to next section */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white/50 to-transparent" />
    </section>
  );
};

export default PremiumHeroSection;

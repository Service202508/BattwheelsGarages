import React, { useState, useEffect, useRef } from 'react';
import { 
  Rocket, 
  Target, 
  Settings, 
  Zap, 
  MapPin, 
  Cpu, 
  Award, 
  Wrench, 
  Users, 
  Handshake,
  TrendingUp,
  Shield,
  Clock,
  CheckCircle2
} from 'lucide-react';

const VisionMissionGoals = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('vision');
  const sectionRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => {
      if (sectionRef.current) {
        observer.unobserve(sectionRef.current);
      }
    };
  }, []);

  const tabs = [
    { id: 'vision', label: 'Vision', icon: Rocket },
    { id: 'mission', label: 'Mission', icon: Target },
    { id: 'goals', label: 'Goals', icon: Settings }
  ];

  const goals = [
    { icon: TrendingUp, text: '95%+ fleet uptime through rapid response and smart maintenance', color: 'from-emerald-500 to-green-600' },
    { icon: MapPin, text: '50+ cities nationwide with reliable service coverage', color: 'from-blue-500 to-indigo-600' },
    { icon: Cpu, text: 'Battwheels OS™-our AI platform powering diagnostics, parts management, and real-time service', color: 'from-purple-500 to-violet-600' },
    { icon: Award, text: 'Industry standards for EV service quality, parts, and technician certification', color: 'from-amber-500 to-orange-600' },
    { icon: Wrench, text: '90% onsite resolution-fix it where it breaks, minimal towing', color: 'from-rose-500 to-pink-600' },
    { icon: Users, text: "India's largest EV-trained workforce who understand motors, batteries, and controllers", color: 'from-cyan-500 to-teal-600' },
    { icon: Handshake, text: 'Strong OEM partnerships as the national aftersales backbone', color: 'from-green-500 to-emerald-600' },
  ];

  return (
    <section 
      ref={sectionRef}
      className="py-20 md:py-28 bg-gradient-to-b from-white via-green-50/30 to-white relative overflow-hidden"
    >
      {/* Background Decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-br from-[#0B8A44]/10 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-to-tl from-[#12B76A]/10 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header */}
        <div 
          className={`text-center mb-12 transform transition-all duration-700 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#0B8A44]/10 to-[#12B76A]/10 text-[#0B8A44] rounded-full text-sm font-semibold mb-4 border border-[#0B8A44]/20">
            <Shield className="w-4 h-4" />
            Who We Are
          </span>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Our Vision, Mission & Goals
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto text-base md:text-lg">
            Building the infrastructure that powers India&apos;s electric future
          </p>
        </div>

        {/* Tab Navigation */}
        <div 
          className={`flex justify-center mb-10 transform transition-all duration-700 delay-100 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <div className="inline-flex bg-gray-100 rounded-2xl p-1.5 gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-300 ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-[#0B8A44] to-[#12B76A] text-white shadow-lg shadow-green-500/30'
                      : 'text-gray-600 hover:text-[#0B8A44] hover:bg-white/50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Area */}
        <div 
          className={`max-w-5xl mx-auto transform transition-all duration-700 delay-200 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          {/* Vision Tab */}
          {activeTab === 'vision' && (
            <div className="animate-fadeIn">
              <div className="relative bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
                {/* Header with Icon */}
                <div className="bg-gradient-to-r from-[#0B8A44] to-[#12B76A] p-8 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                  <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
                  
                  <div className="relative z-10 flex items-center gap-6">
                    {/* Futuristic Icon Container */}
                    <div className="relative">
                      <div className="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30 shadow-2xl">
                        <Rocket className="w-10 h-10 md:w-12 md:h-12 text-white" />
                      </div>
                      {/* Orbiting dots */}
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse" />
                      <div className="absolute -bottom-1 -left-1 w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-300" />
                    </div>
                    
                    <div>
                      <span className="text-white/70 text-sm font-medium uppercase tracking-wider">Our Vision</span>
                      <h3 className="text-2xl md:text-3xl font-bold mt-1">Building Tomorrow&apos;s EV Infrastructure</h3>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-8 md:p-10 space-y-6">
                  <p className="text-lg md:text-xl text-gray-700 leading-relaxed font-medium">
                    We&apos;re building an India where EV breakdowns don&apos;t ruin your day. Where uptime isn&apos;t just promised-it&apos;s delivered.
                  </p>
                  
                  <p className="text-gray-600 leading-relaxed">
                    Right now, breakdowns mean towing, workshop delays, and days without your vehicle. We&apos;re changing that. We fix EVs where they stop. 2-wheelers, autos, cars, commercial fleets-all of them.
                  </p>
                  
                  <p className="text-gray-600 leading-relaxed">
                    Our goal? Become India&apos;s most trusted EV service partner. The ones fleet operators call first. The backbone OEMs rely on. We&apos;re building this city by city, making downtime a thing of the past through smart diagnostics, available parts, and technicians who actually show up fast.
                  </p>

                  <div className="pt-4 border-t border-gray-100">
                    <p className="text-[#0B8A44] font-semibold text-lg flex items-center gap-2">
                      <Zap className="w-5 h-5" />
                      Bottom line: Keeping India&apos;s electric revolution moving. Efficiently. Affordably. Without the headaches.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Mission Tab */}
          {activeTab === 'mission' && (
            <div className="animate-fadeIn">
              <div className="relative bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
                {/* Header with Icon */}
                <div className="bg-gradient-to-r from-[#005E4C] to-[#0B8A44] p-8 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                  <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
                  
                  <div className="relative z-10 flex items-center gap-6">
                    {/* Futuristic Icon Container */}
                    <div className="relative">
                      <div className="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30 shadow-2xl">
                        <Target className="w-10 h-10 md:w-12 md:h-12 text-white" />
                      </div>
                      {/* Targeting rings */}
                      <div className="absolute inset-0 border-2 border-white/20 rounded-2xl animate-ping" style={{ animationDuration: '2s' }} />
                    </div>
                    
                    <div>
                      <span className="text-white/70 text-sm font-medium uppercase tracking-wider">Our Mission</span>
                      <h3 className="text-2xl md:text-3xl font-bold mt-1">Fix Fast. Fix Right. Come to You.</h3>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-8 md:p-10 space-y-6">
                  <p className="text-lg md:text-xl text-gray-700 leading-relaxed font-medium">
                    Fix your EV fast, fix it right, don&apos;t make you come to us.
                  </p>
                  
                  <p className="text-gray-600 leading-relaxed">
                    We solve 80-90% of problems on the spot. Our technicians show up with skills, tools, and parts to handle it right there. No surprise pricing. No shady upselling. No &quot;keep it for a week&quot; excuses.
                  </p>
                  
                  <p className="text-gray-600 leading-relaxed">
                    We&apos;re raising India&apos;s EV service standards by training real experts, using AI diagnostics, and ensuring quality parts everywhere. Through our garages, mobile units, and field techs, we&apos;re building a system that actually works.
                  </p>

                  {/* Mission Highlights */}
                  <div className="grid md:grid-cols-3 gap-4 pt-4">
                    {[
                      { icon: Clock, label: 'Rapid Response', desc: 'Same-day service' },
                      { icon: CheckCircle2, label: 'Quality Parts', desc: 'Genuine components' },
                      { icon: Shield, label: 'No Hidden Costs', desc: 'Transparent pricing' }
                    ].map((item, idx) => (
                      <div key={idx} className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#0B8A44] to-[#12B76A] flex items-center justify-center flex-shrink-0">
                          <item.icon className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900 text-sm">{item.label}</p>
                          <p className="text-gray-500 text-xs">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-4 border-t border-gray-100">
                    <p className="text-[#005E4C] font-semibold text-lg flex items-center gap-2">
                      <Zap className="w-5 h-5" />
                      Simple mission: Keep India&apos;s EVs moving. Always.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Goals Tab */}
          {activeTab === 'goals' && (
            <div className="animate-fadeIn">
              <div className="relative bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
                {/* Header with Icon */}
                <div className="bg-gradient-to-r from-orange-500 to-amber-500 p-8 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                  <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
                  
                  <div className="relative z-10 flex items-center gap-6">
                    {/* Futuristic Icon Container */}
                    <div className="relative">
                      <div className="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30 shadow-2xl">
                        <Settings className="w-10 h-10 md:w-12 md:h-12 text-white animate-spin-slow" />
                      </div>
                      {/* Gear teeth effect */}
                      <div className="absolute -top-2 left-1/2 w-2 h-2 bg-yellow-300 rounded-full" />
                      <div className="absolute -bottom-2 left-1/2 w-2 h-2 bg-yellow-300 rounded-full" />
                      <div className="absolute top-1/2 -left-2 w-2 h-2 bg-yellow-300 rounded-full" />
                      <div className="absolute top-1/2 -right-2 w-2 h-2 bg-yellow-300 rounded-full" />
                    </div>
                    
                    <div>
                      <span className="text-white/70 text-sm font-medium uppercase tracking-wider">Our Goals</span>
                      <h3 className="text-2xl md:text-3xl font-bold mt-1">Scaling India&apos;s EV Future</h3>
                    </div>
                  </div>
                </div>

                {/* Goals Grid */}
                <div className="p-8 md:p-10">
                  <div className="grid md:grid-cols-2 gap-4">
                    {goals.map((goal, index) => {
                      const Icon = goal.icon;
                      return (
                        <div 
                          key={index}
                          className="group flex items-start gap-4 p-5 rounded-2xl bg-gray-50 hover:bg-white hover:shadow-lg border border-transparent hover:border-gray-200 transition-all duration-300"
                        >
                          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${goal.color} flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                            <Icon className="w-6 h-6 text-white" />
                          </div>
                          <p className="text-gray-700 font-medium leading-relaxed pt-1">{goal.text}</p>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-100">
                    <p className="text-orange-600 font-semibold text-lg flex items-center gap-2">
                      <TrendingUp className="w-5 h-5" />
                      We&apos;re building infrastructure that scales with India&apos;s EV future. Not catching up-staying ahead.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CSS for animations */}
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.4s ease-out forwards;
        }
        
        .animate-spin-slow {
          animation: spin 8s linear infinite;
        }
        
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </section>
  );
};

export default VisionMissionGoals;

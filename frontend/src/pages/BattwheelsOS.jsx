import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import SEO from '../components/common/SEO';
import { Button } from '../components/ui/button';
import { 
  Monitor, 
  Smartphone, 
  BarChart3, 
  Zap, 
  Bell, 
  Link as LinkIcon, 
  CheckCircle,
  Brain,
  AlertTriangle,
  Search,
  FileText,
  Database,
  Share2,
  Clock,
  TrendingUp,
  Shield,
  Users,
  Repeat,
  Target,
  ArrowRight
} from 'lucide-react';

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
      description: 'OBD/diagnostic integration for controllers, BMS, motors, and other EV systems with GaragePROEV-grade diagnostics.'
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
      <SEO 
        title="Battwheels OS™ - Garage Management Platform"
        description="Battwheels OS™ is our comprehensive garage management platform. Digital job cards, EV diagnostics, technician apps, and analytics for modern EV service centers."
        url="/battwheels-os"
      />
      {/* Rotating Gears Background */}
      <GearBackground variant="battwheels-os" />
      
      <Header />
      <main>
        {/* Hero with MacBook Dashboard */}
        <section className="relative min-h-[90vh] flex items-center overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
          {/* Subtle Background Pattern */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute top-20 left-20 w-96 h-96 bg-green-500 rounded-full blur-3xl" />
            <div className="absolute bottom-20 right-20 w-80 h-80 bg-emerald-500 rounded-full blur-3xl" />
          </div>
          
          {/* Content */}
          <div className="relative z-10 container mx-auto px-4 py-20">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              {/* Left Content */}
              <div className="order-2 lg:order-1">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-5 py-2.5 rounded-full text-sm font-bold mb-8 shadow-lg shadow-green-500/30">
                  <Monitor className="w-4 h-4" />
                  Tech Platform
                </div>
                
                {/* Main Heading */}
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white mb-6 leading-tight">
                  Battwheels OS<sup className="text-xs align-super relative -top-1">™</sup>
                  <span className="block text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400 mt-2">
                    The EV Aftersales Command Center
                  </span>
                </h1>
                
                {/* Description */}
                <p className="text-lg sm:text-xl text-gray-300 leading-relaxed mb-10 max-w-xl">
                  GaragePROEV-grade diagnostics + field-force management + fleet dashboards in one <span className="text-green-400 font-semibold">EV-native platform</span>.
                </p>
                
                {/* Feature Pills */}
                <div className="flex flex-wrap gap-3 mb-10">
                  <span className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm text-white border border-white/20">
                    🔧 Digital Job Cards
                  </span>
                  <span className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm text-white border border-white/20">
                    📊 Fleet Analytics
                  </span>
                  <span className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm text-white border border-white/20">
                    🔌 EV Diagnostics
                  </span>
                  <span className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm text-white border border-white/20">
                    📱 Technician App
                  </span>
                </div>
                
                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row gap-4">
                  <Button 
                    size="lg"
                    className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold px-8 py-6 text-lg rounded-xl shadow-xl shadow-green-500/30 hover:shadow-green-500/50 transition-all hover:-translate-y-1"
                    onClick={() => navigate('/fleet-oem')}
                  >
                    <Zap className="w-5 h-5 mr-2" />
                    Schedule a Demo
                  </Button>
                  <Button 
                    size="lg"
                    variant="outline"
                    className="border-2 border-white/30 text-white hover:bg-white/10 font-semibold px-8 py-6 text-lg rounded-xl backdrop-blur-sm"
                    onClick={() => navigate('/contact')}
                  >
                    Learn More
                  </Button>
                </div>
              </div>
              
              {/* Right - MacBook Frame with Dashboard */}
              <div className="order-1 lg:order-2 flex justify-center lg:justify-end">
                <div className="relative">
                  {/* Glow Effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-green-500/30 to-emerald-500/30 blur-3xl scale-110" />
                  
                  {/* MacBook Frame */}
                  <div className="relative z-10">
                    {/* MacBook Body */}
                    <div className="bg-gradient-to-b from-gray-700 to-gray-800 rounded-t-2xl p-2 shadow-2xl max-w-2xl">
                      {/* Screen Bezel */}
                      <div className="bg-black rounded-lg p-1">
                        {/* Camera Notch */}
                        <div className="flex justify-center mb-1">
                          <div className="w-2 h-2 rounded-full bg-gray-700" />
                        </div>
                        {/* Screen Content */}
                        <div className="rounded-md overflow-hidden">
                          <img 
                            src="/assets/battwheels-os-dashboard-screen.png" 
                            alt="Battwheels OS Dashboard" 
                            className="w-full h-auto"
                          />
                        </div>
                      </div>
                    </div>
                    {/* MacBook Base/Hinge */}
                    <div className="bg-gradient-to-b from-gray-600 to-gray-700 h-4 rounded-b-lg mx-8 shadow-xl" />
                    {/* MacBook Bottom */}
                    <div className="bg-gradient-to-b from-gray-700 to-gray-800 h-2 rounded-b-xl mx-4" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Bottom Gradient Fade */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent" />
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

        {/* EV Failure Intelligence Section */}
        <section className="py-20 bg-gradient-to-b from-gray-900 to-gray-800 relative overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute top-0 left-0 w-96 h-96 bg-green-500 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-500 rounded-full blur-3xl" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            {/* Section Header */}
            <div className="text-center mb-16">
              {/* Patent & Differentiator Badges */}
              <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-400 px-4 py-2 rounded-full text-sm font-semibold">
                  <Brain className="w-4 h-4" />
                  Core Differentiator
                </div>
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 border border-blue-400/40 text-blue-400 px-4 py-2 rounded-full text-sm font-bold">
                  <Shield className="w-4 h-4" />
                  Patented Technology
                </div>
              </div>
              
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-white mb-4">
                EV Failure Intelligence<sup className="text-blue-400 text-lg ml-1">®</sup>
              </h2>
              <p className="text-xl md:text-2xl text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400 font-bold mb-6">
                One EV Failure Solved. Thousands Prevented.
              </p>
              
              {/* Patent Notice */}
              <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-2 mb-8">
                <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
                </svg>
                <span className="text-blue-300 text-sm">Protected under Indian Patent Law • Proprietary to Battwheels Services Pvt. Ltd.</span>
              </div>
              
              <p className="text-lg text-gray-400 max-w-3xl mx-auto leading-relaxed">
                Every undocumented EV failure in the field is analyzed, converted into structured repair intelligence, 
                and shared across our technician network through Battwheels OS — making the entire system smarter with every repair.
              </p>
            </div>

            {/* Short Explanation */}
            <div className="max-w-4xl mx-auto mb-16">
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 md:p-10">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-green-400" />
                  </div>
                  How Failure Intelligence Works
                </h3>
                <p className="text-gray-300 leading-relaxed mb-6">
                  When a new or undocumented EV issue occurs in the field, our expert team performs root cause analysis 
                  and documents the solution as a structured <span className="text-green-400 font-semibold">"Failure Card"</span>. 
                  These cards are stored inside Battwheels OS, where AI-assisted matching automatically suggests solutions 
                  for similar future cases — enabling faster, more accurate repairs across the network.
                </p>
                <div className="flex flex-wrap gap-3">
                  <span className="px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-full text-sm text-green-400">
                    Root Cause Analysis
                  </span>
                  <span className="px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-full text-sm text-green-400">
                    Structured Knowledge Base
                  </span>
                  <span className="px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-full text-sm text-green-400">
                    AI-Assisted Matching
                  </span>
                  <span className="px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-full text-sm text-green-400">
                    Continuous Learning
                  </span>
                </div>
              </div>
            </div>

            {/* Visual Workflow */}
            <div className="mb-20">
              <h3 className="text-2xl font-bold text-white text-center mb-12">
                The Intelligence Pipeline
              </h3>
              <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-4 max-w-6xl mx-auto">
                {[
                  { icon: AlertTriangle, title: 'New EV Failure', subtitle: 'Detected in field', color: 'from-red-500 to-orange-500' },
                  { icon: Search, title: 'Root Cause', subtitle: 'Expert analysis', color: 'from-orange-500 to-amber-500' },
                  { icon: FileText, title: 'Failure Card', subtitle: 'Documented', color: 'from-amber-500 to-yellow-500' },
                  { icon: Database, title: 'Stored in OS', subtitle: 'Battwheels OS', color: 'from-yellow-500 to-green-500' },
                  { icon: Share2, title: 'Network Sync', subtitle: 'All technicians', color: 'from-green-500 to-emerald-500' },
                  { icon: Zap, title: 'Faster Repairs', subtitle: 'Future cases', color: 'from-emerald-500 to-teal-500' },
                ].map((step, index) => {
                  const Icon = step.icon;
                  return (
                    <div key={index} className="relative group">
                      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-center hover:bg-white/10 transition-all hover:-translate-y-1">
                        <div className={`w-14 h-14 mx-auto mb-4 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center shadow-lg`}>
                          <Icon className="w-7 h-7 text-white" />
                        </div>
                        <h4 className="text-white font-semibold text-sm mb-1">{step.title}</h4>
                        <p className="text-gray-500 text-xs">{step.subtitle}</p>
                      </div>
                      {index < 5 && (
                        <div className="hidden lg:block absolute top-1/2 -right-2 transform -translate-y-1/2 z-10">
                          <ArrowRight className="w-4 h-4 text-gray-600" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Benefits Grid */}
            <div className="mb-16">
              <h3 className="text-2xl font-bold text-white text-center mb-12">
                Why Failure Intelligence Matters
              </h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
                {[
                  { icon: Clock, title: 'Faster First-Time Fix', description: 'Reduce diagnostic time with instant access to proven solutions for similar failures.' },
                  { icon: TrendingUp, title: 'Reduced Fleet Downtime', description: 'Get vehicles back on the road faster with pre-validated repair procedures.' },
                  { icon: Shield, title: 'Consistent Service Quality', description: 'Every technician benefits from the collective knowledge of the entire network.' },
                  { icon: Repeat, title: 'Continuous Learning', description: 'The system improves with every repair, creating compounding intelligence.' },
                  { icon: Users, title: 'Reduced Dependency', description: 'Scale service capacity without relying on individual technician experience.' },
                  { icon: Brain, title: 'Scalable Intelligence', description: 'Turn field experience into enterprise-grade service knowledge.' },
                ].map((benefit, index) => {
                  const Icon = benefit.icon;
                  return (
                    <div key={index} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:border-green-500/30 transition-all">
                      <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center mb-4">
                        <Icon className="w-6 h-6 text-green-400" />
                      </div>
                      <h4 className="text-white font-semibold mb-2">{benefit.title}</h4>
                      <p className="text-gray-400 text-sm leading-relaxed">{benefit.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Technical Credibility */}
            <div className="max-w-3xl mx-auto text-center mb-12">
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-6">
                <p className="text-gray-300 text-sm leading-relaxed">
                  <span className="text-green-400 font-semibold">Technical Foundation:</span> Battwheels OS uses structured failure knowledge, 
                  AI-assisted diagnosis, and continuous feedback loops to improve repair accuracy over time — 
                  creating a self-improving system that gets smarter with every service interaction.
                </p>
              </div>
            </div>

            {/* CTA */}
            <div className="text-center">
              <Button 
                size="lg"
                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold px-10 py-6 text-lg rounded-xl shadow-xl shadow-green-500/30 hover:shadow-green-500/50 transition-all hover:-translate-y-1"
                onClick={() => navigate('/fleet-oem')}
              >
                <Brain className="w-5 h-5 mr-2" />
                Experience Intelligence-Driven EV Service
              </Button>
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-20 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Who Benefits from Battwheels OS™?</h2>
              
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
              Schedule a personalized demo of Battwheels OS™ and see how we can optimize your fleet management and service operations.
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
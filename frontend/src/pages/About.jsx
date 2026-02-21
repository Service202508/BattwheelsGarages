import React from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import VisionMissionGoals from '../components/home/VisionMissionGoals';
import SEO from '../components/common/SEO';
import { 
  Wrench, 
  Zap, 
  Users, 
  Building, 
  TrendingUp, 
  MapPin,
  Clock,
  Shield,
  CheckCircle2,
  Leaf,
  Award,
  Cpu,
  Phone,
  HeartHandshake
} from 'lucide-react';
import { Link } from 'react-router-dom';

const About = () => {
  const stats = [
    { icon: Wrench, value: '10,000+', label: 'EVs Serviced', color: 'from-green-500 to-emerald-600' },
    { icon: TrendingUp, value: '85%', label: 'Onsite Resolution', color: 'from-blue-500 to-indigo-600' },
    { icon: Users, value: '5,000+', label: 'Happy Customers', color: 'from-purple-500 to-violet-600' },
    { icon: MapPin, value: '11', label: 'Cities Covered', color: 'from-orange-500 to-amber-600' },
  ];

  const differentiators = [
    {
      icon: Zap,
      title: 'EV-Only Focus',
      description: 'We don\'t do ICE vehicles. Our entire team, training, tools, and parts inventory are 100% focused on electric vehicles - 2W, 3W, 4W, and commercial.',
      color: 'from-yellow-500 to-orange-500'
    },
    {
      icon: Clock,
      title: 'Onsite First Approach',
      description: '85% of EV issues can be fixed where they break down. Our technicians arrive with diagnostic tools, spare parts, and expertise to resolve problems on the spot.',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: Cpu,
      title: 'Tech-Driven Operations',
      description: 'Battwheels OS™ powers everything - from AI diagnostics to real-time job tracking, parts management, and fleet health dashboards for enterprise clients.',
      color: 'from-purple-500 to-violet-500'
    },
    {
      icon: Award,
      title: 'Certified EV Technicians',
      description: 'Our engineers undergo rigorous training on motors, controllers, BMS, and battery systems. They understand EVs at the component level.',
      color: 'from-blue-500 to-indigo-500'
    },
    {
      icon: Shield,
      title: 'Transparent Pricing',
      description: 'No surprise bills, no hidden charges, no unnecessary upselling. We diagnose first, explain clearly, and fix only what needs fixing.',
      color: 'from-teal-500 to-cyan-500'
    },
    {
      icon: HeartHandshake,
      title: 'Fleet & OEM Partnerships',
      description: 'We\'re the aftersales backbone for fleet operators and OEM partners. Guaranteed SLAs, dedicated account managers, and nationwide coverage.',
      color: 'from-rose-500 to-pink-500'
    }
  ];

  return (
    <div className="min-h-screen relative">
      <SEO 
        title="About Us - India's First No-Towing EV Service"
        description="Learn about Battwheels Garages - India's #1 EV service partner. 10,000+ EVs serviced, 85% onsite resolution rate. Expert technicians for 2W, 3W, and 4W EVs."
        url="/about"
      />
      {/* Rotating Gears Background */}
      <GearBackground variant="default" />
      
      <Header />
      <main>
        {/* Hero Section */}
        <section className="py-20 md:py-28 bg-gradient-to-br from-green-50 via-white to-emerald-50/30 relative overflow-hidden">
          {/* Background Decorations */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-[#0B8A44]/10 to-transparent rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-80 h-80 bg-gradient-to-tr from-[#12B76A]/10 to-transparent rounded-full blur-3xl" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#0B8A44]/10 to-[#12B76A]/10 text-[#0B8A44] rounded-full text-sm font-semibold mb-6 border border-[#0B8A44]/20">
                <Building className="w-4 h-4" />
                About Us
              </span>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                India&apos;s First <span className="bg-gradient-to-r from-[#0B8A44] to-[#12B76A] bg-clip-text text-transparent">EV-Only</span> Onsite Service Company
              </h1>
              
              <p className="text-xl md:text-2xl text-gray-600 leading-relaxed mb-8">
                We built Battwheels to solve one simple problem: <strong className="text-gray-900">EVs don&apos;t need towing first - they need diagnosis and repair on the spot.</strong>
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a 
                  href="https://cloud-finance-suite.preview.emergentagent.com/submit-ticket"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-[#0B8A44] to-[#12B76A] text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-green-500/30 hover:-translate-y-0.5 transition-all duration-300"
                >
                  <Zap className="w-5 h-5" />
                  Book EV Service
                </a>
                <Link 
                  to="/contact"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-[#0B8A44] text-[#0B8A44] font-semibold rounded-xl hover:bg-[#0B8A44] hover:text-white transition-all duration-300"
                >
                  <Phone className="w-5 h-5" />
                  Contact Us
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Our Story Section */}
        <section className="py-16 md:py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-5xl mx-auto">
              <div className="grid lg:grid-cols-2 gap-12 items-center mb-16">
                <div>
                  <span className="inline-block px-3 py-1 bg-[#0B8A44]/10 text-[#0B8A44] rounded-full text-sm font-semibold mb-4">
                    Our Story
                  </span>
                  <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                    Born from a Gap in India&apos;s EV Ecosystem
                  </h2>
                  <div className="space-y-4 text-gray-600 leading-relaxed">
                    <p>
                      India&apos;s EV revolution is accelerating - but after-sales infrastructure hasn&apos;t kept pace. Traditional garages don&apos;t understand EVs. OEM networks are limited. And when your EV breaks down, you&apos;re stuck waiting for tow trucks and workshop queues.
                    </p>
                    <p>
                      <strong className="text-gray-900">Battwheels Garages was founded in 2024</strong> to change this. We&apos;re building India&apos;s largest EV-focused service network - with onsite repair as our core philosophy.
                    </p>
                    <p>
                      From Ather scooters to Tata Nexon EVs, from delivery fleets to corporate cars - we service them all. Our technicians come to you, diagnose on-spot, and fix 85% of issues without towing.
                    </p>
                  </div>
                </div>
                
                <div className="relative">
                  <div className="bg-gradient-to-br from-[#0B8A44]/10 to-[#12B76A]/10 rounded-3xl p-8 border border-[#0B8A44]/20">
                    <img 
                      src="https://customer-assets.emergentagent.com/job_battwheels-ev/artifacts/dbsgrks6_Gemini_Generated_Image_ain6amain6amain6%20%281%29.png"
                      alt="Battwheels onsite EV service"
                      className="rounded-2xl shadow-xl w-full"
                    />
                  </div>
                  {/* Floating Stats Card */}
                  <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-xl p-4 border border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-[#0B8A44] to-[#12B76A] rounded-lg flex items-center justify-center">
                        <CheckCircle2 className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-gray-900">85%</p>
                        <p className="text-sm text-gray-500">Fixed Onsite</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-16">
                {stats.map((stat, index) => {
                  const Icon = stat.icon;
                  return (
                    <div 
                      key={index}
                      className="text-center p-6 bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-100 hover:shadow-lg hover:border-[#12B76A]/30 transition-all duration-300"
                    >
                      <div className={`w-14 h-14 bg-gradient-to-br ${stat.color} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
                        <Icon className="w-7 h-7 text-white" />
                      </div>
                      <div className="text-3xl font-bold bg-gradient-to-r from-[#0B8A44] to-[#12B76A] bg-clip-text text-transparent mb-1">
                        {stat.value}
                      </div>
                      <div className="text-sm text-gray-600 font-medium">{stat.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* Vision, Mission & Goals Section */}
        <VisionMissionGoals />

        {/* What Makes Us Different */}
        <section className="py-16 md:py-20 bg-gradient-to-b from-white to-gray-50">
          <div className="container mx-auto px-4">
            <div className="max-w-5xl mx-auto">
              <div className="text-center mb-12">
                <span className="inline-block px-3 py-1 bg-[#0B8A44]/10 text-[#0B8A44] rounded-full text-sm font-semibold mb-4">
                  Our Difference
                </span>
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                  What Makes Battwheels Different
                </h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  We&apos;re not just another garage. We&apos;re building the infrastructure India&apos;s EV revolution deserves.
                </p>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {differentiators.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <div 
                      key={index}
                      className="group bg-white rounded-2xl p-6 border border-gray-100 hover:border-[#12B76A]/30 hover:shadow-xl transition-all duration-300"
                    >
                      <div className={`w-14 h-14 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center mb-5 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="w-7 h-7 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{item.title}</h3>
                      <p className="text-gray-600 leading-relaxed">{item.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* Sustainability Section */}
        <section className="py-16 md:py-20 bg-gradient-to-br from-[#005E4C] via-[#0B8A44] to-[#12B76A] text-white relative overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 left-0 w-64 h-64 bg-white rounded-full -translate-x-1/2 -translate-y-1/2" />
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full translate-x-1/3 translate-y-1/3" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 backdrop-blur-sm rounded-2xl mb-6 border border-white/30">
                <Leaf className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                Sustainability at Our Core
              </h2>
              <p className="text-xl text-green-50 leading-relaxed mb-8">
                Every EV we service is a step toward a cleaner India. We&apos;re not just fixing vehicles - we&apos;re keeping the electric revolution moving. Our commitment extends beyond service: we use eco-friendly practices, minimize waste, and train technicians to handle EV components responsibly.
              </p>
              <div className="flex flex-wrap justify-center gap-6">
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Eco-Friendly Practices</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Zero Emission Focus</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Responsible Disposal</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 md:py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Ready to Experience the Battwheels Difference?
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Join thousands of EV owners and fleet operators who trust us with their vehicles.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link 
                  to="/book-service"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-orange-500/30 hover:-translate-y-0.5 transition-all duration-300"
                >
                  <Zap className="w-5 h-5" />
                  Book Your Service Now
                </Link>
                <Link 
                  to="/fleet-oem"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:border-[#0B8A44] hover:text-[#0B8A44] transition-all duration-300"
                >
                  <Building className="w-5 h-5" />
                  Fleet & OEM Enquiry
                </Link>
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

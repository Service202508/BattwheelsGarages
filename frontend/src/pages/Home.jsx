import React, { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { Button } from '../components/ui/button';
import { 
  Calendar, Phone, Ban, Search, Wrench, CheckCircle2, MapPin, Target, Zap,
  Battery, Settings, Truck, Shield, Clock, Award, ChevronDown, ChevronRight,
  Star, Play, ArrowRight, Bike, Car
} from 'lucide-react';

// Compact Hero Section
const CompactHero = () => {
  return (
    <section className="relative py-12 md:py-16 bg-gradient-to-br from-green-50 via-white to-emerald-50/30 overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute -top-20 -left-20 w-96 h-96 bg-green-200/30 rounded-full blur-3xl" />
        <div className="absolute top-10 -right-20 w-80 h-80 bg-emerald-200/30 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="grid lg:grid-cols-2 gap-8 items-center">
          {/* Left - Content */}
          <div className="space-y-5">
            <div className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              <Zap className="w-4 h-4 mr-1" />
              India's #1 EV Service Partner
            </div>
            
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 leading-tight">
              EVs Don't Need Towing.
              <span className="block text-green-600">They Need Onsite Repair.</span>
            </h1>
            
            <p className="text-base md:text-lg text-gray-600 max-w-lg">
              85% issues resolved on-the-spot. No towing. No workshop visits. 
              Service for 2W, 3W, 4W & commercial EVs.
            </p>

            {/* Quick Stats */}
            <div className="flex flex-wrap gap-4 py-2">
              {[
                { value: '2 Hrs', label: 'Response' },
                { value: '85%', label: 'Onsite Fix' },
                { value: '11', label: 'Cities' },
                { value: '365', label: 'Days Open' }
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-xl font-bold text-green-600">{stat.value}</div>
                  <div className="text-xs text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Link to="/book-service">
                <Button size="lg" className="w-full sm:w-auto bg-orange-500 hover:bg-orange-600 text-white font-bold shadow-lg">
                  <Calendar className="w-5 h-5 mr-2" />
                  Book EV Service
                </Button>
              </Link>
              <Link to="/fleet-oem">
                <Button size="lg" variant="outline" className="w-full sm:w-auto border-2 border-green-600 text-green-600 hover:bg-green-50 font-semibold">
                  <Phone className="w-5 h-5 mr-2" />
                  Fleet Enquiry
                </Button>
              </Link>
            </div>
          </div>

          {/* Right - Process Flow Card */}
          <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 text-center">
              How It Works
            </h3>
            <div className="grid grid-cols-4 gap-3">
              {[
                { icon: Ban, title: 'No Towing', color: 'from-red-500 to-pink-500' },
                { icon: Search, title: 'Diagnose', color: 'from-blue-500 to-cyan-500' },
                { icon: Wrench, title: 'Repair', color: 'from-orange-500 to-yellow-500' },
                { icon: CheckCircle2, title: 'Done!', color: 'from-green-500 to-emerald-500' }
              ].map((step, idx) => (
                <div key={step.title} className="text-center">
                  <div className={`w-12 h-12 mx-auto rounded-xl bg-gradient-to-br ${step.color} p-0.5 mb-2`}>
                    <div className="w-full h-full rounded-xl bg-white flex items-center justify-center">
                      <step.icon className="w-5 h-5 text-gray-700" />
                    </div>
                  </div>
                  <p className="text-xs font-semibold text-gray-700">{step.title}</p>
                </div>
              ))}
            </div>
            <div className="h-1 bg-gradient-to-r from-red-500 via-blue-500 via-orange-500 to-green-500 rounded-full mt-4 opacity-50" />
            
            {/* Technician Image */}
            <div className="mt-4 rounded-xl overflow-hidden">
              <img 
                src="https://customer-assets.emergentagent.com/job_battwheels-ev/artifacts/dbsgrks6_Gemini_Generated_Image_ain6amain6amain6%20%281%29.png"
                alt="Battwheels onsite service"
                className="w-full h-32 object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// Vehicle Types - Compact Cards
const VehicleTypesCompact = () => {
  const vehicles = [
    { id: '2w', name: '2-Wheeler', icon: Bike, models: '50+', color: 'bg-blue-500' },
    { id: '3w', name: '3-Wheeler', icon: Truck, models: '24+', color: 'bg-purple-500' },
    { id: '4w', name: '4-Wheeler', icon: Car, models: '6+', color: 'bg-green-500' },
    { id: 'commercial', name: 'Commercial', icon: Truck, models: '7+', color: 'bg-orange-500' }
  ];

  return (
    <section className="py-10 bg-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900">We Service All EV Types</h2>
          <p className="text-gray-600 mt-1">105+ models across all categories</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          {vehicles.map((v) => (
            <div key={v.id} className="bg-gray-50 rounded-xl p-4 text-center hover:shadow-lg transition-shadow cursor-pointer group">
              <div className={`w-12 h-12 ${v.color} rounded-xl mx-auto mb-3 flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <v.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900">{v.name}</h3>
              <p className="text-sm text-green-600 font-medium">{v.models} Models</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Services - Tabbed Accordion
const ServicesSection = () => {
  const [activeTab, setActiveTab] = useState('repair');
  const [openAccordion, setOpenAccordion] = useState(null);

  const serviceTabs = {
    repair: {
      title: 'Repair Services',
      services: [
        { name: 'Motor & Controller Repair', desc: 'Diagnosis, rewinding, controller replacement' },
        { name: 'Battery & BMS Service', desc: 'Health check, cell balancing, replacement' },
        { name: 'Brake & Suspension', desc: 'Disc pads, drum shoes, shock absorbers' },
        { name: 'Electrical Systems', desc: 'Wiring, lights, dashboard repairs' }
      ]
    },
    maintenance: {
      title: 'Maintenance',
      services: [
        { name: 'Periodic Service', desc: 'Complete checkup, lubrication, adjustments' },
        { name: 'Preventive Care', desc: 'Scheduled maintenance to prevent breakdowns' },
        { name: 'Software Updates', desc: 'OTA updates, ECU programming' },
        { name: 'Tire & Wheel Care', desc: 'Rotation, balancing, puncture repair' }
      ]
    },
    emergency: {
      title: 'Emergency',
      services: [
        { name: 'Roadside Assistance', desc: '24/7 onsite help within 2 hours' },
        { name: 'Towing (If Needed)', desc: 'Safe transport to nearest service center' },
        { name: 'Jump Start', desc: 'Battery boost for immediate mobility' },
        { name: 'Onsite Diagnosis', desc: 'Identify issue without moving vehicle' }
      ]
    }
  };

  return (
    <section className="py-10 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Our Services</h2>
          <p className="text-gray-600 mt-1">Comprehensive EV care, delivered onsite</p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex bg-white rounded-xl p-1 shadow-sm">
            {Object.keys(serviceTabs).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab 
                    ? 'bg-green-600 text-white shadow-md' 
                    : 'text-gray-600 hover:text-green-600'
                }`}
              >
                {serviceTabs[tab].title}
              </button>
            ))}
          </div>
        </div>

        {/* Accordion Services */}
        <div className="max-w-2xl mx-auto space-y-2">
          {serviceTabs[activeTab].services.map((service, idx) => (
            <div 
              key={service.name}
              className="bg-white rounded-xl overflow-hidden shadow-sm"
            >
              <button
                onClick={() => setOpenAccordion(openAccordion === idx ? null : idx)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-gray-900">{service.name}</span>
                </div>
                <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${openAccordion === idx ? 'rotate-180' : ''}`} />
              </button>
              {openAccordion === idx && (
                <div className="px-4 pb-3 pl-12 text-gray-600 text-sm">
                  {service.desc}
                  <Link to="/book-service" className="ml-2 text-green-600 font-medium hover:underline">
                    Book Now →
                  </Link>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="text-center mt-6">
          <Link to="/services">
            <Button variant="outline" className="border-green-600 text-green-600 hover:bg-green-50">
              View All Services
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
};

// Why Choose Us - Compact Grid
const WhyChooseCompact = () => {
  const benefits = [
    { icon: Ban, title: 'No Towing First', desc: 'We come to your location' },
    { icon: Clock, title: '2-Hour Response', desc: 'Quick turnaround time' },
    { icon: Target, title: '85% Onsite Fix', desc: 'Most issues resolved on spot' },
    { icon: Shield, title: 'OEM Certified', desc: 'Trained technicians' },
    { icon: MapPin, title: '11 Cities', desc: 'Pan-India coverage' },
    { icon: Award, title: '4.8★ Rating', desc: 'Trusted by thousands' }
  ];

  return (
    <section className="py-10 bg-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Why Choose Battwheels</h2>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 max-w-5xl mx-auto">
          {benefits.map((b) => (
            <div key={b.title} className="text-center p-4 rounded-xl hover:bg-green-50 transition-colors">
              <div className="w-12 h-12 bg-green-100 rounded-xl mx-auto mb-2 flex items-center justify-center">
                <b.icon className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 text-sm">{b.title}</h3>
              <p className="text-xs text-gray-500 mt-1">{b.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Industries - Compact Slider
const IndustriesCompact = () => {
  const industries = [
    { name: 'Fleet Operators', icon: Truck },
    { name: 'E-Commerce', icon: Truck },
    { name: 'EV OEMs', icon: Settings },
    { name: 'Individual Owners', icon: Car }
  ];

  return (
    <section className="py-10 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Industries We Serve</h2>
        </div>
        
        <div className="flex flex-wrap justify-center gap-4">
          {industries.map((ind) => (
            <Link 
              key={ind.name}
              to="/industries"
              className="flex items-center gap-2 px-5 py-3 bg-white rounded-full shadow-sm hover:shadow-md transition-shadow"
            >
              <ind.icon className="w-5 h-5 text-green-600" />
              <span className="font-medium text-gray-700">{ind.name}</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};

// Brands Section - Compact
const BrandsCompact = () => {
  const brands = ['Ather', 'Ola Electric', 'TVS iQube', 'Bajaj Chetak', 'Hero Electric', 'Okinawa', 'Ampere', 'Revolt'];

  return (
    <section className="py-8 bg-white border-y border-gray-100">
      <div className="container mx-auto px-4">
        <p className="text-center text-sm text-gray-500 mb-4">Trusted by leading EV brands</p>
        <div className="flex flex-wrap justify-center items-center gap-6 md:gap-10">
          {brands.map((brand) => (
            <span key={brand} className="text-gray-400 font-semibold text-sm hover:text-green-600 transition-colors">
              {brand}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
};

// Testimonials - Compact Carousel
const TestimonialsCompact = () => {
  const testimonials = [
    { name: 'Rajesh Kumar', role: 'Fleet Manager, BluSmart', text: 'Battwheels reduced our vehicle downtime by 40%. Their onsite service is a game-changer.', rating: 5 },
    { name: 'Priya Sharma', role: 'Ather 450X Owner', text: 'Got my scooter fixed at my doorstep in 2 hours. Excellent service!', rating: 5 },
    { name: 'Amit Patel', role: 'Logistics Head, Delhivery', text: 'Managing 200+ EVs is easy with Battwheels subscription. Highly recommended.', rating: 5 }
  ];

  return (
    <section className="py-10 bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900">What Our Customers Say</h2>
        </div>
        
        <div className="grid md:grid-cols-3 gap-4 max-w-5xl mx-auto">
          {testimonials.map((t) => (
            <div key={t.name} className="bg-white rounded-xl p-5 shadow-sm">
              <div className="flex mb-2">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-600 text-sm mb-3">"{t.text}"</p>
              <div>
                <p className="font-semibold text-gray-900 text-sm">{t.name}</p>
                <p className="text-xs text-gray-500">{t.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// CTA Section - Compact
const CTACompact = () => {
  return (
    <section className="py-12 bg-gradient-to-r from-green-600 to-emerald-600">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
          Ready to Experience Hassle-Free EV Service?
        </h2>
        <p className="text-green-100 mb-6 max-w-xl mx-auto">
          Join 10,000+ EV owners and fleet operators who trust Battwheels
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/book-service">
            <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white font-bold shadow-lg">
              <Calendar className="w-5 h-5 mr-2" />
              Book Service Now
            </Button>
          </Link>
          <Link to="/plans">
            <Button size="lg" variant="outline" className="border-2 border-white text-white hover:bg-white/10 font-semibold">
              Explore Plans
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
};

// Main Home Component
const Home = () => {
  return (
    <div className="min-h-screen">
      <Helmet>
        <title>Battwheels Garages | India's #1 EV Onsite Service & Repair</title>
        <meta name="description" content="India's first no-towing-first EV service. Onsite diagnosis & repair for 2W, 3W, 4W EVs. 85% issues resolved on field. Open 365 days." />
        <link rel="canonical" href="https://battwheelsgarages.in" />
        <meta property="og:title" content="Battwheels Garages | India's #1 EV Onsite Service" />
        <meta property="og:description" content="India's first no-towing-first EV service model. Onsite diagnosis and repair for all EV types." />
        <meta property="og:type" content="website" />
      </Helmet>
      
      <Header />
      <main>
        <CompactHero />
        <VehicleTypesCompact />
        <ServicesSection />
        <WhyChooseCompact />
        <BrandsCompact />
        <IndustriesCompact />
        <TestimonialsCompact />
        <CTACompact />
      </main>
      <Footer />
    </div>
  );
};

export default Home;

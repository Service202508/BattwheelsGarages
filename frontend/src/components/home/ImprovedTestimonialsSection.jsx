import React, { useState, useEffect } from 'react';
import { Quote, Truck, Users, Building2, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { testimonialsApi } from '../../utils/api';

const ImprovedTestimonialsSection = () => {
  const [activeCategory, setActiveCategory] = useState('all');
  const [currentPage, setCurrentPage] = useState(0);
  const [testimonials, setTestimonials] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fallback hardcoded testimonials
  const fallbackTestimonials = [
    {
      id: 1,
      name: "Rohit Malhotra",
      role: "Fleet Operations Manager",
      company: "Last-Mile Delivery (EV 2W)",
      category: "2w-fleet",
      quote: "Downtime kills fleet economics. Battwheels' onsite EV repair model helped us reduce vehicle idle time significantly. Their technicians understand EV systems deeply and fix issues without unnecessary towing.",
      avatar: "RM"
    },
    {
      id: 2,
      name: "Ankit Verma",
      role: "City Head",
      company: "Electric 3W Passenger Fleet",
      category: "3w-fleet",
      quote: "Earlier, even small EV issues meant half-day downtime. Battwheels' team resolves most problems onsite for our e-rickshaw fleet. It is a huge operational win for us.",
      avatar: "AV"
    },
    {
      id: 3,
      name: "Pradeep Singh",
      role: "Operations Lead",
      company: "Hyperlocal Logistics Company",
      category: "logistics",
      quote: "Battwheels Garages is not just a service vendor; they behave like an uptime partner. Fast diagnosis, honest recommendations, and clear communication at every step.",
      avatar: "PS"
    },
    {
      id: 4,
      name: "Suresh Kumar",
      role: "Fleet Owner",
      company: "Commercial Electric Cargo Vehicles",
      category: "commercial",
      quote: "Their understanding of motors, controllers, and wiring issues is far better than local garages. Battwheels has helped extend the life of our vehicles and reduce repeat failures.",
      avatar: "SK"
    },
    {
      id: 5,
      name: "Neha Aggarwal",
      role: "Program Manager",
      company: "EV Leasing Company",
      category: "leasing",
      quote: "We needed a reliable after-sales partner for multiple EV brands. Battwheels' EV-only focus and structured processes make them easy to work with at scale.",
      avatar: "NA"
    },
    {
      id: 6,
      name: "Amit Yadav",
      role: "Regional Operations Manager",
      company: "E-commerce EV Fleet",
      category: "2w-fleet",
      quote: "What stands out is speed. Most breakdowns are handled onsite within hours. Battwheels understands fleet pressure and works with that urgency.",
      avatar: "AY"
    },
    {
      id: 7,
      name: "Rakesh Gupta",
      role: "Independent EV Fleet Operator",
      company: "2W & 3W Mixed Fleet",
      category: "3w-fleet",
      quote: "Unlike traditional garages, Battwheels does not experiment. They diagnose accurately and fix only what is needed. That transparency has saved us a lot of money.",
      avatar: "RG"
    },
    {
      id: 8,
      name: "Kunal Sharma",
      role: "Maintenance Head",
      company: "Urban Mobility Startup",
      category: "startup",
      quote: "EV after-sales needs technical depth, not generic mechanics. Battwheels' EV-trained team delivers consistent quality across different vehicle types.",
      avatar: "KS"
    },
    {
      id: 9,
      name: "Mohit Saxena",
      role: "City Ops Head",
      company: "Battery Swapping Partner Network",
      category: "battery",
      quote: "Their coordination with our swapping operations has been seamless. Onsite repairs mean batteries and vehicles are back in circulation faster.",
      avatar: "MS"
    },
    {
      id: 10,
      name: "Deepak Rawat",
      role: "Fleet Supervisor",
      company: "Electric 4W Corporate Transport",
      category: "4w-fleet",
      quote: "Structured service, proper documentation, and reliable technicians — Battwheels brings discipline to EV maintenance, which is rare in this space.",
      avatar: "DR"
    },
    {
      id: 11,
      name: "Vikram Chauhan",
      role: "Operations Director",
      company: "EV OEM Channel Partner",
      category: "oem",
      quote: "Battwheels understands OEM expectations around safety, diagnostic accuracy, and reporting. Their processes align well with professional EV after-sales standards.",
      avatar: "VC"
    },
    {
      id: 12,
      name: "Manoj Tiwari",
      role: "Owner",
      company: "E-Rickshaw Aggregation Business",
      category: "3w-fleet",
      quote: "Earlier, vehicles would sit idle for days. With Battwheels' onsite repairs, most issues are sorted the same day. That directly increased our daily earnings.",
      avatar: "MT"
    },
    {
      id: 13,
      name: "Shubham Jain",
      role: "Supply Chain Manager",
      company: "Quick Commerce EV Fleet",
      category: "logistics",
      quote: "Battwheels helped us stabilize our EV operations during peak demand. Their field team availability and response time are a big advantage.",
      avatar: "SJ"
    },
    {
      id: 14,
      name: "Pankaj Mehta",
      role: "Head – Asset Management",
      company: "EV Leasing Firm",
      category: "leasing",
      quote: "Preventive maintenance and early fault detection from Battwheels reduced long-term repair costs. Their approach is data-driven and practical.",
      avatar: "PM"
    },
    {
      id: 15,
      name: "Rahul Chandra",
      role: "Senior Manager",
      company: "Urban Electric Mobility Program",
      category: "startup",
      quote: "Battwheels is building what the EV ecosystem actually needs — reliable, onsite after-sales. Their model is clearly designed for scale and real-world operations.",
      avatar: "RC"
    }
  ];

  useEffect(() => {
    fetchTestimonials();
  }, [activeCategory]);

  const fetchTestimonials = async () => {
    try {
      setLoading(true);
      const data = await testimonialsApi.getAll(activeCategory);
      
      if (data.testimonials && data.testimonials.length > 0) {
        // Map API data to component format
        const mappedTestimonials = data.testimonials.map(t => ({
          id: t.id,
          name: t.name,
          role: t.role,
          company: t.company,
          category: t.category,
          quote: t.quote,
          avatar: t.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'BW'
        }));
        setTestimonials(mappedTestimonials);
      } else {
        // Use fallback data
        const filtered = activeCategory === 'all' 
          ? fallbackTestimonials 
          : fallbackTestimonials.filter(t => t.category === activeCategory);
        setTestimonials(filtered);
      }
    } catch (err) {
      console.error('Error fetching testimonials:', err);
      // Use fallback data on error
      const filtered = activeCategory === 'all' 
        ? fallbackTestimonials 
        : fallbackTestimonials.filter(t => t.category === activeCategory);
      setTestimonials(filtered);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { id: 'all', label: 'All Testimonials', icon: Users, count: testimonials.length },
    { id: '2w-fleet', label: '2W Fleet', icon: Truck, count: testimonials.filter(t => t.category === '2w-fleet').length },
    { id: '3w-fleet', label: '3W Fleet', icon: Truck, count: testimonials.filter(t => t.category === '3w-fleet').length },
    { id: '4w-fleet', label: '4W Fleet', icon: Truck, count: testimonials.filter(t => t.category === '4w-fleet').length },
    { id: 'logistics', label: 'Logistics', icon: Building2, count: testimonials.filter(t => t.category === 'logistics').length },
    { id: 'leasing', label: 'Leasing', icon: Building2, count: testimonials.filter(t => t.category === 'leasing').length }
  ];

  const filteredTestimonials = testimonials;

  const itemsPerPage = 6;
  const totalPages = Math.ceil(filteredTestimonials.length / itemsPerPage);
  const startIndex = currentPage * itemsPerPage;
  const visibleTestimonials = filteredTestimonials.slice(startIndex, startIndex + itemsPerPage);

  const handleCategoryChange = (category) => {
    setActiveCategory(category);
    setCurrentPage(0);
  };

  const nextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <section className="relative py-20 bg-gradient-to-b from-white via-green-50/30 to-white overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-20 left-10 w-64 h-64 bg-green-400 rounded-full filter blur-3xl" />
        <div className="absolute bottom-20 right-10 w-64 h-64 bg-emerald-400 rounded-full filter blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-2 bg-green-100 rounded-full mb-4">
            <Quote className="w-6 h-6 text-green-600" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Trusted by Fleet Operators Across India
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Real feedback from fleet managers, OEM partners, and operators who trust Battwheels for EV uptime
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <button
                key={category.id}
                onClick={() => handleCategoryChange(category.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all duration-300 ${
                  activeCategory === category.id
                    ? 'bg-green-600 text-white shadow-lg scale-105'
                    : 'bg-white text-gray-700 hover:bg-green-50 border border-gray-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{category.label}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  activeCategory === category.id ? 'bg-white/20' : 'bg-gray-100'
                }`}>
                  {category.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto mb-8">
          {visibleTestimonials.map((testimonial, index) => (
            <div
              key={testimonial.id}
              className="group relative"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Card */}
              <div className="relative h-full bg-white rounded-2xl p-6 shadow-md hover:shadow-2xl transition-all duration-500 border border-gray-100 hover:border-green-200 hover:-translate-y-2">
                {/* Gradient Accent */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                
                {/* Quote Icon */}
                <div className="absolute -top-3 -left-3 bg-gradient-to-br from-green-500 to-emerald-600 p-3 rounded-xl shadow-lg transform group-hover:scale-110 transition-transform">
                  <Quote className="w-5 h-5 text-white" />
                </div>

                {/* Content */}
                <div className="pt-4">
                  <p className="text-gray-700 mb-6 leading-relaxed line-clamp-5">
                    "{testimonial.quote}"
                  </p>

                  {/* Author Info */}
                  <div className="flex items-center gap-4 pt-4 border-t border-gray-100">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white font-bold shadow-md">
                        {testimonial.avatar}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 truncate">{testimonial.name}</h4>
                      <p className="text-sm text-gray-600 truncate">{testimonial.role}</p>
                      <p className="text-xs text-green-600 font-medium truncate">{testimonial.company}</p>
                    </div>
                  </div>
                </div>

                {/* Hover Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={prevPage}
              disabled={currentPage === 0}
              className={`p-2 rounded-lg transition-all ${
                currentPage === 0
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-green-50 shadow-md hover:shadow-lg'
              }`}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="flex gap-2">
              {[...Array(totalPages)].map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentPage(i)}
                  className={`w-10 h-10 rounded-lg font-medium transition-all ${
                    currentPage === i
                      ? 'bg-green-600 text-white shadow-lg scale-110'
                      : 'bg-white text-gray-700 hover:bg-green-50'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>

            <button
              onClick={nextPage}
              disabled={currentPage === totalPages - 1}
              className={`p-2 rounded-lg transition-all ${
                currentPage === totalPages - 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-green-50 shadow-md hover:shadow-lg'
              }`}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Stats Bar */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
          {[
            { label: 'Fleet Operators Served', value: '70+' },
            { label: 'Cities Covered', value: '11+' },
            { label: 'Uptime Guaranteed', value: '95%' },
            { label: 'Customer Satisfaction', value: '4.8/5' }
          ].map((stat) => (
            <div key={stat.label} className="text-center p-6 bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl font-bold text-green-600 mb-2">{stat.value}</div>
              <div className="text-sm text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ImprovedTestimonialsSection;

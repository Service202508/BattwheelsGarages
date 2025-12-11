import React, { useEffect, useState, useRef } from 'react';
import { CheckCircle2 } from 'lucide-react';

const VehicleTypesSection = () => {
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef(null);

  const vehicleTypes = [
    {
      id: '2w',
      name: '2-Wheeler EVs',
      category: 'Scooters & Bikes',
      count: '50+ Models',
      image: '/assets/ev-categories/ev-2w-new.png',
      emoji: '🛵'
    },
    {
      id: '3w',
      name: '3-Wheeler EVs',
      category: 'Auto Rickshaws',
      count: '14+ Models',
      image: '/assets/ev-categories/ev-3w-new.png',
      emoji: '🛺'
    },
    {
      id: '4w',
      name: '4-Wheeler EVs',
      category: 'Cars & SUVs',
      count: '6+ Models',
      image: '/assets/ev-categories/ev-4w-new.png',
      emoji: '🚗'
    },
    {
      id: 'commercial',
      name: 'Commercial EVs',
      category: 'Trucks & Vans',
      count: '7+ Models',
      image: '/assets/ev-categories/ev-commercial-new.png',
      emoji: '🚚'
    }
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.2 }
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

  return (
    <section 
      ref={sectionRef}
      className="relative py-16 md:py-24 bg-white overflow-hidden"
    >
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-green-50/30 to-white" />
      
      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header with Animation */}
        <div 
          className={`text-center mb-12 transform transition-all duration-1000 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            We Service All EV Types
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From 2-wheelers to commercial fleets, expert onsite service for every electric vehicle
          </p>
        </div>

        {/* Horizontal Scrollable Cards Container */}
        <div className="relative">
          {/* Desktop: Grid Layout with Animations */}
          <div className="hidden md:grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
            {vehicleTypes.map((vehicle, index) => (
              <div
                key={vehicle.id}
                className={`transform transition-all duration-700 ${
                  isVisible 
                    ? 'translate-y-0 opacity-100' 
                    : 'translate-y-20 opacity-0'
                }`}
                style={{ transitionDelay: `${index * 150}ms` }}
              >
                <VehicleCard vehicle={vehicle} />
              </div>
            ))}
          </div>

          {/* Mobile/Tablet: Horizontal Scroller */}
          <div className="md:hidden overflow-x-auto pb-4 -mx-4 px-4 scrollbar-hide">
            <div className="flex space-x-4 min-w-max">
              {vehicleTypes.map((vehicle, index) => (
                <div
                  key={vehicle.id}
                  className={`w-72 transform transition-all duration-700 ${
                    isVisible 
                      ? 'translate-x-0 opacity-100' 
                      : 'translate-x-10 opacity-0'
                  }`}
                  style={{ transitionDelay: `${index * 150}ms` }}
                >
                  <VehicleCard vehicle={vehicle} />
                </div>
              ))}
            </div>
          </div>

          {/* Scroll Indicator for Mobile */}
          <div className="md:hidden flex justify-center mt-4 space-x-2">
            {vehicleTypes.map((_, index) => (
              <div
                key={index}
                className="w-2 h-2 rounded-full bg-gray-300"
              />
            ))}
          </div>
        </div>

        {/* Stats Banner */}
        <div 
          className={`mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto transform transition-all duration-1000 delay-500 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          {[
            { label: 'EV Models Serviced', value: '105+' },
            { label: 'Cities Covered', value: '11' },
            { label: 'Onsite Resolution', value: '85%' },
            { label: 'Customer Rating', value: '4.8/5' }
          ].map((stat) => (
            <div 
              key={stat.label} 
              className="text-center p-6 bg-gradient-to-br from-green-50 to-white rounded-xl border border-green-100 hover:shadow-lg transition-shadow"
            >
              <div className="text-3xl font-bold text-green-600 mb-2">{stat.value}</div>
              <div className="text-sm text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom wave transition */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg 
          className="w-full h-16 md:h-24" 
          viewBox="0 0 1440 100" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg" 
          preserveAspectRatio="none"
        >
          <path 
            d="M0,50 C360,80 720,20 1080,50 C1260,65 1350,35 1440,50 L1440,100 L0,100 Z" 
            fill="#f0fdf4" 
          />
        </svg>
      </div>
    </section>
  );
};

// Vehicle Card Component
const VehicleCard = ({ vehicle }) => {
  return (
    <div className="group relative overflow-hidden rounded-2xl bg-white shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer h-full">
      {/* Vehicle Image */}
      <div className="relative h-52 overflow-hidden bg-gradient-to-br from-gray-50 via-white to-gray-100">
        <img
          src={vehicle.image}
          alt={vehicle.name}
          className="w-full h-full object-contain transform group-hover:scale-105 transition-transform duration-700 p-2"
          loading="lazy"
        />
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
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
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-green-500/20 to-emerald-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
    </div>
  );
};

export default VehicleTypesSection;

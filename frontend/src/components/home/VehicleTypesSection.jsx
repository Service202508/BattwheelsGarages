import React, { useEffect, useState, useRef } from 'react';
import { CheckCircle2, ChevronLeft, ChevronRight } from 'lucide-react';

const VehicleTypesSection = () => {
  const [isVisible, setIsVisible] = useState(false);
  const scrollContainerRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
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
      id: '3w-loader',
      name: '3-Wheeler EVs Loader',
      category: 'Loader Cargos',
      count: '10+ Models',
      image: '/assets/ev-categories/ev-3w-loader.png',
      emoji: '📦'
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

  const checkScrollButtons = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    checkScrollButtons();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkScrollButtons);
      window.addEventListener('resize', checkScrollButtons);
      return () => {
        container.removeEventListener('scroll', checkScrollButtons);
        window.removeEventListener('resize', checkScrollButtons);
      };
    }
  }, []);

  const scroll = (direction) => {
    if (scrollContainerRef.current) {
      const scrollAmount = 320; // Card width + gap
      scrollContainerRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <section 
      ref={sectionRef}
      className="relative py-8 md:py-12 bg-gradient-to-b from-green-50/30 via-white to-green-50/50 overflow-hidden"
    >
      {/* Top gradient fade from hero */}
      <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-white via-white/80 to-transparent pointer-events-none" />
      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header - Compact for immediate below hero */}
        <div 
          className={`text-center mb-6 transform transition-all duration-700 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            We Service All EV Types
          </h2>
          <p className="text-base text-gray-600 max-w-xl mx-auto">
            From 2-wheelers to commercial fleets, expert onsite service for every electric vehicle
          </p>
        </div>

        {/* Horizontal Scroller Container */}
        <div className="relative">
          {/* Navigation Arrows - Desktop */}
          <button
            onClick={() => scroll('left')}
            className={`hidden md:flex absolute -left-4 lg:-left-6 top-1/2 -translate-y-1/2 z-10 w-12 h-12 rounded-full bg-white shadow-lg border border-gray-200 items-center justify-center transition-all duration-300 ${
              canScrollLeft 
                ? 'opacity-100 hover:bg-green-50 hover:border-green-300 hover:shadow-xl' 
                : 'opacity-0 pointer-events-none'
            }`}
            aria-label="Scroll left"
          >
            <ChevronLeft className="w-6 h-6 text-gray-700" />
          </button>

          <button
            onClick={() => scroll('right')}
            className={`hidden md:flex absolute -right-4 lg:-right-6 top-1/2 -translate-y-1/2 z-10 w-12 h-12 rounded-full bg-white shadow-lg border border-gray-200 items-center justify-center transition-all duration-300 ${
              canScrollRight 
                ? 'opacity-100 hover:bg-green-50 hover:border-green-300 hover:shadow-xl' 
                : 'opacity-0 pointer-events-none'
            }`}
            aria-label="Scroll right"
          >
            <ChevronRight className="w-6 h-6 text-gray-700" />
          </button>

          {/* Scrollable Cards Container */}
          <div 
            ref={scrollContainerRef}
            className="flex gap-4 md:gap-6 overflow-x-auto pb-4 scrollbar-hide scroll-smooth px-1"
            style={{ 
              scrollSnapType: 'x mandatory',
              WebkitOverflowScrolling: 'touch'
            }}
          >
            {vehicleTypes.map((vehicle, index) => (
              <div
                key={vehicle.id}
                className={`flex-shrink-0 w-[280px] md:w-[300px] transform transition-all duration-700 ${
                  isVisible 
                    ? 'translate-x-0 opacity-100' 
                    : 'translate-x-10 opacity-0'
                }`}
                style={{ 
                  transitionDelay: `${index * 100}ms`,
                  scrollSnapAlign: 'start'
                }}
              >
                <VehicleCard vehicle={vehicle} />
              </div>
            ))}
            
            {/* Extra padding element for better scroll behavior */}
            <div className="flex-shrink-0 w-1" aria-hidden="true" />
          </div>

          {/* Scroll Indicator Dots - Mobile */}
          <div className="flex md:hidden justify-center mt-3 space-x-2">
            {vehicleTypes.map((_, index) => (
              <div
                key={index}
                className="w-2 h-2 rounded-full bg-[#12B76A]/50 transition-colors"
              />
            ))}
          </div>
        </div>

        {/* Compact Stats Banner */}
        <div 
          className={`mt-8 flex flex-wrap justify-center gap-4 md:gap-8 max-w-4xl mx-auto transform transition-all duration-1000 delay-300 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          {[
            { label: 'EV Models', value: '105+' },
            { label: 'Cities', value: '11' },
            { label: 'Onsite Resolution', value: '85%' },
            { label: 'Rating', value: '4.8/5' }
          ].map((stat) => (
            <div 
              key={stat.label} 
              className="text-center px-4 py-3 bg-white rounded-xl border border-[#12B76A]/20 shadow-sm hover:shadow-md hover:border-[#12B76A]/40 transition-all"
            >
              <div className="text-xl md:text-2xl font-bold bg-gradient-to-r from-[#0B8A44] to-[#12B76A] bg-clip-text text-transparent">{stat.value}</div>
              <div className="text-xs md:text-sm text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Vehicle Card Component
const VehicleCard = ({ vehicle }) => {
  return (
    <div className="group relative overflow-hidden rounded-2xl bg-white shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer h-full border border-gray-100">
      {/* Vehicle Image */}
      <div className="relative h-44 overflow-hidden bg-gradient-to-br from-gray-50 via-white to-gray-100">
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
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h4 className="text-base font-bold text-gray-900 mb-0.5">{vehicle.name}</h4>
            <p className="text-sm text-gray-600">{vehicle.category}</p>
          </div>
          <span className="text-2xl">{vehicle.emoji}</span>
        </div>
        
        {/* Stats Chip */}
        <div className="inline-flex items-center px-3 py-1 rounded-full bg-[#0B8A44]/10 text-[#0B8A44] text-xs font-semibold border border-[#0B8A44]/20">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          {vehicle.count}
        </div>
      </div>

      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#0B8A44]/10 to-[#12B76A]/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
    </div>
  );
};

export default VehicleTypesSection;

import React, { useState, useEffect, useRef } from 'react';
import { ExternalLink } from 'lucide-react';

// Brand data with all 15 EV brands
const brandsData = [
  {
    name: 'Ather Energy',
    slug: 'ather-energy',
    homepage: 'https://www.atherenergy.com',
    segment: '2W',
    logo: '/assets/brands/ather-energy-logo.svg',
    logoWhite: '/assets/brands/ather-energy-logo-white.svg',
    alt: 'Ather Energy logo — Battwheels Garages served brand'
  },
  {
    name: 'Ola Electric',
    slug: 'ola-electric',
    homepage: 'https://www.olaelectric.com',
    segment: '2W',
    logo: '/assets/brands/ola-electric-logo.svg',
    logoWhite: '/assets/brands/ola-electric-logo-white.svg',
    alt: 'Ola Electric logo — Battwheels Garages served brand'
  },
  {
    name: 'TVS Motor',
    slug: 'tvs',
    homepage: 'https://www.tvsmotor.com',
    segment: '2W',
    logo: '/assets/brands/tvs-logo.svg',
    logoWhite: '/assets/brands/tvs-logo-white.svg',
    alt: 'TVS Motor logo — Battwheels Garages served brand'
  },
  {
    name: 'Bajaj Auto',
    slug: 'bajaj',
    homepage: 'https://www.bajajauto.com',
    segment: '2W/3W',
    logo: '/assets/brands/bajaj-logo.svg',
    logoWhite: '/assets/brands/bajaj-logo-white.svg',
    alt: 'Bajaj Auto logo — Battwheels Garages served brand'
  },
  {
    name: 'Hero Electric',
    slug: 'hero-electric',
    homepage: 'https://www.heroelectric.in',
    segment: '2W',
    logo: '/assets/brands/hero-electric-logo.svg',
    logoWhite: '/assets/brands/hero-electric-logo-white.svg',
    alt: 'Hero Electric logo — Battwheels Garages served brand'
  },
  {
    name: 'Revolt Motors',
    slug: 'revolt',
    homepage: 'https://www.revoltmotors.com',
    segment: '2W',
    logo: '/assets/brands/revolt-logo.svg',
    logoWhite: '/assets/brands/revolt-logo-white.svg',
    alt: 'Revolt Motors logo — Battwheels Garages served brand'
  },
  {
    name: 'Simple Energy',
    slug: 'simple-energy',
    homepage: 'https://www.simpleenergy.in',
    segment: '2W',
    logo: '/assets/brands/simple-energy-logo.svg',
    logoWhite: '/assets/brands/simple-energy-logo-white.svg',
    alt: 'Simple Energy logo — Battwheels Garages served brand'
  },
  {
    name: 'Bounce',
    slug: 'bounce',
    homepage: 'https://www.bounceshare.com',
    segment: '2W',
    logo: '/assets/brands/bounce-logo.svg',
    logoWhite: '/assets/brands/bounce-logo-white.svg',
    alt: 'Bounce logo — Battwheels Garages served brand'
  },
  {
    name: 'Chetak',
    slug: 'chetak',
    homepage: 'https://www.chetak.com',
    segment: '2W',
    logo: '/assets/brands/chetak-logo.svg',
    logoWhite: '/assets/brands/chetak-logo-white.svg',
    alt: 'Chetak Electric logo — Battwheels Garages served brand'
  },
  {
    name: 'Piaggio',
    slug: 'piaggio',
    homepage: 'https://www.piaggio.com',
    segment: '3W',
    logo: '/assets/brands/piaggio-logo.svg',
    logoWhite: '/assets/brands/piaggio-logo-white.svg',
    alt: 'Piaggio logo — Battwheels Garages served brand'
  },
  {
    name: 'Mahindra Electric',
    slug: 'mahindra',
    homepage: 'https://www.mahindraelectric.com',
    segment: '4W/3W',
    logo: '/assets/brands/mahindra-logo.svg',
    logoWhite: '/assets/brands/mahindra-logo-white.svg',
    alt: 'Mahindra Electric logo — Battwheels Garages served brand'
  },
  {
    name: 'Tata Motors',
    slug: 'tata',
    homepage: 'https://www.tatamotors.com',
    segment: '4W',
    logo: '/assets/brands/tata-logo.svg',
    logoWhite: '/assets/brands/tata-logo-white.svg',
    alt: 'Tata Motors logo — Battwheels Garages served brand'
  },
  {
    name: 'MG Motor',
    slug: 'mg',
    homepage: 'https://www.mgmotor.co.in',
    segment: '4W',
    logo: '/assets/brands/mg-logo.svg',
    logoWhite: '/assets/brands/mg-logo-white.svg',
    alt: 'MG Motor logo — Battwheels Garages served brand'
  },
  {
    name: 'BYD',
    slug: 'byd',
    homepage: 'https://www.byd.com',
    segment: '4W/Commercial',
    logo: '/assets/brands/byd-logo.svg',
    logoWhite: '/assets/brands/byd-logo-white.svg',
    alt: 'BYD logo — Battwheels Garages served brand'
  },
  {
    name: 'Euler Motors',
    slug: 'euler-motors',
    homepage: 'https://www.eulermotors.com',
    segment: 'Commercial',
    logo: '/assets/brands/euler-motors-logo.svg',
    logoWhite: '/assets/brands/euler-motors-logo-white.svg',
    alt: 'Euler Motors logo — Battwheels Garages served brand'
  }
];

const BrandsSection = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [activeSegment, setActiveSegment] = useState('all');
  const sectionRef = useRef(null);

  const segments = [
    { id: 'all', label: 'All Brands', count: brandsData.length },
    { id: '2W', label: '2-Wheeler', count: brandsData.filter(b => b.segment.includes('2W')).length },
    { id: '3W', label: '3-Wheeler', count: brandsData.filter(b => b.segment.includes('3W')).length },
    { id: '4W', label: '4-Wheeler', count: brandsData.filter(b => b.segment.includes('4W')).length },
    { id: 'Commercial', label: 'Commercial', count: brandsData.filter(b => b.segment.includes('Commercial')).length }
  ];

  const filteredBrands = activeSegment === 'all' 
    ? brandsData 
    : brandsData.filter(b => b.segment.includes(activeSegment));

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

  return (
    <section 
      ref={sectionRef}
      className="py-16 md:py-20 bg-gradient-to-b from-white to-gray-50"
    >
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div 
          className={`text-center mb-10 transform transition-all duration-700 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <span className="inline-block px-4 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-semibold mb-4">
            Trusted Partners
          </span>
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
            We Serve These EV Brands
          </h2>
          <p className="text-base text-gray-600 max-w-2xl mx-auto">
            Expert service for all major electric vehicle brands across 2W, 3W, 4W segments
          </p>
        </div>

        {/* Segment Filter Tabs */}
        <div 
          className={`flex flex-wrap justify-center gap-2 mb-10 transform transition-all duration-700 delay-100 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          {segments.map((seg) => (
            <button
              key={seg.id}
              onClick={() => setActiveSegment(seg.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                activeSegment === seg.id
                  ? 'bg-green-600 text-white shadow-lg shadow-green-500/30'
                  : 'bg-white text-gray-700 border border-gray-200 hover:border-green-300 hover:text-green-600'
              }`}
            >
              {seg.label}
              <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-xs ${
                activeSegment === seg.id 
                  ? 'bg-white/20 text-white' 
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {seg.count}
              </span>
            </button>
          ))}
        </div>

        {/* Brands Grid */}
        <div 
          className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-4 md:gap-6 transform transition-all duration-700 delay-200 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          {filteredBrands.map((brand, index) => (
            <a
              key={brand.slug}
              href={brand.homepage}
              target="_blank"
              rel="noopener noreferrer"
              className="brand-card group relative bg-white rounded-xl border border-gray-100 p-4 md:p-5 flex flex-col items-center justify-center hover:border-green-300 hover:shadow-xl hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1"
              aria-label={`Visit ${brand.name} website`}
              title={brand.name}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Logo Container */}
              <div className="w-full h-14 md:h-16 flex items-center justify-center mb-3">
                <img
                  src={brand.logo}
                  alt={brand.alt}
                  loading="lazy"
                  width="140"
                  height="60"
                  className="max-w-[140px] h-auto max-h-full object-contain transition-transform duration-300 group-hover:scale-105"
                  role="img"
                />
              </div>
              
              {/* Brand Name */}
              <span className="text-xs font-medium text-gray-500 group-hover:text-green-600 transition-colors text-center">
                {brand.name}
              </span>
              
              {/* Segment Badge */}
              <span className="absolute top-2 right-2 text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                {brand.segment}
              </span>

              {/* External Link Icon */}
              <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <ExternalLink className="w-3 h-3 text-green-500" />
              </div>
            </a>
          ))}
        </div>

        {/* Footer Note */}
        <div 
          className={`text-center mt-10 transform transition-all duration-700 delay-300 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <p className="text-sm text-gray-500">
            And many more... <span className="text-green-600 font-medium">Contact us</span> for your specific EV brand
          </p>
        </div>
      </div>
    </section>
  );
};

export default BrandsSection;

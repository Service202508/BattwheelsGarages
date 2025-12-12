import React, { useState, useEffect, useRef } from 'react';

// Brand data with all 15 EV brands - names only
const brandsData = [
  { name: 'Ather Energy', slug: 'ather-energy', homepage: 'https://www.atherenergy.com', segment: '2W' },
  { name: 'Ola Electric', slug: 'ola-electric', homepage: 'https://www.olaelectric.com', segment: '2W' },
  { name: 'TVS Motor', slug: 'tvs', homepage: 'https://www.tvsmotor.com', segment: '2W' },
  { name: 'Bajaj Auto', slug: 'bajaj', homepage: 'https://www.bajajauto.com', segment: '2W/3W' },
  { name: 'Hero Electric', slug: 'hero-electric', homepage: 'https://www.heroelectric.in', segment: '2W' },
  { name: 'Revolt Motors', slug: 'revolt', homepage: 'https://www.revoltmotors.com', segment: '2W' },
  { name: 'Simple Energy', slug: 'simple-energy', homepage: 'https://www.simpleenergy.in', segment: '2W' },
  { name: 'Bounce', slug: 'bounce', homepage: 'https://www.bounceshare.com', segment: '2W' },
  { name: 'Chetak', slug: 'chetak', homepage: 'https://www.chetak.com', segment: '2W' },
  { name: 'Piaggio', slug: 'piaggio', homepage: 'https://www.piaggio.com', segment: '3W' },
  { name: 'Mahindra Electric', slug: 'mahindra', homepage: 'https://www.mahindraelectric.com', segment: '4W/3W' },
  { name: 'Tata Motors', slug: 'tata', homepage: 'https://www.tatamotors.com', segment: '4W' },
  { name: 'MG Motor', slug: 'mg', homepage: 'https://www.mgmotor.co.in', segment: '4W' },
  { name: 'BYD', slug: 'byd', homepage: 'https://www.byd.com', segment: '4W/Commercial' },
  { name: 'Euler Motors', slug: 'euler-motors', homepage: 'https://www.eulermotors.com', segment: 'Commercial' }
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
      className="py-16 md:py-20 bg-gradient-to-b from-gray-50 to-white"
    >
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div 
          className={`text-center mb-10 transform transition-all duration-700 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          <span className="inline-block px-4 py-1.5 bg-gradient-to-r from-[#0B8A44]/10 to-[#12B76A]/10 text-[#0B8A44] rounded-full text-sm font-semibold mb-4 border border-[#0B8A44]/20">
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
                  ? 'bg-gradient-to-r from-[#0B8A44] to-[#12B76A] text-white shadow-lg shadow-green-500/30'
                  : 'bg-white text-gray-700 border border-gray-200 hover:border-[#12B76A] hover:text-[#0B8A44]'
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

        {/* Brands Grid - Name Cards Only */}
        <div 
          className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-5 transform transition-all duration-700 delay-200 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}
        >
          {filteredBrands.map((brand, index) => (
            <a
              key={brand.slug}
              href={brand.homepage}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative bg-white rounded-xl border border-gray-200 p-5 md:p-6 flex items-center justify-center hover:border-[#12B76A] hover:shadow-lg hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1"
              aria-label={`Visit ${brand.name} website`}
              title={brand.name}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Brand Name Only */}
              <span className="text-sm md:text-base font-semibold text-gray-700 group-hover:text-[#0B8A44] transition-colors text-center">
                {brand.name}
              </span>
              
              {/* Hover Glow Effect */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
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
            And many more... <span className="text-[#0B8A44] font-medium">Contact us</span> for your specific EV brand
          </p>
        </div>
      </div>
    </section>
  );
};

export default BrandsSection;

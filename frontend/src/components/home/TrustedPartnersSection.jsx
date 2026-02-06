import React from 'react';

const TrustedPartnersSection = () => {
  // Partner logos with actual image files - 24 partners total
  const partners = [
    { name: 'Altigreen', logo: '/assets/partners/altigreen.jpg' },
    { name: 'Exponent', logo: '/assets/partners/exponent.jpeg' },
    { name: 'Indofast Energy', logo: '/assets/partners/indofast.png' },
    { name: 'Shiplog', logo: '/assets/partners/shiplog.png' },
    { name: 'Alt Mobility', logo: '/assets/partners/alt-mobility.png' },
    { name: 'Gentari', logo: '/assets/partners/gentari.webp' },
    { name: 'Magenta', logo: '/assets/partners/magenta.png' },
    { name: 'Sun Mobility', logo: '/assets/partners/sun-mobility.png' },
    { name: 'Bounce', logo: '/assets/partners/bounce.png' },
    { name: 'Lectrix', logo: '/assets/partners/lectrix.png' },
    { name: 'OSM', logo: '/assets/partners/osm.png' },
    { name: 'Zypp Electric', logo: '/assets/partners/zypp.png' },
    { name: 'Delhivery', logo: '/assets/partners/delhivery.png' },
    { name: 'eBlu', logo: '/assets/partners/eblu.png' },
    { name: 'Euler', logo: '/assets/partners/euler.webp' },
    { name: 'Log9', logo: '/assets/partners/log9.webp' },
    { name: 'MoEVing', logo: '/assets/partners/moeving.png' },
    { name: 'Piaggio', logo: '/assets/partners/piaggio.png' },
    { name: 'Quantum', logo: '/assets/partners/quantum.webp' },
    { name: 'Ola Electric', logo: '/assets/partners/ola-electric.jpeg' },
    { name: 'OPG Mobility', logo: '/assets/partners/opg-mobility.jpg' },
    { name: 'Yulu', logo: '/assets/partners/yulu.png' },
    { name: 'JEM', logo: '/assets/partners/jem.png' },
    { name: 'Lithium', logo: '/assets/partners/lithium.png' },
    { name: 'Bajaj', logo: '/assets/partners/bajaj.webp' },
  ];

  return (
    <section className="py-16 md:py-20 bg-gray-900 relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-green-500 to-transparent" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4">
            OEMs & Fleets Already Trust Us to Keep Wheels Turning
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Leading EV fleets, OEMs, and logistics companies rely on Battwheels for their service needs
          </p>
        </div>

        {/* Logo Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-5 max-w-6xl mx-auto">
          {partners.map((partner, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-3 md:p-4 flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 h-[70px] md:h-[85px]"
            >
              <img
                src={partner.logo}
                alt={partner.name}
                className="max-h-[45px] md:max-h-[55px] max-w-full object-contain"
                loading="lazy"
              />
            </div>
          ))}
        </div>

        {/* Stats Bar */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-[#12B76A]">24+</div>
            <div className="text-gray-400 text-sm mt-1">OEM & Fleet Partners</div>
          </div>
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-[#12B76A]">50K+</div>
            <div className="text-gray-400 text-sm mt-1">Vehicles Serviced</div>
          </div>
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-[#12B76A]">11</div>
            <div className="text-gray-400 text-sm mt-1">Cities Covered</div>
          </div>
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-[#12B76A]">98%</div>
            <div className="text-gray-400 text-sm mt-1">Client Retention</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TrustedPartnersSection;

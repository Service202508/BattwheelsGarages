import React from 'react';

const TrustedPartnersSection = () => {
  // Partner logos - using brand colors and names for visibility
  const partners = [
    { name: 'ALTIGREEN', color: '#00A650', textColor: '#00A650' },
    { name: 'exponent', color: '#333333', textColor: '#333333' },
    { name: 'INDOFAST ENERGY', color: '#FFD700', textColor: '#333333', bg: '#FFD700' },
    { name: 'Shiplog', color: '#E53935', textColor: '#E53935' },
    { name: 'alt.mobility', color: '#333333', textColor: '#333333', accent: '#FFD700' },
    { name: 'gentari', color: '#00BCD4', textColor: '#00BCD4' },
    { name: 'magenta', color: '#E91E63', textColor: '#E91E63' },
    { name: 'SUN MOBILITY', color: '#4CAF50', textColor: '#333333' },
    { name: 'BOUNCE infinity', color: '#FF0000', textColor: '#FFFFFF', bg: '#FF0000' },
    { name: 'LECTRIX', color: '#00C853', textColor: '#00C853' },
    { name: 'OSM', color: '#333333', textColor: '#333333' },
    { name: 'ZYPP ELECTRIC', color: '#00E676', textColor: '#00E676' },
    { name: 'DELHIVERY', color: '#E53935', textColor: '#E53935' },
    { name: 'eBlu', color: '#2196F3', textColor: '#2196F3' },
    { name: 'EULER', color: '#333333', textColor: '#333333' },
    { name: 'LOG9', color: '#FF5722', textColor: '#FFFFFF', bg: '#FF5722' },
    { name: 'MoEVing', color: '#4CAF50', textColor: '#4CAF50' },
    { name: 'PIAGGIO', color: '#00695C', textColor: '#00695C' },
    { name: 'Quantum', color: '#00BCD4', textColor: '#00BCD4' },
  ];

  return (
    <section className="py-16 md:py-20 relative overflow-hidden">
      {/* Background with overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920')] bg-cover bg-center opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-900/50 to-gray-900/80" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4">
            Fleets Already Trust Us to Keep Wheels Turning
          </h2>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Leading EV fleets, OEMs, and logistics companies rely on Battwheels for their service needs
          </p>
        </div>

        {/* Logo Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6 max-w-6xl mx-auto">
          {partners.map((partner, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-4 md:p-5 flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 min-h-[80px] md:min-h-[90px]"
            >
              {partner.bg ? (
                <div 
                  className="px-3 py-2 rounded-lg w-full text-center"
                  style={{ backgroundColor: partner.bg }}
                >
                  <span 
                    className="font-bold text-sm md:text-base tracking-wide"
                    style={{ color: partner.textColor }}
                  >
                    {partner.name}
                  </span>
                </div>
              ) : (
                <span 
                  className="font-bold text-sm md:text-base tracking-wide text-center"
                  style={{ color: partner.textColor }}
                >
                  {partner.name.includes('alt.') ? (
                    <span>
                      alt<span style={{ color: '#FFD700' }}>.</span>
                      <span className="text-gray-400 text-xs block">mobility</span>
                    </span>
                  ) : partner.name.includes('infinity') ? (
                    <span>
                      <span className="text-red-500 font-black">BOUNCE</span>
                      <span className="text-gray-600 text-xs block">infinity</span>
                    </span>
                  ) : partner.name.includes('SUN') ? (
                    <span className="flex items-center gap-1 justify-center">
                      <span className="text-yellow-500">☀</span>
                      <span>
                        <span className="text-green-600 font-bold">SUN</span>
                        <span className="text-gray-600 block text-xs">MOBILITY</span>
                      </span>
                    </span>
                  ) : partner.name.includes('ZYPP') ? (
                    <span>
                      <span className="text-green-500 font-black">ZYPP</span>
                      <span className="text-green-400 text-xs block">ELECTRIC</span>
                    </span>
                  ) : partner.name.includes('Quantum') ? (
                    <span>
                      <span style={{ color: partner.textColor }}>Quantum</span>
                      <span className="text-cyan-400 text-xs block">• • • • • eScooters</span>
                    </span>
                  ) : (
                    partner.name
                  )}
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Stats Bar */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-[#12B76A]">19+</div>
            <div className="text-gray-400 text-sm mt-1">Fleet Partners</div>
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

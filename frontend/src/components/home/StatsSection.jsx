import React from 'react';
import { stats } from '../../data/mockData';

const StatsSection = () => {
  return (
    <section className="py-16 bg-gradient-to-b from-white to-green-50/30 border-y border-green-100">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.id} className="text-center">
              <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[#0B8A44] to-[#12B76A] bg-clip-text text-transparent mb-2">
                {stat.value}{stat.suffix}
              </div>
              <div className="text-gray-600 text-sm md:text-base">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
import React from 'react';
import { coreUSPs, comparisonData } from '../mockData';
import { Zap, MapPin, TrendingUp, Clock, Map, Shield } from 'lucide-react';

const iconMap = {
  Zap,
  MapPin,
  TrendingUp,
  Clock,
  Map,
  Shield
};

const WhyBattwheelsSection = () => {
  return (
    <section id="why" className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why Battwheels Garages
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            India's first and only EV-focused aftersales infrastructure with proven operational credibility
          </p>
        </div>

        {/* Core USPs Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {coreUSPs.map((usp) => {
            const Icon = iconMap[usp.icon];
            return (
              <div key={usp.id} className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="bg-green-100 p-3 rounded-lg">
                    <Icon className="w-6 h-6 text-green-600" />
                  </div>
                  <span className="text-xs font-bold text-green-600 bg-green-50 px-3 py-1 rounded-full">
                    {usp.stats}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{usp.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{usp.description}</p>
              </div>
            );
          })}
        </div>

        {/* Comparison Table */}
        <div className="max-w-5xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Battwheels vs Traditional RSA
          </h3>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Feature</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Traditional RSA</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-green-600">Battwheels Garages</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {comparisonData.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{row.feature}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{row.traditional}</td>
                      <td className="px-6 py-4 text-sm text-green-700 font-medium">{row.battwheels}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default WhyBattwheelsSection;
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Phone, Calendar } from 'lucide-react';
import { companyInfo } from '../../data/mockData';

const CTABand = () => {
  const navigate = useNavigate();

  return (
    <section className="py-16 bg-gradient-to-r from-[#0B8A44] via-[#0F9D52] to-[#12B76A] text-white relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-60 h-60 bg-white rounded-full translate-x-1/3 translate-y-1/3" />
      </div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Need EV Service Today?
          </h2>
          <p className="text-xl text-green-50 mb-8">
            {companyInfo.hours}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              className="bg-white text-[#0B8A44] hover:bg-gray-50 hover:shadow-lg transition-all duration-300 font-semibold"
              onClick={() => window.open('https://battwheelsgarages.battwheels.com/submit-ticket', '_blank')}
            >
              <Calendar className="mr-2 w-5 h-5" />
              Book EV Service
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              className="border-2 border-white text-white hover:bg-white/10 transition-all duration-300 font-semibold"
              onClick={() => window.location.href = `tel:${companyInfo.phone}`}
            >
              <Phone className="mr-2 w-5 h-5" />
              Call Now
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTABand;
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Phone, Calendar } from 'lucide-react';
import { companyInfo } from '../../data/mockData';

const CTABand = () => {
  const navigate = useNavigate();

  return (
    <section className="py-16 bg-gradient-to-r from-green-600 to-green-500 text-white">
      <div className="container mx-auto px-4">
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
              className="bg-white text-green-600 hover:bg-gray-100"
              onClick={() => navigate('/book-service')}
            >
              <Calendar className="mr-2 w-5 h-5" />
              Book EV Service
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              className="border-white text-white hover:bg-green-700"
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
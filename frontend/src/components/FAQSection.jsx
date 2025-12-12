import React from 'react';
import { Link } from 'react-router-dom';
import { faqs } from '../data/mockData';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from './ui/accordion';
import { HelpCircle, ChevronRight } from 'lucide-react';

const FAQSection = () => {
  // Show top 8 most important FAQs on homepage (mix of categories)
  const featuredFaqIds = [1, 2, 6, 7, 11, 17, 18, 26];
  const displayFaqs = faqs.filter(faq => featuredFaqIds.includes(faq.id));

  return (
    <section className="py-16 md:py-20 bg-gradient-to-b from-white to-gray-50">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          {/* Section Header */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-700 text-sm font-medium mb-4">
              <HelpCircle className="w-4 h-4 mr-2" />
              Common Questions
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Quick answers about our EV services, fleet programs, and how we operate
            </p>
          </div>

          {/* FAQ Accordion */}
          <Accordion type="single" collapsible className="space-y-3">
            {displayFaqs.map((faq) => (
              <AccordionItem 
                key={faq.id} 
                value={`item-${faq.id}`}
                className="bg-white border border-gray-200 rounded-xl px-6 shadow-sm hover:shadow-md transition-all"
              >
                <AccordionTrigger className="text-left hover:no-underline py-5">
                  <span className="font-semibold text-gray-900 pr-4">{faq.question}</span>
                </AccordionTrigger>
                <AccordionContent className="text-gray-600 pb-5 leading-relaxed">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>

          {/* View All Link */}
          <div className="text-center mt-10">
            <Link 
              to="/faq"
              className="inline-flex items-center px-6 py-3 rounded-xl bg-[#0B8A44] text-white font-medium hover:bg-[#0A7A3D] transition-colors shadow-md hover:shadow-lg"
            >
              View All 34 FAQs
              <ChevronRight className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FAQSection;

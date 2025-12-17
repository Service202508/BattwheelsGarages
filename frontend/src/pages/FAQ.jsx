import React, { useState } from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import SEO from '../components/common/SEO';
import { faqs, faqCategories } from '../data/mockData';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import { HelpCircle, AlertTriangle, Wrench, Calendar, Cpu, Building, Globe, ChevronRight } from 'lucide-react';

const iconMap = {
  HelpCircle,
  AlertTriangle,
  Wrench,
  Calendar,
  Cpu,
  Building,
  Globe
};

const FAQ = () => {
  const [activeCategory, setActiveCategory] = useState('all');

  const filteredFaqs = activeCategory === 'all' 
    ? faqs 
    : faqs.filter(faq => faq.category === activeCategory);

  const getCategoryName = (categoryId) => {
    const category = faqCategories.find(c => c.id === categoryId);
    return category ? category.name : 'General';
  };

  return (
    <div className="min-h-screen relative">
      <GearBackground variant="default" />
      <Header />
      <main>
        {/* Hero */}
        <section className="py-16 md:py-20 bg-gradient-to-br from-green-50 via-white to-green-50/50">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-700 text-sm font-medium mb-6">
                <HelpCircle className="w-4 h-4 mr-2" />
                34 Questions Answered
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Frequently Asked Questions
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Everything you need to know about our EV services, fleet programs, and operations
              </p>
            </div>
          </div>
        </section>

        {/* Category Tabs */}
        <section className="py-6 bg-white border-b border-gray-100 sticky top-[72px] z-40">
          <div className="container mx-auto px-4">
            <div className="flex flex-wrap gap-2 justify-center">
              <button
                onClick={() => setActiveCategory('all')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  activeCategory === 'all'
                    ? 'bg-[#0B8A44] text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All FAQs ({faqs.length})
              </button>
              {faqCategories.map((category) => {
                const Icon = iconMap[category.icon];
                const count = faqs.filter(f => f.category === category.id).length;
                return (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      activeCategory === category.id
                        ? 'bg-[#0B8A44] text-white shadow-md'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {Icon && <Icon className="w-4 h-4 mr-2" />}
                    {category.name} ({count})
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* FAQs */}
        <section className="py-12 md:py-20 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              {activeCategory === 'all' ? (
                // Show all FAQs grouped by category
                faqCategories.map((category) => {
                  const categoryFaqs = faqs.filter(f => f.category === category.id);
                  const Icon = iconMap[category.icon];
                  
                  return (
                    <div key={category.id} className="mb-10">
                      <div className="flex items-center mb-6">
                        <div className="w-10 h-10 rounded-lg bg-[#0B8A44]/10 flex items-center justify-center mr-3">
                          {Icon && <Icon className="w-5 h-5 text-[#0B8A44]" />}
                        </div>
                        <h2 className="text-xl md:text-2xl font-bold text-gray-900">
                          {category.name}
                        </h2>
                      </div>
                      <Accordion type="single" collapsible className="space-y-3">
                        {categoryFaqs.map((faq) => (
                          <AccordionItem 
                            key={faq.id} 
                            value={`item-${faq.id}`}
                            className="bg-white border border-gray-200 rounded-xl px-6 shadow-sm hover:shadow-md transition-shadow"
                          >
                            <AccordionTrigger className="text-left hover:no-underline py-5">
                              <span className="font-semibold text-gray-900 pr-4 text-base">
                                {faq.question}
                              </span>
                            </AccordionTrigger>
                            <AccordionContent className="text-gray-600 pb-5 text-base leading-relaxed">
                              {faq.answer}
                            </AccordionContent>
                          </AccordionItem>
                        ))}
                      </Accordion>
                    </div>
                  );
                })
              ) : (
                // Show filtered FAQs
                <div>
                  <div className="flex items-center mb-6">
                    {(() => {
                      const category = faqCategories.find(c => c.id === activeCategory);
                      const Icon = category ? iconMap[category.icon] : null;
                      return (
                        <>
                          <div className="w-10 h-10 rounded-lg bg-[#0B8A44]/10 flex items-center justify-center mr-3">
                            {Icon && <Icon className="w-5 h-5 text-[#0B8A44]" />}
                          </div>
                          <h2 className="text-xl md:text-2xl font-bold text-gray-900">
                            {getCategoryName(activeCategory)} FAQs
                          </h2>
                        </>
                      );
                    })()}
                  </div>
                  <Accordion type="single" collapsible className="space-y-3">
                    {filteredFaqs.map((faq) => (
                      <AccordionItem 
                        key={faq.id} 
                        value={`item-${faq.id}`}
                        className="bg-white border border-gray-200 rounded-xl px-6 shadow-sm hover:shadow-md transition-shadow"
                      >
                        <AccordionTrigger className="text-left hover:no-underline py-5">
                          <span className="font-semibold text-gray-900 pr-4 text-base">
                            {faq.question}
                          </span>
                        </AccordionTrigger>
                        <AccordionContent className="text-gray-600 pb-5 text-base leading-relaxed">
                          {faq.answer}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              )}

              {/* Still have questions */}
              <div className="mt-12 bg-gradient-to-br from-[#0B8A44] to-[#12B76A] p-8 md:p-10 rounded-2xl text-center text-white shadow-xl">
                <h3 className="text-2xl md:text-3xl font-bold mb-4">Still Have Questions?</h3>
                <p className="text-green-100 mb-8 text-lg">
                  Our team is here to help. Contact us for any additional queries about EV services.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <a 
                    href="/contact"
                    className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-xl bg-white text-[#0B8A44] hover:bg-green-50 transition-colors shadow-lg"
                  >
                    Contact Us
                    <ChevronRight className="w-5 h-5 ml-2" />
                  </a>
                  <a 
                    href="https://wa.me/918076331607"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-xl border-2 border-white/30 text-white hover:bg-white/10 transition-colors"
                  >
                    WhatsApp: +91 8076331607
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default FAQ;

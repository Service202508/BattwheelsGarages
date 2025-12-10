import React from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { faqs } from '../data/mockData';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';

const FAQ = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Frequently Asked Questions
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Common questions about our EV services, fleet programs, and operations
              </p>
            </div>
          </div>
        </section>

        {/* FAQs */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto">
              <Accordion type="single" collapsible className="space-y-4">
                {faqs.map((faq) => (
                  <AccordionItem 
                    key={faq.id} 
                    value={`item-${faq.id}`}
                    className="bg-gray-50 border border-gray-200 rounded-lg px-6"
                  >
                    <AccordionTrigger className="text-left hover:no-underline py-6">
                      <span className="font-semibold text-gray-900 pr-4">{faq.question}</span>
                    </AccordionTrigger>
                    <AccordionContent className="text-gray-600 pb-6">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>

              {/* Still have questions */}
              <div className="mt-12 bg-green-50 p-8 rounded-xl text-center">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">Still Have Questions?</h3>
                <p className="text-gray-600 mb-6">Our team is here to help. Contact us for any additional queries.</p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <a 
                    href="/contact"
                    className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 transition-colors"
                  >
                    Contact Us
                  </a>
                  <a 
                    href={`tel:+918076331607`}
                    className="inline-flex items-center justify-center px-6 py-3 border border-green-600 text-base font-medium rounded-lg text-green-600 bg-white hover:bg-green-50 transition-colors"
                  >
                    Call: +91 8076331607
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
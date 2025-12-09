import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import HeroSection from '../components/HeroSection';
import ProblemSolutionSection from '../components/ProblemSolutionSection';
import AboutSection from '../components/AboutSection';
import ServicesSection from '../components/ServicesSection';
import FleetSolutionsSection from '../components/FleetSolutionsSection';
import WhyBattwheelsSection from '../components/WhyBattwheelsSection';
import GarageModelsSection from '../components/GarageModelsSection';
import TestimonialsSection from '../components/TestimonialsSection';
import PartnersSection from '../components/PartnersSection';
import FAQSection from '../components/FAQSection';
import ContactSection from '../components/ContactSection';
import { Toaster } from '../components/ui/toaster';

const Home = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <HeroSection />
        <ProblemSolutionSection />
        <AboutSection />
        <ServicesSection />
        <FleetSolutionsSection />
        <WhyBattwheelsSection />
        <GarageModelsSection />
        <TestimonialsSection />
        <PartnersSection />
        <FAQSection />
        <ContactSection />
      </main>
      <Footer />
      <Toaster />
    </div>
  );
};

export default Home;
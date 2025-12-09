import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import HeroSection from '../components/HeroSection';
import ServicesSection from '../components/ServicesSection';
import AboutSection from '../components/AboutSection';
import StatsSection from '../components/StatsSection';
import TestimonialsSection from '../components/TestimonialsSection';
import FeaturesSection from '../components/FeaturesSection';
import BrandsSection from '../components/BrandsSection';
import FAQSection from '../components/FAQSection';
import ContactSection from '../components/ContactSection';
import { Toaster } from '../components/ui/toaster';

const Home = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <HeroSection />
        <ServicesSection />
        <AboutSection />
        <StatsSection />
        <TestimonialsSection />
        <FeaturesSection />
        <BrandsSection />
        <FAQSection />
        <ContactSection />
      </main>
      <Footer />
      <Toaster />
    </div>
  );
};

export default Home;
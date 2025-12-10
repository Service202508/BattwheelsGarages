import React from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import HeroSection from '../components/home/HeroSection';
import RSAExplainedSection from '../components/home/RSAExplainedSection';
import StatsSection from '../components/home/StatsSection';
import WhyChooseSection from '../components/home/WhyChooseSection';
import ServiceCategoriesSection from '../components/home/ServiceCategoriesSection';
import IndustriesSlider from '../components/home/IndustriesSlider';
import BrandsSection from '../components/home/BrandsSection';
import TestimonialsSection from '../components/home/TestimonialsSection';
import CTABand from '../components/home/CTABand';

const Home = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <HeroSection />
        <RSAExplainedSection />
        <StatsSection />
        <WhyChooseSection />
        <ServiceCategoriesSection />
        <IndustriesSlider />
        <BrandsSection />
        <TestimonialsSection />
        <CTABand />
      </main>
      <Footer />
    </div>
  );
};

export default Home;
import React from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import PremiumHeroSection from '../components/home/PremiumHeroSection';
import VehicleTypesSection from '../components/home/VehicleTypesSection';
import RSAExplainedSection from '../components/home/RSAExplainedSection';
import StatsSection from '../components/home/StatsSection';
import WhyChooseSection from '../components/home/WhyChooseSection';
import ServiceCategoriesSection from '../components/home/ServiceCategoriesSection';
import IndustriesSlider from '../components/home/IndustriesSlider';
import BrandsSection from '../components/home/BrandsSection';
import ImprovedTestimonialsSection from '../components/home/ImprovedTestimonialsSection';
import CTABand from '../components/home/CTABand';

const Home = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <PremiumHeroSection />
        <VehicleTypesSection />
        <RSAExplainedSection />
        <StatsSection />
        <WhyChooseSection />
        <ServiceCategoriesSection />
        <IndustriesSlider />
        <BrandsSection />
        <ImprovedTestimonialsSection />
        <CTABand />
      </main>
      <Footer />
    </div>
  );
};

export default Home;
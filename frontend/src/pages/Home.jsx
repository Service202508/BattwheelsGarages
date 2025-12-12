import React from 'react';
import { Helmet } from 'react-helmet-async';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import PremiumHeroSection from '../components/home/PremiumHeroSection';
import VehicleTypesSection from '../components/home/VehicleTypesSection';
import RSAExplainedSection from '../components/home/RSAExplainedSection';
import StatsSection from '../components/home/StatsSection';
import WhyChooseSection from '../components/home/WhyChooseSection';
import VisionMissionGoals from '../components/home/VisionMissionGoals';
import ServiceCategoriesSection from '../components/home/ServiceCategoriesSection';
import IndustriesSlider from '../components/home/IndustriesSlider';
import BrandsSection from '../components/home/BrandsSection';
import ImprovedTestimonialsSection from '../components/home/ImprovedTestimonialsSection';
import CTABand from '../components/home/CTABand';
import { getLocalBusinessSchema } from '../utils/schema';

const Home = () => {
  return (
    <div className="min-h-screen relative">
      {/* Rotating Gears Background */}
      <GearBackground variant="home" />
      <Helmet>
        <title>Battwheels Garages | India&apos;s #1 EV Onsite Service & Repair</title>
        <meta name="description" content="India's first no-towing-first EV service model. Onsite diagnosis and repair for 2W, 3W, 4W and commercial EVs. 85% issues resolved on field. Open 365 days." />
        <link rel="canonical" href="https://battwheelsgarages.in" />
        
        {/* OpenGraph */}
        <meta property="og:title" content="Battwheels Garages | India's #1 EV Onsite Service" />
        <meta property="og:description" content="India's first no-towing-first EV service model. Onsite diagnosis and repair for all EV types." />
        <meta property="og:image" content="https://battwheelsgarages.in/assets/battwheels-logo-new.png" />
        <meta property="og:url" content="https://battwheelsgarages.in" />
        <meta property="og:type" content="website" />
        <meta property="og:site_name" content="Battwheels Garages" />
        
        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Battwheels Garages | India's #1 EV Onsite Service" />
        <meta name="twitter:description" content="India's first no-towing-first EV service model. Onsite diagnosis and repair for all EV types." />
        <meta name="twitter:image" content="https://battwheelsgarages.in/assets/battwheels-logo-new.png" />
        
        {/* JSON-LD LocalBusiness Schema */}
        <script type="application/ld+json">
          {JSON.stringify(getLocalBusinessSchema())}
        </script>
      </Helmet>
      
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
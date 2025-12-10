import React, { useEffect, useState } from 'react';
import AdvancedFloatingCard from './AdvancedFloatingCard';

const HeroSection = () => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <section className="hero-section-wrapper">
      {/* Hero Background with Composite EV Images */}
      <div 
        className="hero-background"
        style={{
          transform: `translateY(${scrollY * 0.4}px)`,
        }}
      >
        {/* Main Hero Image - Composite of Multiple EVs */}
        <div className="hero-image-overlay"></div>
        <img 
          src="https://customer-assets.emergentagent.com/job_car-repair-zone-1/artifacts/khzyy699_Gemini_Generated_Image_pb7w79pb7w79pb7w.png" 
          alt="Electric Vehicles Service - Multiple EVs including Auto-Rickshaws"
          className="hero-main-image"
          loading="eager"
        />
        
        {/* Gradient Overlay for Text Readability */}
        <div className="hero-gradient-overlay"></div>
      </div>

      {/* Content Container */}
      <div className="hero-content-container">
        <div className="container mx-auto px-4 py-20 md:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Side - Advanced Floating Card */}
            <div className="hero-floating-card-wrapper">
              <AdvancedFloatingCard />
            </div>

            {/* Right Side - Visual Stats Card */}
            <div className="hero-stats-card">
              <div className="stats-card-content">
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-icon">🏍️</div>
                    <div className="stat-label">2-Wheeler EVs</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-icon">🛺</div>
                    <div className="stat-label">3-Wheeler EVs</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-icon">🚗</div>
                    <div className="stat-label">4-Wheeler EVs</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-icon">🚚</div>
                    <div className="stat-label">Commercial EVs</div>
                  </div>
                </div>
                
                <div className="main-stat">
                  <div className="main-stat-number">10,000+</div>
                  <div className="main-stat-label">Electric Vehicles Serviced</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .hero-section-wrapper {
          position: relative;
          min-height: 90vh;
          overflow: hidden;
          background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 100%);
        }

        .hero-background {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 0;
          will-change: transform;
        }

        .hero-main-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          object-position: center;
        }

        .hero-image-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.1);
          z-index: 1;
        }

        .hero-gradient-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(135deg, rgba(0, 0, 0, 0.5) 0%, transparent 60%);
          z-index: 2;
        }

        .hero-content-container {
          position: relative;
          z-index: 10;
        }

        .hero-floating-card-wrapper {
          animation: fadeInUp 1s ease-out;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .hero-stats-card {
          display: none;
        }

        @media (min-width: 1024px) {
          .hero-stats-card {
            display: block;
            animation: fadeInRight 1s ease-out 0.3s both;
          }
        }

        @keyframes fadeInRight {
          from {
            opacity: 0;
            transform: translateX(40px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .stats-card-content {
          backdrop-filter: blur(20px) brightness(1.1);
          background: rgba(255, 255, 255, 0.9);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 24px;
          padding: 40px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 24px;
          margin-bottom: 32px;
        }

        .stat-item {
          text-align: center;
          padding: 20px;
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%);
          border-radius: 16px;
          transition: all 0.3s ease;
          cursor: pointer;
        }

        .stat-item:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
        }

        .stat-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }

        .stat-label {
          font-size: 14px;
          font-weight: 600;
          color: #4a4a4a;
        }

        .main-stat {
          text-align: center;
          padding: 32px;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          border-radius: 20px;
          color: white;
        }

        .main-stat-number {
          font-size: 56px;
          font-weight: 700;
          margin-bottom: 8px;
        }

        .main-stat-label {
          font-size: 18px;
          font-weight: 500;
        }

        @media (max-width: 1023px) {
          .hero-section-wrapper {
            min-height: auto;
          }

          .hero-background {
            opacity: 0.3;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .hero-floating-card-wrapper,
          .hero-stats-card,
          .stat-item {
            animation: none !important;
          }
          
          .hero-background {
            transform: none !important;
          }
        }
      `}</style>
    </section>
  );
};

export default HeroSection;
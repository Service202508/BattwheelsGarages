import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Phone, Check } from 'lucide-react';

const AdvancedFloatingCard = () => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    setTimeout(() => setIsVisible(true), 300);
  }, []);

  const processSteps = [
    { id: 1, icon: '🚫', label: 'No Towing First', delay: 0 },
    { id: 2, icon: '🔍', label: 'Diagnose Onsite', delay: 150 },
    { id: 3, icon: '🔧', label: 'Repair On-Spot', delay: 300 },
    { id: 4, icon: '✅', label: 'Resume Operations', delay: 450 }
  ];

  const trustBadges = [
    'Open 365 Days',
    '11 Cities Covered',
    '95% Uptime Guaranteed'
  ];

  return (
    <div 
      className={`floating-card-container ${isVisible ? 'animate-in' : ''}`}
      style={{
        position: 'relative',
        zIndex: 10
      }}
    >
      <div className="floating-card">
        {/* Main Content */}
        <div className="card-content">
          {/* Primary Headline */}
          <h1 className="card-headline">
            EVs Don't Need Towing First.
            <br />
            <span className="headline-emphasis">They Need Diagnosis & Repair Onsite.</span>
          </h1>

          {/* Secondary Description */}
          <p className="card-description">
            India's first <strong>no-towing-first</strong> EV service model. We come to you - diagnosing and fixing your 2W, 3W, 4W and commercial EVs right where they stop. More uptime, lower costs.
          </p>

          {/* Process Flow Section */}
          <div className="process-section">
            <h3 className="process-title">The Battwheels Difference</h3>
            
            <div className="process-steps-container">
              {processSteps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div 
                    className="process-step"
                    style={{ animationDelay: `${step.delay}ms` }}
                  >
                    <div className="step-icon-container">
                      <span className="step-icon">{step.icon}</span>
                    </div>
                    <p className="step-label">{step.label}</p>
                  </div>
                  {index < processSteps.length - 1 && (
                    <div className="step-arrow">→</div>
                  )}
                </React.Fragment>
              ))}
            </div>

            {/* Key Statistics */}
            <div className="stats-badges">
              <span className="stat-badge">85% issues resolved on field</span>
              <span className="stat-badge">2 hrs Avg Breakdown TAT</span>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="cta-buttons">
            <button 
              className="btn-primary"
              onClick={() => window.open('https://cloud-finance-suite.preview.emergentagent.com/submit-ticket', '_blank')}
            >
              Book EV Service Now
              <ArrowRight className="btn-icon" />
            </button>
            <button 
              className="btn-secondary"
              onClick={() => navigate('/fleet-oem')}
            >
              <Phone className="btn-icon" />
              Talk to Fleet & OEM Team
            </button>
          </div>

          {/* Trust Badges */}
          <div className="trust-badges">
            {trustBadges.map((badge, index) => (
              <div key={index} className="trust-badge">
                <Check className="badge-icon" />
                <span>{badge}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        .floating-card-container {
          opacity: 0;
          transform: translateY(30px);
          transition: all 0.8s ease-out;
        }

        .floating-card-container.animate-in {
          opacity: 1;
          transform: translateY(0);
        }

        .floating-card {
          backdrop-filter: blur(20px) brightness(1.1);
          background: rgba(255, 255, 255, 0.85);
          background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.8) 100%);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 24px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
          padding: 40px;
          max-width: 600px;
          transition: all 0.3s ease;
        }

        .floating-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 24px 70px rgba(0, 0, 0, 0.18);
        }

        @media (max-width: 768px) {
          .floating-card {
            padding: 24px;
            max-width: 90vw;
            margin: 0 auto;
          }
        }

        .card-headline {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 32px;
          font-weight: 700;
          line-height: 1.3;
          color: #1a1a1a;
          margin-bottom: 16px;
        }

        .headline-emphasis {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        @media (max-width: 768px) {
          .card-headline {
            font-size: 24px;
          }
        }

        .card-description {
          font-size: 16px;
          line-height: 1.6;
          color: #4a4a4a;
          margin-bottom: 32px;
        }

        @media (max-width: 768px) {
          .card-description {
            font-size: 14px;
          }
        }

        .process-section {
          margin-bottom: 32px;
        }

        .process-title {
          font-size: 20px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 24px;
          text-align: center;
        }

        .process-steps-container {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 24px;
          overflow-x: auto;
          scroll-snap-type: x mandatory;
          -webkit-overflow-scrolling: touch;
          padding: 8px 0;
        }

        @media (max-width: 768px) {
          .process-steps-container {
            justify-content: flex-start;
          }
        }

        .process-step {
          flex: 0 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          scroll-snap-align: start;
          animation: slideIn 0.6s ease-out forwards;
          opacity: 0;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .step-icon-container {
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          cursor: pointer;
        }

        .step-icon-container:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
        }

        @media (max-width: 768px) {
          .step-icon-container {
            width: 60px;
            height: 60px;
          }
        }

        .step-icon {
          font-size: 36px;
        }

        @media (max-width: 768px) {
          .step-icon {
            font-size: 28px;
          }
        }

        .step-label {
          font-size: 13px;
          font-weight: 600;
          color: #4a4a4a;
          text-align: center;
          max-width: 100px;
        }

        .step-arrow {
          font-size: 24px;
          color: #10b981;
          flex-shrink: 0;
          animation: arrowPulse 2s ease-in-out infinite;
        }

        @keyframes arrowPulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }

        @media (max-width: 768px) {
          .step-arrow {
            font-size: 20px;
          }
        }

        .stats-badges {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          justify-content: center;
        }

        .stat-badge {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          padding: 8px 16px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 600;
          display: inline-flex;
          align-items: center;
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
          animation: fadeIn 0.6s ease-out forwards;
          animation-delay: 0.8s;
          opacity: 0;
        }

        @keyframes fadeIn {
          to { opacity: 1; }
        }

        .cta-buttons {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        @media (max-width: 768px) {
          .cta-buttons {
            flex-direction: column;
          }
        }

        .btn-primary,
        .btn-secondary {
          flex: 1;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 16px 32px;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          border: none;
          cursor: pointer;
          transition: all 0.3s ease;
          animation: scaleIn 0.4s ease-out forwards;
          animation-delay: 0.6s;
          opacity: 0;
          transform: scale(0.9);
        }

        @keyframes scaleIn {
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .btn-primary {
          background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
          color: white;
          box-shadow: 0 4px 14px rgba(255, 107, 53, 0.4);
        }

        .btn-primary:hover {
          transform: scale(1.02);
          filter: brightness(1.1);
          box-shadow: 0 6px 20px rgba(255, 107, 53, 0.5);
        }

        .btn-primary:active {
          transform: scale(0.98);
        }

        .btn-secondary {
          background: transparent;
          border: 2px solid #FF6B35;
          color: #FF6B35;
        }

        .btn-secondary:hover {
          background: #FF6B35;
          color: white;
        }

        .btn-icon {
          width: 18px;
          height: 18px;
        }

        .trust-badges {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          justify-content: center;
          animation: fadeIn 0.6s ease-out forwards;
          animation-delay: 1s;
          opacity: 0;
        }

        .trust-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: #f5f5f5;
          border-radius: 20px;
          font-size: 13px;
          color: #4a4a4a;
        }

        .badge-icon {
          width: 14px;
          height: 14px;
          color: #10b981;
        }
      `}</style>
    </div>
  );
};

export default AdvancedFloatingCard;

import React, { useState, useEffect } from 'react';
import { MessageCircle, X } from 'lucide-react';

const FloatingWhatsApp = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Show button after 2 seconds
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  const handleWhatsAppClick = () => {
    window.open('https://wa.me/918076331607', '_blank', 'noopener,noreferrer');
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Expanded tooltip */}
      {isExpanded && (
        <div className="absolute bottom-16 right-0 mb-2 bg-white rounded-lg shadow-2xl p-4 w-64 animate-in slide-in-from-bottom-4 duration-300">
          <button
            onClick={() => setIsExpanded(false)}
            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
            aria-label="Close WhatsApp tooltip"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="pr-6">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">Battwheels Support</p>
                <p className="text-xs text-green-600">Online</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-3">
              Need help with EV service? Chat with us on WhatsApp!
            </p>
            <button
              onClick={handleWhatsAppClick}
              className="w-full bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors text-sm font-medium"
            >
              Start Chat
            </button>
          </div>
        </div>
      )}

      {/* Floating button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        onMouseEnter={() => setIsExpanded(true)}
        className="group relative bg-green-500 hover:bg-green-600 text-white rounded-full p-4 shadow-2xl hover:shadow-green-500/50 transition-all duration-300 hover:scale-110 animate-bounce-slow"
        aria-label="Open WhatsApp chat"
      >
        {/* Pulse animation ring */}
        <span className="absolute inset-0 rounded-full bg-green-500 opacity-75 animate-ping" />
        
        {/* Icon */}
        <MessageCircle className="w-6 h-6 relative z-10" />
        
        {/* Notification badge */}
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
          1
        </span>
      </button>
    </div>
  );
};

export default FloatingWhatsApp;

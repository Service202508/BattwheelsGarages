// Google Analytics 4 tracking utilities
// Replace G-XXXXXXXXXX with your actual GA4 Measurement ID

const GA_MEASUREMENT_ID = 'G-XXXXXXXXXX';

// Track page views (for React Router navigation)
export const trackPageView = (url, title) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', GA_MEASUREMENT_ID, {
      page_path: url,
      page_title: title,
    });
  }
};

// Track custom events
export const trackEvent = (action, category, label, value) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', action, {
      event_category: category,
      event_label: label,
      value: value,
    });
  }
};

// Track form submissions
export const trackFormSubmission = (formName, success = true) => {
  trackEvent(
    success ? 'form_submission_success' : 'form_submission_error',
    'Forms',
    formName
  );
};

// Track button clicks
export const trackButtonClick = (buttonName, location) => {
  trackEvent('button_click', 'Engagement', `${buttonName} - ${location}`);
};

// Track service booking
export const trackBooking = (vehicleType, serviceType, city) => {
  trackEvent('booking_initiated', 'Conversions', `${vehicleType} - ${serviceType}`, 1);
  
  // Also track as conversion
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'conversion', {
      send_to: `${GA_MEASUREMENT_ID}/booking`,
      value: 1,
      currency: 'INR',
    });
  }
};

// Track fleet enquiry
export const trackFleetEnquiry = (companyName, fleetSize) => {
  trackEvent('fleet_enquiry', 'Conversions', `${companyName} - ${fleetSize} vehicles`, fleetSize);
};

// Track contact form
export const trackContactSubmission = (subject) => {
  trackEvent('contact_submission', 'Conversions', subject, 1);
};

// Track career application
export const trackCareerApplication = (jobTitle) => {
  trackEvent('career_application', 'Conversions', jobTitle, 1);
};

// Track WhatsApp clicks
export const trackWhatsAppClick = (location) => {
  trackEvent('whatsapp_click', 'Engagement', location);
};

// Track phone calls
export const trackPhoneCall = (location) => {
  trackEvent('phone_click', 'Engagement', location);
};

// Track outbound links
export const trackOutboundLink = (url, label) => {
  trackEvent('outbound_click', 'Engagement', label || url);
};

export default {
  trackPageView,
  trackEvent,
  trackFormSubmission,
  trackButtonClick,
  trackBooking,
  trackFleetEnquiry,
  trackContactSubmission,
  trackCareerApplication,
  trackWhatsAppClick,
  trackPhoneCall,
  trackOutboundLink,
};

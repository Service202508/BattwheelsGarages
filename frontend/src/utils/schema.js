/**
 * JSON-LD Schema for LocalBusiness/AutomotiveBusiness
 */
export const getLocalBusinessSchema = () => ({
  "@context": "https://schema.org",
  "@type": "AutomotiveBusiness",
  "name": "Battwheels Garages",
  "description": "India's first no-towing-first EV service model. Onsite diagnosis and repair for 2W, 3W, 4W and commercial EVs.",
  "url": "https://battwheelsgarages.in",
  "logo": "https://battwheelsgarages.in/assets/battwheels-logo-new.png",
  "image": "https://battwheelsgarages.in/assets/battwheels-logo-new.png",
  "telephone": "+91-XXXXXXXXXX",
  "email": "contact@battwheelsgarages.in",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Delhi NCR",
    "addressRegion": "Delhi",
    "addressCountry": "IN"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "28.6139",
    "longitude": "77.2090"
  },
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": [
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ],
    "opens": "09:00",
    "closes": "23:00"
  },
  "priceRange": "$$",
  "servesCuisine": "EV Repair & Maintenance",
  "areaServed": [
    "Delhi NCR", "Mumbai", "Bangalore", "Hyderabad", "Chennai", 
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh"
  ],
  "sameAs": [
    "https://www.linkedin.com/company/battwheels-garages",
    "https://twitter.com/battwheelsgarages",
    "https://www.instagram.com/battwheelsgarages"
  ],
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "EV Services",
    "itemListElement": [
      {
        "@type": "Offer",
        "itemOffered": {
          "@type": "Service",
          "name": "Onsite EV Repair",
          "description": "Onsite diagnosis and repair for electric vehicles"
        }
      },
      {
        "@type": "Offer",
        "itemOffered": {
          "@type": "Service",
          "name": "EV Roadside Assistance",
          "description": "24/7 emergency roadside assistance for EVs"
        }
      },
      {
        "@type": "Offer",
        "itemOffered": {
          "@type": "Service",
          "name": "Fleet Maintenance",
          "description": "Comprehensive fleet maintenance programs for EV operators"
        }
      }
    ]
  }
});

/**
 * JSON-LD Schema for Service pages
 */
export const getServiceSchema = (service) => ({
  "@context": "https://schema.org",
  "@type": "Service",
  "name": service.title,
  "description": service.description || service.short_description,
  "provider": {
    "@type": "AutomotiveBusiness",
    "name": "Battwheels Garages",
    "url": "https://battwheelsgarages.in"
  },
  "areaServed": "India",
  "serviceType": "EV Repair and Maintenance"
});

/**
 * JSON-LD Schema for Blog posts
 */
export const getBlogSchema = (blog) => ({
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": blog.title,
  "description": blog.excerpt || blog.meta_desc,
  "image": blog.thumbnail_image || blog.og_image,
  "datePublished": blog.created_at || blog.published_at,
  "dateModified": blog.updated_at || blog.created_at,
  "author": {
    "@type": "Organization",
    "name": "Battwheels Garages"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Battwheels Garages",
    "logo": {
      "@type": "ImageObject",
      "url": "https://battwheelsgarages.in/assets/battwheels-logo-new.png"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": `https://battwheelsgarages.in/blog/${blog.slug}`
  }
});

/**
 * JSON-LD Schema for FAQ page
 */
export const getFAQSchema = (faqs) => ({
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": faqs.map(faq => ({
    "@type": "Question",
    "name": faq.question,
    "acceptedAnswer": {
      "@type": "Answer",
      "text": faq.answer
    }
  }))
});

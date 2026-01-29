// Company Info
export const companyInfo = {
  name: 'Battwheels Garages',
  tagline: 'Your 100% Onsite EV Issues Resolution Partner',
  phone: '+91 8076331607',
  email: 'service@battwheelsgarages.in',
  address: 'Plot No 157, Sector 28, Part-2, Bamnoli, Sector 28 Dwarka, New Delhi, Delhi, 110077',
  hours: 'Open 365 days • 09:00 AM – 11:00 PM',
  social: {
    facebook: '#',
    instagram: '#',
    linkedin: '#'
  }
};

// Stats - 2-Wheeler EVs (Scooters & Bikes)
export const stats = [
  { id: 1, value: '10000', label: 'EVs Serviced', suffix: '+' },
  { id: 2, value: '5000', label: 'Happy Customers', suffix: '+' },
  { id: 3, value: '50', label: 'OEM & Fleet Partners', suffix: '+' },
  { id: 4, value: '2', label: 'Avg Breakdown TAT', suffix: ' hrs' }
];

// Why Choose Us
export const whyChooseUs = [
  {
    id: 1,
    title: '100% Onsite First',
    description: 'We fix your EV at your site or on the road - wherever it is safe. No unnecessary towing means lower downtime and lower cost.',
    icon: 'MapPin'
  },
  {
    id: 2,
    title: 'EV-Only Expertise',
    description: 'Our engineers are trained specifically on EV motors, controllers, BMS, chargers, and high-voltage safety. No ICE distractions.',
    icon: 'Zap'
  },
  {
    id: 3,
    title: 'All Segments Covered',
    description: 'Complete support for 2W, 3W, 4W, and commercial EVs with specialized expertise for each category.',
    icon: 'Car'
  },
  {
    id: 4,
    title: 'Tech-Driven: Battwheels OS™',
    description: 'Track jobs in real-time, get digital job cards, and access GaragePROEV-style EV diagnostics - all integrated into Battwheels OS™.',
    icon: 'Monitor'
  }
];

// Service Categories
export const serviceCategories = [
  {
    id: 1,
    title: 'Periodic EV Service',
    description: 'Comprehensive health checks and maintenance for all EV segments',
    icon: 'Wrench',
    link: '/services/periodic'
  },
  {
    id: 2,
    title: 'EV Motor & Controller Repair',
    description: 'Expert diagnostics and repair for motors, controllers, and drivetrains',
    icon: 'Cpu',
    link: '/services/motor-controller'
  },
  {
    id: 3,
    title: 'Battery Health & BMS Diagnostics',
    description: 'Battery diagnostics, BMS troubleshooting, and high-voltage safety checks',
    icon: 'Battery',
    link: '/services/battery-bms'
  },
  {
    id: 4,
    title: 'EV Charger & Connector Repair',
    description: 'Charger diagnostics, connector repairs, and charging system troubleshooting',
    icon: 'Plug',
    link: '/services/charger'
  },
  {
    id: 5,
    title: 'Brakes, Tyres & Suspension',
    description: 'Regenerative braking, tyre services, and suspension maintenance for EVs',
    icon: 'CircleSlash',
    link: '/services/brakes-tyres'
  },
  {
    id: 6,
    title: 'Body, Paint & Crash Repairs',
    description: 'EV-safe body work, denting, painting with HV isolation protocols',
    icon: 'Paintbrush',
    link: '/services/body-paint'
  },
  {
    id: 7,
    title: 'Onsite Breakdown & Roadside Assistance',
    description: '24/7 emergency breakdown support with onsite diagnostics and repair',
    icon: 'AlertCircle',
    link: '/services/roadside'
  },
  {
    id: 8,
    title: 'Fleet Preventive Maintenance',
    description: 'Custom SLAs, uptime guarantees, and centralized fleet management',
    icon: 'ClipboardCheck',
    link: '/services/fleet'
  }
];

// Industries We Serve
export const industries = [
  {
    id: 1,
    title: 'EV OEMs',
    description: 'After-sales support, warranty management, and technical assistance for EV manufacturers',
    icon: 'Building'
  },
  {
    id: 2,
    title: 'Fleet Operators & Logistics',
    description: 'High-uptime maintenance solutions for delivery fleets and logistics companies',
    icon: 'Truck'
  },
  {
    id: 3,
    title: 'Battery-Swapping & Energy Operators',
    description: 'Technical support and integration with battery swap and charging infrastructure',
    icon: 'BatteryCharging'
  },
  {
    id: 4,
    title: 'Quick Commerce & Hyperlocal Delivery',
    description: 'Fast turnaround maintenance for high-frequency delivery operations',
    icon: 'Package'
  },
  {
    id: 5,
    title: 'Individual EV Owners',
    description: 'Reliable, transparent service for 2W, 3W, and 4W EV owners',
    icon: 'User'
  }
];

// Testimonials
export const testimonials = [
  {
    id: 1,
    name: 'MD. Abdul Aziz',
    designation: 'Fleet Manager',
    company: 'Logistics Corp',
    content: 'We are pleased to work with Battwheels team as our vehicle service or breakdown TAT is very low. We are getting proper service on time, and also, there is proper spare parts availability.',
    rating: 5
  },
  {
    id: 2,
    name: 'Diwakar',
    designation: 'Operations Head',
    company: 'E-Commerce Fleet',
    content: 'I am writing to thank you for the quality of service provided. We sincerely appreciate your efficient customer service and the way you conduct business. We will continue to recommend your services.',
    rating: 5
  },
  {
    id: 3,
    name: 'Sandeep Kumar Tiwari',
    designation: 'Director',
    company: 'GPS Solutions',
    content: 'Battwheels Garages has been very instrumental in supporting our GPS related on-field operations. We found Battwheels to be the best fit partner for after sales services.',
    rating: 5
  },
  {
    id: 4,
    name: 'Dipankar Panhera',
    designation: 'Product Manager',
    company: 'Mobility Platform',
    content: 'Roadside assistance with onsite resolution from Battwheels is a great addition for our customers. Perfect fit with our motto of simplifying the EV ownership journey.',
    rating: 5
  }
];

// FAQs
// FAQ Categories
export const faqCategories = [
  { id: 'general', name: 'General EV Service', icon: 'HelpCircle' },
  { id: 'breakdown', name: 'Breakdown, RSA & Uptime', icon: 'AlertTriangle' },
  { id: 'maintenance', name: 'Service, Maintenance & Warranty', icon: 'Wrench' },
  { id: 'booking', name: 'Booking, Pricing & Coverage', icon: 'Calendar' },
  { id: 'technical', name: 'Technical EV', icon: 'Cpu' },
  { id: 'fleet', name: 'Fleet & Enterprise', icon: 'Building' },
  { id: 'website', name: 'Website & Booking', icon: 'Globe' }
];

export const faqs = [
  // General EV Service FAQs
  {
    id: 1,
    category: 'general',
    question: 'What is Battwheels Garages and what services do you provide?',
    answer: 'Battwheels Garages is India\'s first no-towing-first EV service network focused on onsite diagnosis and repair for 2-wheelers, 3-wheelers, 4-wheelers and commercial EV fleets. We fix breakdowns, provide periodic service, run fleet uptime programs, and offer advanced EV diagnostics.'
  },
  {
    id: 2,
    category: 'general',
    question: 'Do you repair EVs onsite or do you tow the vehicle?',
    answer: 'Our model is simple: no towing first. We always try to diagnose and fix your EV onsite. Only if the issue truly requires workshop-level repair do we arrange controlled logistics.'
  },
  {
    id: 3,
    category: 'general',
    question: 'Which EV brands do you service?',
    answer: 'We service almost every major EV brand including Ather, Ola, TVS, Bajaj, Hero Electric, Revolt, Simple, Bounce, Piaggio, Chetak, Mahindra, Tata, MG, BYD, Euler Motors and many others.'
  },
  {
    id: 4,
    category: 'general',
    question: 'Do you offer doorstep EV repair services?',
    answer: 'Yes, we specialize in onsite EV repair. Our technicians come to your location with tools, spares and diagnostics.'
  },
  {
    id: 5,
    category: 'general',
    question: 'Are your technicians trained for EV high-voltage systems?',
    answer: 'Absolutely. Every Battwheels technician undergoes certified EV training covering battery systems, BMS, controllers, motors and CAN diagnostics.'
  },
  // Breakdown, RSA & Uptime FAQs
  {
    id: 6,
    category: 'breakdown',
    question: 'What should I do if my EV breaks down on the road?',
    answer: 'Just book a breakdown request through the website or call us. A technician is dispatched immediately to diagnose the issue onsite.'
  },
  {
    id: 7,
    category: 'breakdown',
    question: 'How fast does Battwheels respond to breakdown calls?',
    answer: 'Our average breakdown response time is 2 hours, depending on your city and traffic conditions.'
  },
  {
    id: 8,
    category: 'breakdown',
    question: 'What kind of issues can be fixed onsite?',
    answer: 'Most EV faults - including wiring issues, controller errors, throttle issues, brake faults, BMS resets, battery connector repairs and software calibrations - can be handled onsite.'
  },
  {
    id: 9,
    category: 'breakdown',
    question: 'Do you support EV fleets and delivery vehicles?',
    answer: 'Yes, fleet support is one of our core strengths. We maintain uptime programs for logistics, e-commerce and last-mile mobility fleets.'
  },
  {
    id: 10,
    category: 'breakdown',
    question: 'Do you provide 24/7 emergency EV assistance?',
    answer: 'Yes, we operate 365 days with 24/7 emergency response for fleets and premium customers.'
  },
  // Service, Maintenance & Warranty FAQs
  {
    id: 11,
    category: 'maintenance',
    question: 'Do you perform periodic service for EVs?',
    answer: 'Yes. We offer routine EV servicing, brake service, electrical checks, software diagnostics, tyre replacement and preventive maintenance packages.'
  },
  {
    id: 12,
    category: 'maintenance',
    question: 'Will my EV warranty remain valid?',
    answer: 'Our services do not interfere with OEM warranties. We follow brand-aligned procedures and standardized repair practices.'
  },
  {
    id: 13,
    category: 'maintenance',
    question: 'Do you use genuine parts for replacement?',
    answer: 'We use OEM-approved or high-quality compatible components that meet industry standards.'
  },
  {
    id: 14,
    category: 'maintenance',
    question: 'How often should an EV be serviced?',
    answer: 'Most EVs should undergo preventive service every 2,500–3,000 km or every 3 months, especially fleet vehicles.'
  },
  {
    id: 15,
    category: 'maintenance',
    question: 'Do you service commercial EVs like loaders, cargo vans or L5 autos?',
    answer: 'Yes. We repair and maintain L3/L5 autos, cargo EVs, loaders, delivery scooters and commercial four-wheelers.'
  },
  // Booking, Pricing & Coverage FAQs
  {
    id: 16,
    category: 'booking',
    question: 'How do I book an EV service with Battwheels?',
    answer: 'Simply use the Book Service form on our website or contact our fleet support team.'
  },
  {
    id: 17,
    category: 'booking',
    question: 'How much does an onsite EV service cost?',
    answer: 'Pricing depends on the vehicle category and issue type. Diagnostics charges are minimal, and most repairs are offered upfront with transparent pricing.'
  },
  {
    id: 18,
    category: 'booking',
    question: 'Which cities does Battwheels currently operate in?',
    answer: 'We operate in 11+ cities including Delhi, Noida, Gurugram, Bengaluru, Chennai, Hyderabad, Jaipur, Lucknow, Pune, Ulhasnagar and more.'
  },
  {
    id: 19,
    category: 'booking',
    question: 'Are there any hidden charges?',
    answer: 'No, all charges are shared transparently before starting the repair.'
  },
  {
    id: 20,
    category: 'booking',
    question: 'Do you offer subscription or AMC plans for fleets?',
    answer: 'Yes, we have customizable AMC and uptime assurance programs for fleet operators.'
  },
  // Technical EV FAQs
  {
    id: 21,
    category: 'technical',
    question: 'My EV is showing an error code. Can Battwheels fix it?',
    answer: 'Yes. Our advanced tools can read and reset error codes for most EV brands and diagnose underlying faults.'
  },
  {
    id: 22,
    category: 'technical',
    question: 'Can you fix battery issues onsite?',
    answer: 'Many BMS, connector and wiring-related issues can be fixed onsite. Deep battery repairs may require workshop handling.'
  },
  {
    id: 23,
    category: 'technical',
    question: 'My EV is not turning on. What should I do?',
    answer: 'This is usually due to fuse, wiring, controller or BMS issues. Book an inspection - 85% of such faults are fixed onsite.'
  },
  {
    id: 24,
    category: 'technical',
    question: 'Do you repair EV chargers and onboard chargers?',
    answer: 'We repair portable chargers, connectors, wiring failures, and charging-port issues.'
  },
  {
    id: 25,
    category: 'technical',
    question: 'Do you handle motor controller replacements and calibrations?',
    answer: 'Yes. We handle controller replacement, programming and motor alignment.'
  },
  // Fleet & Enterprise FAQs
  {
    id: 26,
    category: 'fleet',
    question: 'Do you offer uptime guarantees for fleets?',
    answer: 'Yes - our fleet programs provide 95%+ uptime, SLA-based operations and dedicated technician support.'
  },
  {
    id: 27,
    category: 'fleet',
    question: 'How do you support large EV fleets?',
    answer: 'We deploy mobile technicians, run night-shift maintenance, create service schedules and offer backend analytics on breakdown patterns.'
  },
  {
    id: 28,
    category: 'fleet',
    question: 'Can fleet operators integrate with Battwheels OS™?',
    answer: 'Yes. Fleets can access job tracking, technician updates, breakdown history and service logs through our digital platform.'
  },
  {
    id: 29,
    category: 'fleet',
    question: 'Do you offer bulk pricing for large fleets?',
    answer: 'Yes, fleet operators get customized pricing based on volume and service frequency.'
  },
  {
    id: 30,
    category: 'fleet',
    question: 'Do you support battery-swapping fleets?',
    answer: 'Absolutely. We regularly service swap-based e-rickshaws and commercial two-wheelers.'
  },
  {
    id: 31,
    category: 'fleet',
    question: 'Can Battwheels station technicians inside fleet hubs?',
    answer: 'Yes - we provide on-site stationed technicians for high-volume EV fleets.'
  },
  // Website & Booking FAQs
  {
    id: 32,
    category: 'website',
    question: 'Is online payment available for EV services?',
    answer: 'Yes, we support online and offline payment methods.'
  },
  {
    id: 33,
    category: 'website',
    question: 'Can I track my service request?',
    answer: 'Yes, once your booking is created, you\'ll receive real-time updates from our team.'
  },
  {
    id: 34,
    category: 'website',
    question: 'How do I contact support for urgent help?',
    answer: 'You can reach us via the website, WhatsApp, or the emergency helpline mentioned in the footer.'
  }
];

// EV Brands
export const evBrands = [
  'Ather Energy', 'Ola Electric', 'TVS', 'Bajaj', 'Hero Electric',
  'Revolt', 'Simple', 'Bounce', 'Chetak', 'Piaggio',
  'Mahindra', 'Tata', 'MG', 'BYD', 'Euler Motors'
];

// Blog Posts (Sample)
export const blogPosts = [
  {
    id: 1,
    title: 'How Often Should You Service Your EV Fleet?',
    excerpt: 'A comprehensive guide to preventive maintenance schedules for electric vehicle fleets to maximize uptime and minimize costs.',
    category: 'Fleet Ops',
    date: '2025-01-15',
    image: 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=600',
    slug: 'ev-fleet-service-schedule'
  },
  {
    id: 2,
    title: 'Common EV Motor Issues and How We Fix Them',
    excerpt: 'Understanding motor noise, overheating, and alignment problems in electric vehicles and our diagnostic approach.',
    category: 'EV Tech Deep Dive',
    date: '2025-01-10',
    image: 'https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=600',
    slug: 'ev-motor-issues-diagnostics'
  },
  {
    id: 3,
    title: 'Onsite vs. Workshop EV Repairs: What Fleets Should Know',
    excerpt: 'Comparing the benefits of onsite diagnostics and repair versus traditional workshop-based service for EV fleets.',
    category: 'Fleet Ops',
    date: '2025-01-05',
    image: 'https://images.unsplash.com/photo-1615906655593-ad0386982a0f?w=600',
    slug: 'onsite-vs-workshop-ev-repairs'
  }
];

// Subscription Plans
export const subscriptionPlans = [
  {
    id: 1,
    name: 'Starter',
    subtitle: 'For Individual EV Owners',
    price: '₹899',
    priceUnit: '/Month/Vehicle',
    annualPrice: '₹7,999',
    annualUnit: '/Annually/Vehicle',
    features: [
      'Coverage for 1 vehicle',
      '2 periodic services per year',
      '1 breakdown visit included',
      'Standard support',
      'Digital service history',
      'Basic diagnostics'
    ],
    cta: 'Get Started',
    popular: false
  },
  {
    id: 2,
    name: 'Fleet Essential',
    subtitle: 'For Small Fleets (5-20 vehicles)',
    price: '₹1,199',
    priceUnit: '/Month/Vehicle',
    annualPrice: '₹9,999',
    annualUnit: '/Annually/Vehicle',
    features: [
      'Coverage for up to 20 vehicles',
      'Unlimited periodic services',
      '5 breakdown visits per vehicle',
      'Priority support (4-hour response)',
      'Fleet dashboard access',
      'Preventive maintenance scheduling',
      'Centralized invoicing'
    ],
    cta: 'Contact Sales',
    popular: true
  },
  {
    id: 3,
    name: 'Fleet Pro',
    subtitle: 'For Large Fleets & OEM Programs',
    price: '₹1,399',
    priceUnit: '/Month/Vehicle',
    annualPrice: '₹10,999',
    annualUnit: '/Annually/Vehicle',
    features: [
      'Coverage for 20+ vehicles',
      'Unlimited periodic services',
      'Unlimited breakdown visits',
      'Dedicated service manager',
      'Custom SLAs and uptime guarantees',
      'Battwheels OS™ integration',
      'Telematics integration',
      'Monthly performance reports',
      'Onsite dedicated team option'
    ],
    cta: 'Schedule Demo',
    popular: false
  }
];
// Services by EV Type
export const servicesByType = [
  {
    id: 1,
    category: 'Electric 2-Wheelers',
    description: 'Specialized onsite diagnostics and repair for electric scooters and bikes',
    services: [
      'Battery diagnostics & repair',
      'Controller & motor troubleshooting',
      'Throttle & wiring issues',
      'Brake system maintenance',
      'Software updates & calibration',
      'Charging port repair'
    ],
    icon: 'Bike'
  },
  {
    id: 2,
    category: 'Electric 3-Wheelers',
    description: 'Fleet-grade service for e-rickshaws, cargo vehicles, and battery swapping models',
    services: [
      'E-rickshaw diagnostics',
      'Battery swapping model support',
      'Load carrier maintenance',
      'Fleet preventive maintenance',
      'Controller replacement',
      'Complete electrical overhaul'
    ],
    icon: 'TramFront'
  },
  {
    id: 3,
    category: 'Electric 4-Wheelers',
    description: 'Commercial & passenger EV service including fleet operations',
    services: [
      'Passenger EV diagnostics',
      'Commercial fleet maintenance',
      'Battery health monitoring',
      'HVAC & thermal management',
      'Advanced driver assistance systems',
      'Complete vehicle refurbishment'
    ],
    icon: 'Car'
  }
];

// Fleet Solutions
export const fleetSolutions = [
  {
    id: 1,
    title: 'AMC & SLA Contracts',
    description: 'Structured service agreements with guaranteed TAT and uptime SLAs for fleet operators',
    features: ['Predictable cost structure', 'Priority response', 'Dedicated service manager', 'Monthly reports'],
    icon: 'FileText'
  },
  {
    id: 2,
    title: 'Preventive Maintenance Programs',
    description: 'Scheduled inspections and maintenance to prevent breakdowns and maximize fleet uptime',
    features: ['Scheduled inspections', 'Health monitoring', 'Parts lifecycle tracking', 'Performance optimization'],
    icon: 'ClipboardCheck'
  },
  {
    id: 3,
    title: 'Dark Store & Spare Parts Logistics',
    description: 'Strategic parts inventory management ensuring critical components availability across regions',
    features: ['Regional spare parts hubs', 'Fast replacement parts', '24x7 availability', 'Optimized inventory'],
    icon: 'Package'
  },
  {
    id: 4,
    title: 'Fleet Audits & Digital Inspections',
    description: 'Comprehensive vehicle health audits with digital ticketing and gate-entry inspection systems',
    features: ['Digital inspection reports', 'Gate-entry checks', 'Parking ticketing', 'Fleet health scoring'],
    icon: 'Clipboard'
  }
];

// Why Battwheels - USP Comparison
export const comparisonData = [
  {
    feature: 'EV Specialization',
    traditional: 'ICE-focused, limited EV knowledge',
    battwheels: 'EV-Only expertise, no ICE distraction'
  },
  {
    feature: 'Service Model',
    traditional: 'Towing-first approach',
    battwheels: '85% onsite resolution, no towing dependency'
  },
  {
    feature: 'Fleet Understanding',
    traditional: 'Consumer-focused service',
    battwheels: 'Fleet-first DNA, uptime optimization'
  },
  {
    feature: 'Response Time',
    traditional: 'Hours to days',
    battwheels: 'Sub-2 hour response, faster MTTR'
  },
  {
    feature: 'Technician Training',
    traditional: 'ICE mechanics adapting',
    battwheels: 'EV-trained technicians & electricians'
  },
  {
    feature: 'Parts Availability',
    traditional: 'Generic network',
    battwheels: 'EV-specific dark stores & logistics'
  }
];

// Garage Models
export const garageModels = [
  {
    id: 1,
    model: 'COCO',
    fullForm: 'Company Owned Company Operated',
    description: 'Fully owned and operated service centers in strategic metros and high-density EV zones',
    benefits: ['Complete quality control', 'Direct operations', 'Rapid response', 'Brand standards'],
    icon: 'Building2'
  },
  {
    id: 2,
    model: 'FOCO',
    fullForm: 'Franchise Owned Company Operated',
    description: 'Franchised infrastructure with Battwheels operational management and service standards',
    benefits: ['Asset-light expansion', 'Local partnerships', 'Standardized service', 'Scalable model'],
    icon: 'Handshake'
  },
  {
    id: 3,
    model: 'FOFO',
    fullForm: 'Franchise Owned Franchise Operated',
    description: 'Fully franchised model for rapid pan-India coverage with certified training and support',
    benefits: ['Fastest expansion', 'Local entrepreneurship', 'Network effect', 'Geographic coverage'],
    icon: 'Network'
  }
];

// Core USPs
export const coreUSPs = [
  {
    id: 1,
    title: 'EV-Only Expertise',
    description: 'Zero distraction from ICE vehicles. Our technicians are trained exclusively in EV systems, electronics, and battery technology.',
    icon: 'Zap',
    stats: '100% EV-Focused'
  },
  {
    id: 2,
    title: 'Onsite Resolution Model',
    description: 'Diagnose and repair where the vehicle stops. 85% issues resolved on field without towing dependency.',
    icon: 'MapPin',
    stats: '85% Onsite Fix Rate'
  },
  {
    id: 3,
    title: 'Fleet-First DNA',
    description: 'Built for high-utilization fleets running 10-14 hours daily. We understand uptime is money for fleet operations.',
    icon: 'TrendingUp',
    stats: 'Max Uptime Guaranteed'
  },
  {
    id: 4,
    title: 'Faster MTTR',
    description: 'Mean Time to Repair optimized for fleet operations. Response within 2 hours, resolution on the same day.',
    icon: 'Clock',
    stats: '<2hr Response Time'
  },
  {
    id: 5,
    title: 'Pan-India Scalability',
    description: 'COCO, FOCO, and FOFO garage models enabling rapid geographic expansion and local presence.',
    icon: 'Map',
    stats: 'Pan-India Network'
  },
  {
    id: 6,
    title: 'Operational Credibility',
    description: 'Real operations, not marketing. ₹1 Crore revenue in Year 1 with a strong field engineering backbone.',
    icon: 'Shield',
    stats: '₹1Cr+ Revenue Y1'
  }
];

// Testimonials - B2B Focused
export const testimonials = [
  {
    id: 1,
    name: 'Sandeep Kumar Tiwari',
    role: 'Operations Head',
    company: 'Fleet Operations',
    content: 'Battwheels has been instrumental in supporting our field operations. Their onsite resolution model reduced our vehicle downtime by 60%. Best fit partner for aftersales services.',
    rating: 5
  },
  {
    id: 2,
    name: 'Dipankar Panhera',
    role: 'Product Manager',
    company: 'EV Mobility Platform',
    content: 'Roadside assistance with onsite resolution is a game-changer for our customers. Perfectly aligns with our motto of simplifying EV ownership journey.',
    rating: 5
  },
  {
    id: 3,
    name: 'MD. Abdul Aziz',
    role: 'Fleet Manager',
    company: 'Last Mile Delivery',
    content: 'Our vehicle breakdown TAT dropped significantly. Proper service on time with spare parts availability. No major issues since partnering with Battwheels.',
    rating: 5
  },
  {
    id: 4,
    name: 'Surender Sharma',
    role: 'CEO',
    company: 'EV Fleet Solutions',
    content: 'Focus on strengthening aftersales service. Battwheels initiative empowers and increases EV awareness. Strong operational partner.',
    rating: 5
  }
];

// Stats
export const stats = [
  { id: 1, value: '10000', label: 'Vehicles Serviced', suffix: '+' },
  { id: 2, value: '90', label: 'Onsite Resolution Rate', suffix: '%' },
  { id: 3, value: '2', label: 'Avg Response Time', suffix: 'hrs' },
  { id: 4, value: '100', label: 'EV-Only Focus', suffix: '%' }
];

// FAQs - B2B Focused
export const faqs = [
  {
    id: 1,
    question: 'What makes Battwheels different from traditional RSA providers?',
    answer: 'We are EV-only specialists with an onsite resolution model. Unlike traditional providers who tow-first, we diagnose and repair on the spot, achieving 85% onsite fix rates. This eliminates towing dependency and maximizes fleet uptime.'
  },
  {
    id: 2,
    question: 'Do you work with fleet operators and OEMs?',
    answer: 'Yes, B2B fleets are our core focus. We work with last-mile delivery fleets, mobility operators, battery swapping companies, and EV OEMs. We offer AMC/SLA contracts, preventive maintenance programs, and dedicated fleet solutions.'
  },
  {
    id: 3,
    question: 'What is your average response time?',
    answer: 'Our average response time is under 2 hours for emergency breakdowns. For AMC/SLA customers, we provide priority response with guaranteed TAT based on contract terms.'
  },
  {
    id: 4,
    question: 'Which EV types do you service?',
    answer: 'We service all EV categories: 2-wheelers (scooters, bikes), 3-wheelers (e-rickshaws, cargo vehicles, battery swapping models), and 4-wheelers (passenger and commercial EVs). We do not service ICE vehicles.'
  },
  {
    id: 5,
    question: 'How does your garage expansion model work?',
    answer: 'We operate through three models: COCO (Company Owned Company Operated), FOCO (Franchise Owned Company Operated), and FOFO (Franchise Owned Franchise Operated). This enables rapid pan-India scaling while maintaining service standards.'
  },
  {
    id: 6,
    question: 'What is included in your AMC contracts?',
    answer: 'AMC contracts include preventive maintenance, priority breakdown response, dedicated service manager, spare parts logistics, digital fleet audits, and monthly performance reports with guaranteed uptime SLAs.'
  }
];

// Partners/Clients
export const partners = [
  { id: 1, name: 'Zypp Electric', category: 'Last Mile Delivery' },
  { id: 2, name: 'Ather Energy', category: 'EV OEM' },
  { id: 3, name: 'Omega Seiki Mobility', category: 'EV OEM' },
  { id: 4, name: 'Sun Mobility', category: 'Battery Swapping' },
  { id: 5, name: 'Battery Smart', category: 'Battery Swapping' },
  { id: 6, name: 'Magenta Mobility', category: 'Fleet Operator' },
  { id: 7, name: 'Gentari', category: 'Charging Infrastructure' },
  { id: 8, name: 'Log9', category: 'Battery Technology' },
  { id: 9, name: 'Switchh', category: 'Mobility Platform' },
  { id: 10, name: 'Indofast', category: 'Logistics' }
];
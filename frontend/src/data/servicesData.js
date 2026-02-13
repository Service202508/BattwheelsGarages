// Detailed Services Data

export const periodicService = {
  title: 'Periodic EV Service',
  subtitle: 'Comprehensive health checks for all EV segments',
  description: 'Regular maintenance to keep your EV running at peak performance with reduced breakdowns and extended battery life.',
  segments: [
    {
      name: '2-Wheeler EVs',
      packages: [
        {
          name: 'Basic Health Check',
          price: 'Starting from ₹999',
          includes: [
            'Visual inspection',
            'Brake system check',
            'Tyre pressure and condition',
            'Software diagnostics',
            'Fastener tightening',
            'Lubrication points'
          ]
        },
        {
          name: 'Comprehensive Service',
          price: 'Starting from ₹1,999',
          includes: [
            'All Basic Health Check items',
            'Motor diagnostics',
            'Controller health check',
            'Battery BMS diagnostics',
            'Electrical wiring inspection',
            'Brake pad/shoe service',
            'Wheel alignment'
          ]
        }
      ]
    },
    {
      name: '3-Wheeler EVs (E-Rickshaws)',
      packages: [
        {
          name: 'Basic Health Check',
          price: 'Starting from ₹1,499',
          includes: [
            'Visual inspection',
            'Brake system check',
            'Tyre condition check',
            'Software diagnostics',
            'Load capacity assessment',
            'Fastener checks'
          ]
        },
        {
          name: 'Comprehensive Service',
          price: 'Starting from ₹2,999',
          includes: [
            'All Basic Health Check items',
            'Motor and controller diagnostics',
            'Battery pack health check',
            'Suspension check',
            'Body and chassis inspection',
            'Electrical system overhaul'
          ]
        }
      ]
    },
    {
      name: '4-Wheeler & Commercial EVs',
      packages: [
        {
          name: 'Basic Health Check',
          price: 'Starting from ₹2,499',
          includes: [
            'Multi-point inspection',
            'Brake system diagnostics',
            'Tyre rotation and balancing',
            'HVAC system check',
            'Software updates',
            'Battery cooling system check'
          ]
        },
        {
          name: 'Comprehensive Service',
          price: 'Starting from ₹4,999',
          includes: [
            'All Basic Health Check items',
            'Complete drivetrain diagnostics',
            'High-voltage system safety check',
            'BMS calibration',
            'Regenerative braking optimization',
            'Suspension and steering check',
            'Body electronics diagnostics'
          ]
        }
      ]
    }
  ]
};

export const motorControllerService = {
  title: 'EV Motor & Controller Repair',
  subtitle: 'Expert diagnostics and repair for EV drivetrains',
  description: 'Specialized service for motor alignment, bearing replacement, controller troubleshooting, and drivetrain repairs.',
  services: [
    'Motor noise and vibration diagnostics',
    'Motor overheating analysis',
    'Bearing replacement',
    'Rotor alignment',
    'Motor rewinding (if required)',
    'Controller diagnostics and replacement',
    'Hall sensor issues',
    'Throttle response problems',
    'Gearbox/drivetrain fixes',
    'Motor mounting and alignment'
  ],
  idealFor: ['All EV segments', 'Fleet operators', 'High-mileage vehicles']
};

export const batteryBMSService = {
  title: 'Battery Health & BMS Services',
  subtitle: 'Advanced battery diagnostics and management',
  description: 'Comprehensive battery pack analysis, BMS troubleshooting, and high-voltage safety protocols.',
  services: [
    'Battery health diagnostics',
    'State of Health (SOH) assessment',
    'BMS configuration and troubleshooting',
    'Cell balancing issues',
    'High-voltage safety checks',
    'Thermal management diagnostics',
    'Battery capacity testing',
    'Coordination with OEM for replacement',
    'Battery swap integration support'
  ],
  idealFor: ['Fleet operators', 'Battery swap platforms', 'OEMs', 'Individual owners']
};

export const chargerService = {
  title: 'EV Charger & Connector Repair',
  subtitle: 'Charging system diagnostics and repair',
  description: 'Expert service for onboard chargers, charging ports, connectors, and charging infrastructure.',
  services: [
    'Onboard charger diagnostics',
    'Charging port repair/replacement',
    'Connector and cable issues',
    'Slow charging troubleshooting',
    'AC/DC charging system checks',
    'Wallbox charger installation support',
    'Charging communication errors',
    'CCS/CHAdeMO/Type 2 connector service'
  ],
  idealFor: ['All EV owners', 'Charging infrastructure operators', 'Fleet depots']
};

export const brakesTyresService = {
  title: 'Brakes, Tyres & Suspension (EV-Optimized)',
  subtitle: 'Regenerative braking and chassis care',
  description: 'Specialized brake service considering regenerative braking systems, plus tyre and suspension maintenance.',
  services: [
    'Regenerative braking system diagnostics',
    'Brake pad/shoe replacement',
    'Disc machining and caliper overhaul',
    'Brake fluid check (if applicable)',
    'Tyre rotation and balancing',
    'Wheel alignment',
    'Tyre replacement',
    'Suspension diagnostics',
    'Shock absorber service'
  ],
  idealFor: ['High-usage fleets', 'City commute EVs', 'Commercial vehicles']
};

export const bodyPaintService = {
  title: 'Body, Paint & Crash Repairs',
  subtitle: 'EV-safe body work and collision repair',
  description: 'Professional denting, painting, and crash repairs with proper HV isolation and safety protocols.',
  services: [
    'Denting and panel beating',
    'Paint matching and refinishing',
    'Bumper repair/replacement',
    'Door and panel replacement',
    'High-voltage isolation during body work',
    'Battery area safety checks',
    'Accident damage assessment',
    'Insurance claim documentation support'
  ],
  idealFor: ['Accident repairs', 'Cosmetic restoration', 'Fleet refurbishment']
};

export const roadsideService = {
  title: 'Onsite Breakdown & Roadside Assistance',
  subtitle: '24/7 emergency EV breakdown support',
  description: 'Fast-response onsite diagnostics and comprehensive repair to get you back on the road with minimal downtime.',
  services: [
    '24/7 emergency response',
    'Onsite diagnostics with professional tools',
    'Critical electrical & electronics repairs on-site',
    'Motor, controller & BMS repairs on-site',
    'Mechanical repairs on-site',
    'Emergency charging/jump-start',
    'Tyre change',
    'Software reset and troubleshooting',
    'Towing only if absolutely necessary',
    'Live status updates via Battwheels OS™'
  ],
  idealFor: ['Individual owners', 'Fleet operators', 'Last-mile delivery companies']
};

export const fleetService = {
  title: 'Fleet Preventive Maintenance Programs',
  subtitle: 'Custom SLAs and uptime guarantees',
  description: 'Comprehensive fleet management solutions with preventive maintenance, centralized reporting, and dedicated support.',
  services: [
    'Custom SLA agreements',
    'Uptime guarantees with agreed TAT',
    'Preventive maintenance schedules',
    'Centralized invoicing and reporting',
    'Dedicated service manager',
    'Fleet health dashboards',
    'Telematics integration',
    'Spare parts inventory management',
    'On-site dedicated team options',
    'Driver training and support'
  ],
  idealFor: ['Fleet operators', 'OEMs', 'Logistics companies', 'Corporate fleets']
};
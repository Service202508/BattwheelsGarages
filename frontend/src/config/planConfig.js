const PLANS = {
  free_trial: {
    id: 'free_trial',
    name: 'Free Trial',
    price: 0,
    duration: '14 days',
    maxUsers: 3,
    evfiTokens: 10,
    limits: {
      tickets: 20,
      contacts: 10,
      estimates: 10,
      invoices: 10,
      items: 20,
    },
  },
  starter: {
    id: 'starter',
    name: 'Starter',
    price: 999,
    duration: 'monthly',
    maxUsers: 5,
    evfiTokens: 25,
    limits: {
      tickets: -1,
      contacts: -1,
      estimates: -1,
      invoices: -1,
      items: -1,
    },
  },
  professional: {
    id: 'professional',
    name: 'Professional',
    price: 2499,
    duration: 'monthly',
    maxUsers: 15,
    evfiTokens: 100,
    limits: {},
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    price: 4999,
    duration: 'monthly',
    maxUsers: -1,
    evfiTokens: -1,
    limits: {},
  },
};

// Module access matrix
// true = accessible, false = locked
const MODULE_ACCESS = {
  // HOME — always open
  '/home':                  { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/dashboard':             { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/insights':              { free_trial: true,  starter: true,  professional: true,  enterprise: true },

  // INTELLIGENCE
  '/ai-assistant':          { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/knowledge-brain':       { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/failure-intelligence':  { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/fault-tree-import':     { free_trial: false, starter: false, professional: true,  enterprise: true },

  // OPERATIONS
  '/tickets/new':           { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/tickets':               { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/vehicles':              { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/amc':                   { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/time-tracking':         { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/alerts':                { free_trial: true,  starter: true,  professional: true,  enterprise: true },

  // CONTACTS
  '/contacts':              { free_trial: true,  starter: true,  professional: true,  enterprise: true },

  // SALES
  '/estimates':             { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/sales-orders':          { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/invoices-enhanced':     { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/payments-received':     { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/invoice-settings':      { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/recurring-transactions':{ free_trial: false, starter: false, professional: true,  enterprise: true },
  '/credit-notes':          { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/delivery-challans':     { free_trial: false, starter: false, professional: true,  enterprise: true },

  // PURCHASES
  '/purchases':             { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/bills-enhanced':        { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/recurring-bills':       { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/vendor-credits':        { free_trial: false, starter: false, professional: true,  enterprise: true },

  // INVENTORY
  '/items':                 { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/composite-items':       { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/inventory-enhanced':    { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/stock-transfers':       { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/price-lists':           { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/inventory-adjustments': { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/serial-batch-tracking': { free_trial: false, starter: false, professional: true,  enterprise: true },

  // FINANCE
  '/expenses':              { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/recurring-expenses':    { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/banking':               { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/accountant':            { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/chart-of-accounts':     { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/journal-entries':       { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/trial-balance':         { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/opening-balances':      { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/period-locks':          { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/balance-sheet':         { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/profit-loss':           { free_trial: false, starter: false, professional: true,  enterprise: true },

  // REPORTS
  '/reports-advanced':      { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/reports':               { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/gst-reports':           { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/accounting':            { free_trial: false, starter: false, professional: true,  enterprise: true },

  // PROJECTS
  '/projects':              { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/project-tasks':         { free_trial: false, starter: false, professional: true,  enterprise: true },

  // HR & PAYROLL
  '/hr':                    { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/employees':             { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/attendance':            { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/leave':                 { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/payroll':               { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/productivity':          { free_trial: false, starter: false, professional: true,  enterprise: true },

  // SETTINGS
  '/subscription':          { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/team':                  { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/branding':              { free_trial: false, starter: false, professional: true,  enterprise: true },
  '/organization-settings': { free_trial: true,  starter: true,  professional: true,  enterprise: true },
  '/data-management':       { free_trial: false, starter: false, professional: false, enterprise: true },
  '/documents':             { free_trial: false, starter: true,  professional: true,  enterprise: true },
  '/customer-portal':       { free_trial: false, starter: false, professional: true,  enterprise: true },
};

// Module descriptions for upgrade prompts
const MODULE_DESCRIPTIONS = {
  '/knowledge-brain': {
    title: 'EVFI Knowledge Brain',
    description: 'Access the collective diagnostic intelligence from thousands of EV repairs. Search symptoms, browse solutions, and learn from real-world repair data.',
    minPlan: 'starter',
  },
  '/failure-intelligence': {
    title: 'Failure Intelligence Dashboard',
    description: 'Deep analytics on failure patterns, trending issues, and predictive insights across your fleet. Identify recurring problems before they become costly.',
    minPlan: 'professional',
  },
  '/fault-tree-import': {
    title: 'Fault Tree Import',
    description: 'Import and manage fault tree analysis data for structured diagnostic workflows and root cause identification.',
    minPlan: 'professional',
  },
  '/amc': {
    title: 'AMC Management',
    description: 'Manage annual maintenance contracts, track renewals, automate billing cycles, and never miss a service deadline for your customers.',
    minPlan: 'starter',
  },
  '/time-tracking': {
    title: 'Time Tracking',
    description: 'Track technician hours, monitor job durations, and optimize workshop productivity with real-time time logging.',
    minPlan: 'professional',
  },
  '/sales-orders': {
    title: 'Sales Orders',
    description: 'Create and manage sales orders, track fulfillment status, and convert orders to invoices seamlessly.',
    minPlan: 'starter',
  },
  '/recurring-transactions': {
    title: 'Recurring Invoices',
    description: 'Automate recurring billing for AMC customers, fleet contracts, and repeat services. Set it once, invoice automatically.',
    minPlan: 'professional',
  },
  '/credit-notes': {
    title: 'Credit Notes',
    description: 'Issue credit notes for returns, adjustments, and refunds. Automatically updates accounting and GST reports.',
    minPlan: 'starter',
  },
  '/delivery-challans': {
    title: 'Delivery Challans',
    description: 'Generate delivery challans for parts dispatch, track deliveries, and convert to invoices on receipt.',
    minPlan: 'professional',
  },
  '/invoice-settings': {
    title: 'Invoice Automation',
    description: 'Configure automatic invoice generation, numbering sequences, payment reminders, and late fee policies.',
    minPlan: 'professional',
  },
  '/purchases': {
    title: 'Purchase Orders',
    description: 'Create purchase orders for spare parts and supplies, track vendor deliveries, and manage procurement.',
    minPlan: 'starter',
  },
  '/bills-enhanced': {
    title: 'Bills & Payables',
    description: 'Record vendor bills, track payment due dates, and manage accounts payable with automatic journal entries.',
    minPlan: 'starter',
  },
  '/recurring-bills': {
    title: 'Recurring Bills',
    description: 'Automate recurring vendor payments for rent, utilities, and regular supplies.',
    minPlan: 'professional',
  },
  '/vendor-credits': {
    title: 'Vendor Credits',
    description: 'Track credits from vendors for returns and adjustments. Apply credits against future bills.',
    minPlan: 'professional',
  },
  '/composite-items': {
    title: 'Composite Items',
    description: 'Bundle multiple parts into kits and service packages. Track components and auto-calculate pricing.',
    minPlan: 'professional',
  },
  '/inventory-enhanced': {
    title: 'Stock Management',
    description: 'Track stock levels across warehouses, set reorder points, and get low-stock alerts before you run out.',
    minPlan: 'starter',
  },
  '/stock-transfers': {
    title: 'Stock Transfers',
    description: 'Transfer inventory between warehouses and service centers. Track in-transit stock.',
    minPlan: 'professional',
  },
  '/price-lists': {
    title: 'Price Lists',
    description: 'Create multiple price lists for different customer segments, bulk buyers, and seasonal pricing.',
    minPlan: 'professional',
  },
  '/inventory-adjustments': {
    title: 'Inventory Adjustments',
    description: 'Record stock adjustments for damages, theft, or stock-take corrections with automatic journal entries.',
    minPlan: 'starter',
  },
  '/serial-batch-tracking': {
    title: 'Serial & Batch Tracking',
    description: 'Track individual battery serial numbers and part batches for warranty claims and recall management.',
    minPlan: 'professional',
  },
  '/expenses': {
    title: 'Expense Tracking',
    description: 'Record and categorize workshop expenses, attach receipts, and track spending by category.',
    minPlan: 'starter',
  },
  '/recurring-expenses': {
    title: 'Recurring Expenses',
    description: 'Automate recurring expense entries for rent, salaries, and regular operational costs.',
    minPlan: 'professional',
  },
  '/banking': {
    title: 'Banking & Reconciliation',
    description: 'Connect bank accounts, reconcile transactions, and maintain accurate cash flow records.',
    minPlan: 'professional',
  },
  '/accountant': {
    title: 'Accountant Dashboard',
    description: 'Comprehensive accounting overview with trial balance, journal entries, and financial statements.',
    minPlan: 'professional',
  },
  '/chart-of-accounts': {
    title: 'Chart of Accounts',
    description: 'Manage your complete chart of accounts for organized financial tracking and reporting.',
    minPlan: 'starter',
  },
  '/journal-entries': {
    title: 'Journal Entries',
    description: 'Create manual journal entries for adjustments, accruals, and complex accounting transactions.',
    minPlan: 'professional',
  },
  '/trial-balance': {
    title: 'Trial Balance',
    description: 'Verify accounting accuracy with a complete trial balance report of all account balances.',
    minPlan: 'professional',
  },
  '/opening-balances': {
    title: 'Opening Balances',
    description: 'Set opening balances for accounts when migrating from another system or starting a new fiscal year.',
    minPlan: 'professional',
  },
  '/period-locks': {
    title: 'Period Locks',
    description: 'Lock accounting periods to prevent unauthorized changes to finalized financial data.',
    minPlan: 'professional',
  },
  '/balance-sheet': {
    title: 'Balance Sheet',
    description: 'View your complete financial position — assets, liabilities, and equity at any point in time.',
    minPlan: 'professional',
  },
  '/profit-loss': {
    title: 'Profit & Loss Statement',
    description: 'Track revenue, expenses, and profitability. Export for CA filing and business planning.',
    minPlan: 'professional',
  },
  '/reports': {
    title: 'Financial Reports',
    description: 'Comprehensive P&L, Balance Sheet, AR/AP Aging, Sales Reports, and SLA analytics.',
    minPlan: 'professional',
  },
  '/reports-advanced': {
    title: 'Analytics Dashboard',
    description: 'Visual business intelligence — revenue trends, customer analytics, sales funnel, and payment insights.',
    minPlan: 'starter',
  },
  '/gst-reports': {
    title: 'GST Returns',
    description: 'Auto-generate GSTR-1, GSTR-3B with HSN validation. Export-ready for GST portal filing.',
    minPlan: 'starter',
  },
  '/accounting': {
    title: 'Accounting Overview',
    description: 'Full accounting module with double-entry ledger, reconciliation, and financial reporting.',
    minPlan: 'professional',
  },
  '/hr': {
    title: 'HR Dashboard',
    description: 'Manage your workshop team — employee profiles, departments, designations, and performance overview.',
    minPlan: 'professional',
  },
  '/employees': {
    title: 'Employee Management',
    description: 'Complete employee records, documents, salary structure, and employment history.',
    minPlan: 'professional',
  },
  '/attendance': {
    title: 'Attendance Tracking',
    description: 'Daily attendance with check-in/check-out, overtime tracking, and monthly attendance reports.',
    minPlan: 'professional',
  },
  '/leave': {
    title: 'Leave Management',
    description: 'Leave policies, applications, approvals, and balance tracking for your entire team.',
    minPlan: 'professional',
  },
  '/payroll': {
    title: 'Payroll Processing',
    description: 'Monthly salary computation with attendance, deductions, PF/ESI, and payslip generation.',
    minPlan: 'professional',
  },
  '/productivity': {
    title: 'Productivity Dashboard',
    description: 'Track team productivity metrics, technician efficiency, and workshop utilization rates.',
    minPlan: 'professional',
  },
  '/projects': {
    title: 'Project Management',
    description: 'Organize large fleet maintenance or installation projects with tasks, timelines, and budgets.',
    minPlan: 'professional',
  },
  '/project-tasks': {
    title: 'Project Tasks',
    description: 'Break down projects into actionable tasks, assign to team members, and track progress.',
    minPlan: 'professional',
  },
  '/branding': {
    title: 'Custom Branding',
    description: 'Add your logo, brand colors, and custom PDF headers. White-label invoices and estimates.',
    minPlan: 'professional',
  },
  '/data-management': {
    title: 'Data Management',
    description: 'Import/export data, manage backups, and perform data operations at enterprise scale.',
    minPlan: 'enterprise',
  },
  '/documents': {
    title: 'Document Management',
    description: 'Upload and organize service documents, warranty cards, and vehicle records.',
    minPlan: 'starter',
  },
  '/customer-portal': {
    title: 'Customer Portal',
    description: 'Give your customers a branded portal to track service status, view invoices, and approve estimates.',
    minPlan: 'professional',
  },
};

// Normalize plan ID — treats "free" as "free_trial" for backward compat
function normalizePlan(planId) {
  if (!planId || planId === 'free') return 'free_trial';
  return planId.toLowerCase();
}

export function isModuleAccessible(path, planId) {
  const access = MODULE_ACCESS[path];
  if (!access) return true; // unlisted modules are accessible
  return access[normalizePlan(planId)] || false;
}

export function getMinPlan(path) {
  const desc = MODULE_DESCRIPTIONS[path];
  return desc ? desc.minPlan : 'free_trial';
}

export function getModuleDescription(path) {
  return MODULE_DESCRIPTIONS[path] || null;
}

export function getPlanDetails(planId) {
  return PLANS[normalizePlan(planId)] || PLANS.free_trial;
}

export function getRecordLimit(planId, resource) {
  const plan = PLANS[normalizePlan(planId)];
  if (!plan || !plan.limits) return -1;
  const limit = plan.limits[resource];
  return limit !== undefined ? limit : -1;
}

export { PLANS, MODULE_ACCESS, MODULE_DESCRIPTIONS };

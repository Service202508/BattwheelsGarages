import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Building2, Users, Zap, Shield, BarChart3, Globe, ArrowRight, Check, ChevronRight } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SaaSLanding = () => {
  const navigate = useNavigate();
  const [showSignup, setShowSignup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
    industry_type: 'ev_garage',
    city: '',
    state: ''
  });

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "AI-Powered Diagnostics",
      description: "Intelligent fault detection and resolution recommendations for EV repairs"
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Complete ERP Suite",
      description: "Invoicing, inventory, HR, and operations in one unified platform"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Multi-User Access",
      description: "Role-based access for technicians, managers, and administrators"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Enterprise Security",
      description: "Complete data isolation between organizations with encryption"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Zoho Books Integration",
      description: "Seamless sync with Zoho Books for accounting and invoicing"
    },
    {
      icon: <Building2 className="w-6 h-6" />,
      title: "Multi-Location Support",
      description: "Manage multiple workshops from a single dashboard"
    }
  ];

  const plans = [
    {
      name: "Starter",
      price: "Free",
      period: "14-day trial",
      features: ["Up to 3 users", "100 tickets/month", "Basic reports", "Email support"],
      cta: "Start Free Trial",
      highlighted: false
    },
    {
      name: "Professional",
      price: "₹4,999",
      period: "/month",
      features: ["Up to 15 users", "Unlimited tickets", "Zoho Books sync", "AI diagnostics", "Priority support"],
      cta: "Get Started",
      highlighted: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "contact us",
      features: ["Unlimited users", "Custom integrations", "Dedicated support", "On-premise option", "SLA guarantee"],
      cta: "Contact Sales",
      highlighted: false
    }
  ];

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/organizations/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Organization created successfully!');
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('organization', JSON.stringify(data.organization));
        navigate('/admin/dashboard');
      } else {
        toast.error(data.detail || 'Signup failed');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-slate-900/80 backdrop-blur-lg border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">Battwheels OS</span>
          </div>
          <div className="flex items-center space-x-6">
            <a href="#features" className="text-slate-300 hover:text-white transition">Features</a>
            <a href="#pricing" className="text-slate-300 hover:text-white transition">Pricing</a>
            <button
              onClick={() => navigate('/login')}
              className="text-slate-300 hover:text-white transition"
            >
              Sign In
            </button>
            <button
              onClick={() => setShowSignup(true)}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-2 rounded-lg font-medium transition"
            >
              Start Free Trial
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center bg-emerald-500/10 border border-emerald-500/30 rounded-full px-4 py-2 mb-8">
            <span className="text-emerald-400 text-sm font-medium">New: AI-Powered Failure Intelligence</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            The Complete ERP for
            <span className="text-emerald-400"> EV Workshops</span>
          </h1>
          
          <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-12">
            Manage your electric vehicle service center with AI-powered diagnostics, 
            seamless Zoho Books integration, and enterprise-grade multi-tenant architecture.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => setShowSignup(true)}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-8 py-4 rounded-xl font-semibold text-lg flex items-center gap-2 transition shadow-lg shadow-emerald-500/25"
            >
              Start 14-Day Free Trial
              <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/login')}
              className="border border-slate-600 hover:border-slate-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition"
            >
              Sign In to Your Account
            </button>
          </div>
          
          <p className="text-slate-400 mt-6 text-sm">
            No credit card required • Free 14-day trial • Cancel anytime
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Everything You Need to Run Your Workshop
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              From service tickets to payroll, we've got you covered with a complete suite of tools.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <div
                key={idx}
                className="bg-slate-800/80 border border-slate-700/50 rounded-2xl p-6 hover:border-emerald-500/50 transition group"
              >
                <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 mb-4 group-hover:bg-emerald-500/20 transition">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-slate-400 text-lg">
              Choose the plan that fits your workshop size
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans.map((plan, idx) => (
              <div
                key={idx}
                className={`rounded-2xl p-8 ${
                  plan.highlighted
                    ? 'bg-emerald-500 text-white ring-4 ring-emerald-500/30'
                    : 'bg-slate-800 border border-slate-700'
                }`}
              >
                <h3 className={`text-xl font-semibold mb-2 ${plan.highlighted ? 'text-white' : 'text-white'}`}>
                  {plan.name}
                </h3>
                <div className="mb-6">
                  <span className={`text-4xl font-bold ${plan.highlighted ? 'text-white' : 'text-white'}`}>
                    {plan.price}
                  </span>
                  <span className={`${plan.highlighted ? 'text-emerald-100' : 'text-slate-400'}`}>
                    {plan.period}
                  </span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="flex items-center gap-2">
                      <Check className={`w-5 h-5 ${plan.highlighted ? 'text-white' : 'text-emerald-400'}`} />
                      <span className={plan.highlighted ? 'text-emerald-50' : 'text-slate-300'}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => setShowSignup(true)}
                  className={`w-full py-3 rounded-xl font-semibold transition ${
                    plan.highlighted
                      ? 'bg-white text-emerald-600 hover:bg-emerald-50'
                      : 'bg-emerald-500 text-white hover:bg-emerald-600'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-emerald-500">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Workshop?
          </h2>
          <p className="text-emerald-100 text-lg mb-8">
            Join hundreds of EV service centers already using Battwheels OS
          </p>
          <button
            onClick={() => setShowSignup(true)}
            className="bg-white text-emerald-600 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-emerald-50 transition inline-flex items-center gap-2"
          >
            Get Started Now
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-slate-900 border-t border-slate-800">
        <div className="max-w-7xl mx-auto text-center text-slate-400">
          <p>© 2026 Battwheels Services Private Limited. All rights reserved.</p>
        </div>
      </footer>

      {/* Signup Modal */}
      {showSignup && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 rounded-2xl max-w-md w-full p-8 border border-slate-700 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">Create Your Organization</h2>
              <button
                onClick={() => setShowSignup(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Organization Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., Mumbai EV Service Center"
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Your Name
                </label>
                <input
                  type="text"
                  name="admin_name"
                  value={formData.admin_name}
                  onChange={handleInputChange}
                  required
                  placeholder="John Doe"
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  name="admin_email"
                  value={formData.admin_email}
                  onChange={handleInputChange}
                  required
                  placeholder="you@company.com"
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  name="admin_password"
                  value={formData.admin_password}
                  onChange={handleInputChange}
                  required
                  minLength={6}
                  placeholder="Min 6 characters"
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    placeholder="Mumbai"
                    className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    State
                  </label>
                  <input
                    type="text"
                    name="state"
                    value={formData.state}
                    onChange={handleInputChange}
                    placeholder="Maharashtra"
                    className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-3 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    Create Organization
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
              
              <p className="text-center text-slate-400 text-sm">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setShowSignup(false);
                    navigate('/login');
                  }}
                  className="text-emerald-400 hover:text-emerald-300"
                >
                  Sign in
                </button>
              </p>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SaaSLanding;

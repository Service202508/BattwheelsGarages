/**
 * Marketplace Login - Phone OTP Based Authentication
 */
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useMarketplace } from '../../context/MarketplaceContext';
import {
  Phone,
  ArrowRight,
  Shield,
  Zap,
  Package,
  Truck,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const MarketplaceLogin = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sendOTP, verifyOTP, isAuthenticated } = useMarketplace();
  
  const [step, setStep] = useState('phone'); // phone, otp
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [debugOtp, setDebugOtp] = useState(''); // For testing

  const redirectTo = location.state?.from || '/marketplace';

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectTo);
    }
  }, [isAuthenticated, navigate, redirectTo]);

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await sendOTP(phone);
      if (result.success) {
        setStep('otp');
        // For testing - remove in production
        if (result.debug_otp) {
          setDebugOtp(result.debug_otp);
        }
      } else {
        setError(result.detail || 'Failed to send OTP');
      }
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await verifyOTP(phone, otp);
      if (result.success) {
        navigate(redirectTo);
      } else {
        setError(result.detail || 'Invalid OTP');
      }
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Helmet>
        <title>Login | Battwheels Marketplace</title>
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full">
          {/* Logo/Brand */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-[#12B76A]/10 rounded-2xl mb-4">
              <Zap className="w-8 h-8 text-[#12B76A]" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Welcome to Marketplace</h1>
            <p className="text-gray-600 mt-2">Sign in to access exclusive pricing and order parts</p>
          </div>

          {/* Login Card */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {step === 'phone' ? (
              <form onSubmit={handleSendOTP}>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2 flex items-center gap-1 text-gray-500">
                      <Phone className="w-5 h-5" />
                      <span className="text-sm font-medium">+91</span>
                    </div>
                    <Input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                      placeholder="98765 43210"
                      className="pl-24 py-6 text-lg"
                      required
                      maxLength={10}
                      pattern="[0-9]{10}"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    We&apos;ll send you a one-time password via SMS
                  </p>
                </div>

                <Button
                  type="submit"
                  disabled={loading || phone.length !== 10}
                  className="w-full bg-[#12B76A] hover:bg-[#0F9F5F] text-white py-6 text-lg"
                >
                  {loading ? 'Sending...' : 'Get OTP'}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP}>
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Enter OTP
                    </label>
                    <button
                      type="button"
                      onClick={() => setStep('phone')}
                      className="text-sm text-[#12B76A] hover:underline"
                    >
                      Change Number
                    </button>
                  </div>
                  <Input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="Enter 6-digit OTP"
                    className="py-6 text-lg text-center tracking-widest font-mono"
                    required
                    maxLength={6}
                    autoFocus
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    OTP sent to +91 {phone}
                  </p>
                  
                  {/* Debug OTP - Remove in production */}
                  {debugOtp && (
                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
                      Debug OTP: <span className="font-mono font-bold">{debugOtp}</span>
                      <br />
                      <span className="text-[10px]">(Remove in production)</span>
                    </div>
                  )}
                </div>

                <Button
                  type="submit"
                  disabled={loading || otp.length !== 6}
                  className="w-full bg-[#12B76A] hover:bg-[#0F9F5F] text-white py-6 text-lg"
                >
                  {loading ? 'Verifying...' : 'Verify & Login'}
                  <CheckCircle className="w-5 h-5 ml-2" />
                </Button>

                <button
                  type="button"
                  onClick={handleSendOTP}
                  disabled={loading}
                  className="w-full mt-4 text-sm text-gray-600 hover:text-[#12B76A]"
                >
                  Didn&apos;t receive OTP? Resend
                </button>
              </form>
            )}
          </div>

          {/* Benefits */}
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-900 text-center mb-4">
              Why create an account?
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="w-10 h-10 bg-[#12B76A]/10 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Package className="w-5 h-5 text-[#12B76A]" />
                </div>
                <p className="text-xs text-gray-600">Track Orders</p>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 bg-[#12B76A]/10 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Shield className="w-5 h-5 text-[#12B76A]" />
                </div>
                <p className="text-xs text-gray-600">Fleet Pricing</p>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 bg-[#12B76A]/10 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Truck className="w-5 h-5 text-[#12B76A]" />
                </div>
                <p className="text-xs text-gray-600">Fast Checkout</p>
              </div>
            </div>
          </div>

          {/* Continue as Guest */}
          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/marketplace')}
              className="text-sm text-gray-600 hover:text-[#12B76A]"
            >
              Continue browsing without login →
            </button>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
};

export default MarketplaceLogin;

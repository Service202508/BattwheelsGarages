/**
 * Checkout Page - Real Razorpay Integration + COD Payment Options
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { useMarketplace } from '../../context/MarketplaceContext';
import { useToast } from '../../hooks/use-toast';
import {
  CreditCard,
  Truck,
  MapPin,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  Package,
  Shield,
  Banknote,
  Loader2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const Checkout = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const {
    cart,
    getCartTotal,
    clearCart,
    user
  } = useMarketplace();

  const [loading, setLoading] = useState(false);
  const [razorpayLoaded, setRazorpayLoaded] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: Address, 2: Payment, 3: Confirmation
  const [paymentMethod, setPaymentMethod] = useState('razorpay');
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [razorpayConfig, setRazorpayConfig] = useState(null);

  const [address, setAddress] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    email: user?.email || '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    pincode: '',
    gst_number: ''
  });

  const subtotal = getCartTotal();
  const shipping = subtotal >= 2000 ? 0 : 99;
  const total = subtotal + shipping;

  // Load Razorpay SDK
  useEffect(() => {
    const loadRazorpay = async () => {
      if (window.Razorpay) {
        setRazorpayLoaded(true);
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      script.onload = () => setRazorpayLoaded(true);
      script.onerror = () => {
        console.error('Failed to load Razorpay SDK');
        setError('Failed to load payment gateway. Please try again.');
      };
      document.body.appendChild(script);
    };

    loadRazorpay();

    // Fetch Razorpay config
    const fetchConfig = async () => {
      try {
        const response = await fetch(`${API_URL}/api/payments/config`);
        if (response.ok) {
          const config = await response.json();
          setRazorpayConfig(config);
        }
      } catch (err) {
        console.error('Failed to fetch payment config:', err);
      }
    };

    fetchConfig();
  }, []);

  // Redirect if cart is empty
  if (cart.length === 0 && !orderSuccess) {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Your Cart is Empty</h1>
            <Button
              onClick={() => navigate('/marketplace')}
              className="bg-[#12B76A] hover:bg-[#0F9F5F]"
            >
              Browse Products
            </Button>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  const handleAddressSubmit = (e) => {
    e.preventDefault();
    if (!address.name || !address.phone || !address.address_line1 || !address.city || !address.state || !address.pincode) {
      setError('Please fill in all required fields');
      return;
    }
    setError('');
    setStep(2);
  };

  const initiateRazorpayPayment = async () => {
    if (!razorpayLoaded || !razorpayConfig) {
      setError('Payment gateway is loading. Please wait...');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Create order on backend
      const orderResponse = await fetch(`${API_URL}/api/payments/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: total,
          currency: 'INR',
          items: cart.map(item => ({
            product_id: item.id,
            name: item.name,
            quantity: item.quantity,
            price: item.final_price,
            sku: item.sku
          })),
          customer_name: address.name,
          customer_email: address.email || '',
          customer_phone: address.phone,
          shipping_address: `${address.address_line1}, ${address.address_line2 || ''}, ${address.city}, ${address.state} - ${address.pincode}`
        })
      });

      if (!orderResponse.ok) {
        const errorData = await orderResponse.json();
        throw new Error(errorData.detail || 'Failed to create order');
      }

      const orderData = await orderResponse.json();

      // Initialize Razorpay checkout
      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: razorpayConfig.name,
        description: razorpayConfig.description,
        image: razorpayConfig.image,
        order_id: orderData.order_id,
        handler: async function (response) {
          // Verify payment on backend
          try {
            const verifyResponse = await fetch(`${API_URL}/api/payments/verify-payment`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              })
            });

            if (verifyResponse.ok) {
              const result = await verifyResponse.json();
              setOrderSuccess({
                order_number: response.razorpay_order_id,
                payment_id: response.razorpay_payment_id,
                subtotal: subtotal,
                shipping_charge: shipping,
                total: total,
                estimated_delivery: '3-5 business days'
              });
              clearCart();
              setStep(3);
              toast({
                title: "Payment Successful!",
                description: "Your order has been placed successfully.",
              });
            } else {
              throw new Error('Payment verification failed');
            }
          } catch (err) {
            setError('Payment verification failed. Please contact support.');
          }
        },
        prefill: {
          name: address.name,
          email: address.email,
          contact: address.phone
        },
        notes: {
          shipping_address: `${address.address_line1}, ${address.city}, ${address.state} - ${address.pincode}`
        },
        theme: {
          color: '#12B76A'
        },
        modal: {
          ondismiss: function() {
            setLoading(false);
          }
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.on('payment.failed', function (response) {
        setError(`Payment failed: ${response.error.description}`);
        setLoading(false);
      });
      razorpay.open();

    } catch (err) {
      setError(err.message || 'Failed to initiate payment');
      setLoading(false);
    }
  };

  const handleCODOrder = async () => {
    setLoading(true);
    setError('');

    try {
      // Create COD order
      const orderResponse = await fetch(`${API_URL}/api/marketplace/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: cart.map(item => ({
            product_id: item.id,
            quantity: item.quantity
          })),
          shipping_address: {
            name: address.name,
            phone: address.phone,
            email: address.email,
            address: `${address.address_line1}, ${address.address_line2 || ''}, ${address.city}, ${address.state} - ${address.pincode}`,
            pincode: address.pincode
          },
          payment_method: 'cod'
        })
      });

      if (orderResponse.ok) {
        const result = await orderResponse.json();
        setOrderSuccess({
          order_number: result.order_number || result.id,
          subtotal: subtotal,
          shipping_charge: shipping,
          total: total,
          estimated_delivery: result.estimated_delivery || '3-5 business days'
        });
        clearCart();
        setStep(3);
        toast({
          title: "Order Placed!",
          description: "Your COD order has been placed successfully.",
        });
      } else {
        const errorData = await orderResponse.json();
        throw new Error(errorData.detail || 'Failed to place order');
      }
    } catch (err) {
      setError(err.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  const handlePlaceOrder = async () => {
    if (paymentMethod === 'razorpay') {
      await initiateRazorpayPayment();
    } else {
      await handleCODOrder();
    }
  };

  // Order Success Screen
  if (step === 3 && orderSuccess) {
    return (
      <>
        <Helmet>
          <title>Order Confirmed | Battwheels Marketplace</title>
        </Helmet>
        <Header />
        <main className="min-h-screen bg-gray-50 py-12">
          <div className="container mx-auto px-4">
            <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
              <div className="w-20 h-20 bg-[#12B76A]/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-[#12B76A]" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Order Placed Successfully!</h1>
              <p className="text-gray-600 mb-6">
                Thank you for your order. We&apos;ll send you a confirmation shortly.
              </p>

              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-gray-500">Order Number</p>
                <p className="text-xl font-mono font-bold text-gray-900">{orderSuccess.order_number}</p>
                {orderSuccess.payment_id && (
                  <p className="text-xs text-gray-400 mt-1">Payment ID: {orderSuccess.payment_id}</p>
                )}
              </div>

              <div className="text-left border-t border-gray-200 pt-6">
                <h3 className="font-semibold text-gray-900 mb-4">Order Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Items Total</span>
                    <span>₹{orderSuccess.subtotal?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Shipping</span>
                    <span>{orderSuccess.shipping_charge === 0 ? 'FREE' : `₹${orderSuccess.shipping_charge}`}</span>
                  </div>
                  <div className="flex justify-between font-bold text-base pt-2 border-t">
                    <span>Total</span>
                    <span>₹{orderSuccess.total?.toLocaleString()}</span>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <Truck className="w-4 h-4 inline mr-1" />
                    Estimated Delivery: {orderSuccess.estimated_delivery}
                  </p>
                </div>

                {paymentMethod === 'cod' && (
                  <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                    <p className="text-sm text-yellow-700">
                      <Banknote className="w-4 h-4 inline mr-1" />
                      Pay ₹{orderSuccess.total?.toLocaleString()} on delivery
                    </p>
                  </div>
                )}
              </div>

              <div className="flex gap-4 mt-8">
                <Button
                  variant="outline"
                  onClick={() => navigate('/marketplace')}
                  className="flex-1"
                >
                  Continue Shopping
                </Button>
                <Button
                  onClick={() => navigate('/marketplace')}
                  className="flex-1 bg-[#12B76A] hover:bg-[#0F9F5F]"
                >
                  Back to Marketplace
                </Button>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Helmet>
        <title>Checkout | Battwheels Marketplace</title>
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4">
          {/* Progress Steps */}
          <div className="max-w-3xl mx-auto mb-8">
            <div className="flex items-center justify-center">
              <div className={`flex items-center ${step >= 1 ? 'text-[#12B76A]' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-[#12B76A] text-white' : 'bg-gray-200'}`}>
                  1
                </div>
                <span className="ml-2 font-medium hidden sm:inline">Address</span>
              </div>
              <div className={`w-16 h-1 mx-2 ${step >= 2 ? 'bg-[#12B76A]' : 'bg-gray-200'}`} />
              <div className={`flex items-center ${step >= 2 ? 'text-[#12B76A]' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-[#12B76A] text-white' : 'bg-gray-200'}`}>
                  2
                </div>
                <span className="ml-2 font-medium hidden sm:inline">Payment</span>
              </div>
              <div className={`w-16 h-1 mx-2 ${step >= 3 ? 'bg-[#12B76A]' : 'bg-gray-200'}`} />
              <div className={`flex items-center ${step >= 3 ? 'text-[#12B76A]' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-[#12B76A] text-white' : 'bg-gray-200'}`}>
                  3
                </div>
                <span className="ml-2 font-medium hidden sm:inline">Confirm</span>
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-2 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  {error}
                </div>
              )}

              {/* Step 1: Address */}
              {step === 1 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-[#12B76A]" />
                    Shipping Address
                  </h2>

                  <form onSubmit={handleAddressSubmit} className="space-y-4">
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="name">Full Name *</Label>
                        <Input
                          id="name"
                          value={address.name}
                          onChange={(e) => setAddress({ ...address, name: e.target.value })}
                          placeholder="John Doe"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="phone">Phone Number *</Label>
                        <Input
                          id="phone"
                          value={address.phone}
                          onChange={(e) => setAddress({ ...address, phone: e.target.value })}
                          placeholder="+91 98765 43210"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={address.email}
                        onChange={(e) => setAddress({ ...address, email: e.target.value })}
                        placeholder="john@example.com"
                      />
                    </div>

                    <div>
                      <Label htmlFor="address1">Address Line 1 *</Label>
                      <Input
                        id="address1"
                        value={address.address_line1}
                        onChange={(e) => setAddress({ ...address, address_line1: e.target.value })}
                        placeholder="House/Building No., Street"
                        required
                      />
                    </div>

                    <div>
                      <Label htmlFor="address2">Address Line 2</Label>
                      <Input
                        id="address2"
                        value={address.address_line2}
                        onChange={(e) => setAddress({ ...address, address_line2: e.target.value })}
                        placeholder="Landmark, Area"
                      />
                    </div>

                    <div className="grid sm:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="city">City *</Label>
                        <Input
                          id="city"
                          value={address.city}
                          onChange={(e) => setAddress({ ...address, city: e.target.value })}
                          placeholder="Delhi"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="state">State *</Label>
                        <Input
                          id="state"
                          value={address.state}
                          onChange={(e) => setAddress({ ...address, state: e.target.value })}
                          placeholder="Delhi"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="pincode">Pincode *</Label>
                        <Input
                          id="pincode"
                          value={address.pincode}
                          onChange={(e) => setAddress({ ...address, pincode: e.target.value })}
                          placeholder="110001"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="gst">GST Number (Optional - for business)</Label>
                      <Input
                        id="gst"
                        value={address.gst_number}
                        onChange={(e) => setAddress({ ...address, gst_number: e.target.value })}
                        placeholder="22AAAAA0000A1Z5"
                      />
                    </div>

                    <div className="flex gap-4 pt-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => navigate('/marketplace/cart')}
                        className="flex-1"
                      >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Cart
                      </Button>
                      <Button type="submit" className="flex-1 bg-[#12B76A] hover:bg-[#0F9F5F]">
                        Continue to Payment
                      </Button>
                    </div>
                  </form>
                </div>
              )}

              {/* Step 2: Payment */}
              {step === 2 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-[#12B76A]" />
                    Payment Method
                  </h2>

                  <div className="space-y-4 mb-6">
                    {/* Razorpay */}
                    <label
                      className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all ${
                        paymentMethod === 'razorpay' ? 'border-[#12B76A] bg-[#12B76A]/5' : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="payment"
                        value="razorpay"
                        checked={paymentMethod === 'razorpay'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        className="sr-only"
                      />
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        paymentMethod === 'razorpay' ? 'border-[#12B76A]' : 'border-gray-300'
                      }`}>
                        {paymentMethod === 'razorpay' && (
                          <div className="w-3 h-3 rounded-full bg-[#12B76A]" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <CreditCard className="w-5 h-5 text-blue-600" />
                          <span className="font-medium text-gray-900">Pay Online (Razorpay)</span>
                          {!razorpayLoaded && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          Credit/Debit Card, UPI, Net Banking, Wallets
                        </p>
                      </div>
                      <Shield className="w-5 h-5 text-green-500" />
                    </label>

                    {/* COD */}
                    <label
                      className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all ${
                        paymentMethod === 'cod' ? 'border-[#12B76A] bg-[#12B76A]/5' : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="payment"
                        value="cod"
                        checked={paymentMethod === 'cod'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        className="sr-only"
                      />
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        paymentMethod === 'cod' ? 'border-[#12B76A]' : 'border-gray-300'
                      }`}>
                        {paymentMethod === 'cod' && (
                          <div className="w-3 h-3 rounded-full bg-[#12B76A]" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Banknote className="w-5 h-5 text-green-600" />
                          <span className="font-medium text-gray-900">Cash on Delivery</span>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          Pay when your order arrives
                        </p>
                      </div>
                    </label>
                  </div>

                  {/* Shipping Address Summary */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">Shipping to:</h3>
                      <button
                        onClick={() => setStep(1)}
                        className="text-sm text-[#12B76A] hover:underline"
                      >
                        Edit
                      </button>
                    </div>
                    <p className="text-sm text-gray-600">
                      {address.name}<br />
                      {address.address_line1}<br />
                      {address.address_line2 && <>{address.address_line2}<br /></>}
                      {address.city}, {address.state} - {address.pincode}<br />
                      Phone: {address.phone}
                    </p>
                  </div>

                  <div className="flex gap-4">
                    <Button
                      variant="outline"
                      onClick={() => setStep(1)}
                      className="flex-1"
                    >
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Back
                    </Button>
                    <Button
                      onClick={handlePlaceOrder}
                      disabled={loading || (paymentMethod === 'razorpay' && !razorpayLoaded)}
                      className="flex-1 bg-[#12B76A] hover:bg-[#0F9F5F]"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        `Place Order • ₹${total.toLocaleString()}`
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Order Summary Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-[100px]">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>

                {/* Items */}
                <div className="space-y-3 mb-4 max-h-[300px] overflow-y-auto">
                  {cart.map((item) => (
                    <div key={item.id} className="flex gap-3">
                      <div className="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0 flex items-center justify-center">
                        {item.images?.[0] ? (
                          <img src={item.images[0]} alt="" className="w-full h-full object-contain rounded-lg" />
                        ) : (
                          <Package className="w-8 h-8 text-gray-300" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 line-clamp-1">{item.name}</p>
                        <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                        <p className="text-sm font-medium">₹{(item.final_price * item.quantity).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-gray-200 pt-4 space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Subtotal</span>
                    <span>₹{subtotal.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Shipping</span>
                    <span>{shipping === 0 ? 'FREE' : `₹${shipping}`}</span>
                  </div>
                  <div className="flex justify-between font-bold text-gray-900 pt-2 border-t">
                    <span>Total</span>
                    <span>₹{total.toLocaleString()}</span>
                  </div>
                </div>

                {/* Security Badge */}
                <div className="mt-4 p-3 bg-green-50 rounded-lg flex items-center gap-2">
                  <Shield className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-green-700">Secure Payment with Razorpay</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
};

export default Checkout;

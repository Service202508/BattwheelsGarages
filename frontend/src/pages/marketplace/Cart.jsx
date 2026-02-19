/**
 * Shopping Cart Page - Premium Marketplace Design
 * Standard e-commerce cart with product images, quantity controls, and order summary
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Button } from '../../components/ui/button';
import { useMarketplace } from '../../context/MarketplaceContext';
import { useToast } from '../../hooks/use-toast';
import {
  ShoppingCart,
  Package,
  Trash2,
  Plus,
  Minus,
  ArrowLeft,
  ArrowRight,
  Truck,
  Shield,
  Tag,
  CreditCard,
  Gift,
  CheckCircle,
  X,
  Heart,
  RefreshCw,
  Percent,
  Clock,
  MapPin,
  Phone,
  Zap
} from 'lucide-react';

const Cart = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { cart, removeFromCart, updateQuantity, getCartTotal, getCartCount, clearCart } = useMarketplace();
  const [couponCode, setCouponCode] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState(null);

  const subtotal = getCartTotal();
  const shipping = subtotal >= 2000 ? 0 : 99;
  const discount = appliedCoupon ? Math.round(subtotal * 0.1) : 0;
  const total = subtotal + shipping - discount;

  const handleApplyCoupon = () => {
    if (couponCode.toUpperCase() === 'FIRST10' || couponCode.toUpperCase() === 'BATTWHEELS10') {
      setAppliedCoupon({ code: couponCode.toUpperCase(), discount: 10 });
      toast({
        title: "Coupon Applied!",
        description: "10% discount has been applied to your order.",
      });
    } else {
      toast({
        title: "Invalid Coupon",
        description: "Please enter a valid coupon code.",
        variant: "destructive"
      });
    }
  };

  const handleRemoveCoupon = () => {
    setAppliedCoupon(null);
    setCouponCode('');
    toast({
      title: "Coupon Removed",
      description: "Discount has been removed from your order.",
    });
  };

  const handleRemoveItem = (itemId, itemName) => {
    removeFromCart(itemId);
    toast({
      title: "Item Removed",
      description: `${itemName} has been removed from your cart.`,
    });
  };

  // Empty Cart State
  if (cart.length === 0) {
    return (
      <>
        <Helmet>
          <title>Shopping Cart | Battwheels Marketplace</title>
        </Helmet>
        <Header />
        <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
          <div className="container mx-auto px-4 py-16">
            <div className="max-w-md mx-auto text-center">
              {/* Empty Cart Illustration */}
              <div className="w-32 h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-8">
                <ShoppingCart className="w-16 h-16 text-gray-400" />
              </div>
              
              <h1 className="text-3xl font-bold text-gray-900 mb-3">Your Cart is Empty</h1>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Looks like you haven&apos;t added anything to your cart yet. 
                Start shopping and find amazing deals on EV parts and vehicles!
              </p>
              
              <div className="space-y-4">
                <Button
                  onClick={() => navigate('/marketplace/spares')}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white py-6 text-lg"
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Browse Spare Parts
                </Button>
                <Button
                  onClick={() => navigate('/marketplace/vehicles')}
                  variant="outline"
                  className="w-full py-6 text-lg border-2"
                >
                  Browse Electric Vehicles
                </Button>
              </div>

              {/* Suggestions */}
              <div className="mt-12 p-6 bg-green-50 rounded-2xl text-left">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Gift className="w-5 h-5 text-green-600" />
                  Quick Tips
                </h3>
                <ul className="text-sm text-gray-600 space-y-2">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    Free shipping on orders above ₹2,000
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    Use code FIRST10 for 10% off your first order
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    All parts come with warranty coverage
                  </li>
                </ul>
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
        <title>{`Shopping Cart (${getCartCount()}) | Battwheels Marketplace`}</title>
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4">
          {/* Breadcrumb & Title */}
          <div className="mb-8">
            <nav className="text-sm text-gray-500 mb-4">
              <Link to="/marketplace" className="hover:text-green-600">Marketplace</Link>
              <span className="mx-2">/</span>
              <span className="text-gray-900">Shopping Cart</span>
            </nav>
            
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                  Shopping Cart
                </h1>
                <p className="text-gray-600 mt-1">{getCartCount()} item{getCartCount() > 1 ? 's' : ''} in your cart</p>
              </div>
              <button
                onClick={() => {
                  clearCart();
                  toast({ title: "Cart Cleared", description: "All items have been removed." });
                }}
                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1.5 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Clear Cart
              </button>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Cart Items Column */}
            <div className="lg:col-span-2 space-y-4">
              {/* Free Shipping Progress */}
              {subtotal < 2000 && (
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <Truck className="w-5 h-5 text-green-600" />
                    <span className="text-sm font-medium text-gray-900">
                      Add ₹{(2000 - subtotal).toLocaleString()} more for <span className="text-green-600">FREE shipping!</span>
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min((subtotal / 2000) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Cart Items */}
              {cart.map((item, index) => (
                <div
                  key={item.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
                  data-testid={`cart-item-${item.sku}`}
                >
                  <div className="p-4 md:p-6">
                    <div className="flex gap-4 md:gap-6">
                      {/* Product Image */}
                      <Link
                        to={`/marketplace/product/${item.slug}`}
                        className="w-24 h-24 md:w-32 md:h-32 bg-gray-50 rounded-xl flex-shrink-0 overflow-hidden group"
                      >
                        {item.images?.[0] ? (
                          <img
                            src={item.images[0]}
                            alt={item.name}
                            className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Package className="w-12 h-12 text-gray-300" />
                          </div>
                        )}
                      </Link>

                      {/* Product Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <Link
                              to={`/marketplace/product/${item.slug}`}
                              className="font-semibold text-gray-900 hover:text-green-600 transition-colors line-clamp-2 text-lg"
                            >
                              {item.name}
                            </Link>
                            
                            <div className="flex flex-wrap items-center gap-3 mt-2">
                              <span className="text-sm text-gray-500">SKU: {item.sku}</span>
                              {item.is_certified && (
                                <span className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                                  <Shield className="w-3 h-3" />
                                  Certified
                                </span>
                              )}
                              {item.warranty_months > 0 && (
                                <span className="text-xs text-gray-500">
                                  {item.warranty_months} months warranty
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Remove Button */}
                          <button
                            onClick={() => handleRemoveItem(item.id, item.name)}
                            className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors"
                            aria-label="Remove item"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>

                        {/* Price & Quantity Row */}
                        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mt-4">
                          {/* Quantity Control */}
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-600">Qty:</span>
                            <div className="flex items-center border-2 border-gray-200 rounded-lg overflow-hidden">
                              <button
                                onClick={() => updateQuantity(item.id, item.quantity - 1)}
                                className="p-2 hover:bg-gray-100 transition-colors disabled:opacity-50"
                                disabled={item.quantity <= 1}
                                aria-label="Decrease quantity"
                              >
                                <Minus className="w-4 h-4" />
                              </button>
                              <span className="px-4 py-2 font-semibold min-w-[50px] text-center bg-gray-50">
                                {item.quantity}
                              </span>
                              <button
                                onClick={() => updateQuantity(item.id, item.quantity + 1)}
                                className="p-2 hover:bg-gray-100 transition-colors disabled:opacity-50"
                                disabled={item.quantity >= (item.stock_quantity || 99)}
                                aria-label="Increase quantity"
                              >
                                <Plus className="w-4 h-4" />
                              </button>
                            </div>
                            
                            {item.stock_quantity && item.quantity >= item.stock_quantity && (
                              <span className="text-xs text-amber-600">Max qty reached</span>
                            )}
                          </div>

                          {/* Price */}
                          <div className="text-right">
                            <p className="text-2xl font-bold text-gray-900">
                              ₹{(item.final_price * item.quantity).toLocaleString()}
                            </p>
                            {item.quantity > 1 && (
                              <p className="text-sm text-gray-500">
                                ₹{item.final_price.toLocaleString()} × {item.quantity}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Delivery Info Bar */}
                  <div className="bg-gray-50 px-4 md:px-6 py-3 flex items-center gap-4 text-sm text-gray-600 border-t">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-green-500" />
                      Ships in 24-48 hrs
                    </span>
                    <span className="flex items-center gap-1.5">
                      <RefreshCw className="w-4 h-4 text-blue-500" />
                      Easy Returns
                    </span>
                  </div>
                </div>
              ))}

              {/* Continue Shopping Link */}
              <Link
                to="/marketplace"
                className="inline-flex items-center gap-2 text-green-600 hover:text-green-700 font-medium mt-4 hover:underline"
              >
                <ArrowLeft className="w-4 h-4" />
                Continue Shopping
              </Link>
            </div>

            {/* Order Summary Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden sticky top-[100px]">
                {/* Header */}
                <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-5">
                  <h2 className="text-lg font-semibold">Order Summary</h2>
                </div>

                <div className="p-5">
                  {/* Coupon Code */}
                  <div className="mb-6">
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Have a coupon?
                    </label>
                    {appliedCoupon ? (
                      <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <Tag className="w-4 h-4 text-green-600" />
                          <span className="font-medium text-green-700">{appliedCoupon.code}</span>
                          <span className="text-sm text-green-600">(-{appliedCoupon.discount}%)</span>
                        </div>
                        <button
                          onClick={handleRemoveCoupon}
                          className="text-gray-500 hover:text-red-500"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={couponCode}
                          onChange={(e) => setCouponCode(e.target.value)}
                          placeholder="Enter code"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        />
                        <Button
                          onClick={handleApplyCoupon}
                          variant="outline"
                          className="px-4"
                        >
                          Apply
                        </Button>
                      </div>
                    )}
                    <p className="text-xs text-gray-500 mt-2">Try: FIRST10, BATTWHEELS10</p>
                  </div>

                  {/* Price Breakdown */}
                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between text-gray-600">
                      <span>Subtotal ({getCartCount()} items)</span>
                      <span>₹{subtotal.toLocaleString()}</span>
                    </div>
                    
                    <div className="flex justify-between text-gray-600">
                      <span className="flex items-center gap-1.5">
                        <Truck className="w-4 h-4" />
                        Shipping
                      </span>
                      <span className={shipping === 0 ? 'text-green-600 font-medium' : ''}>
                        {shipping === 0 ? 'FREE' : `₹${shipping}`}
                      </span>
                    </div>
                    
                    {appliedCoupon && (
                      <div className="flex justify-between text-green-600">
                        <span className="flex items-center gap-1.5">
                          <Percent className="w-4 h-4" />
                          Discount ({appliedCoupon.discount}%)
                        </span>
                        <span>-₹{discount.toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Total */}
                  <div className="border-t-2 border-gray-100 pt-4 mb-6">
                    <div className="flex justify-between items-end">
                      <div>
                        <span className="text-lg font-bold text-gray-900">Total</span>
                        <p className="text-xs text-gray-500">Inclusive of all taxes</p>
                      </div>
                      <span className="text-2xl font-bold text-gray-900">₹{total.toLocaleString()}</span>
                    </div>
                    
                    {discount > 0 && (
                      <p className="text-sm text-green-600 mt-2">
                        🎉 You&apos;re saving ₹{discount.toLocaleString()} on this order!
                      </p>
                    )}
                  </div>

                  {/* Checkout Button */}
                  <Button
                    onClick={() => navigate('/marketplace/checkout')}
                    className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all"
                    data-testid="checkout-button"
                  >
                    <CreditCard className="w-5 h-5 mr-2" />
                    Proceed to Checkout
                  </Button>

                  {/* Payment Methods */}
                  <div className="mt-4 flex items-center justify-center gap-2 text-gray-400">
                    <Shield className="w-4 h-4" />
                    <span className="text-xs">Secure checkout with Razorpay</span>
                  </div>
                </div>

                {/* Trust Features */}
                <div className="bg-gray-50 p-5 border-t">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <Shield className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-900">Secure Payment</p>
                        <p className="text-xs text-gray-500">256-bit SSL</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Truck className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-900">Fast Delivery</p>
                        <p className="text-xs text-gray-500">Pan-India</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <RefreshCw className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-900">Easy Returns</p>
                        <p className="text-xs text-gray-500">7-day policy</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                        <Phone className="w-5 h-5 text-amber-600" />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-900">24/7 Support</p>
                        <p className="text-xs text-gray-500">WhatsApp</p>
                      </div>
                    </div>
                  </div>
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

export default Cart;

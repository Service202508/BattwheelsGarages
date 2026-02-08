/**
 * Marketplace Context - Cart & Auth State Management
 */
import React, { createContext, useContext, useState, useEffect } from 'react';

const MarketplaceContext = createContext();

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const MarketplaceProvider = ({ children }) => {
  // Auth State
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('marketplace_token'));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  // Cart State
  const [cart, setCart] = useState(() => {
    const saved = localStorage.getItem('marketplace_cart');
    return saved ? JSON.parse(saved) : [];
  });

  // User role for pricing
  const userRole = user?.role || 'public';

  // Persist cart to localStorage
  useEffect(() => {
    localStorage.setItem('marketplace_cart', JSON.stringify(cart));
  }, [cart]);

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await fetch(`${API_URL}/api/marketplace/auth/me?token=${token}`);
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            // Invalid token
            localStorage.removeItem('marketplace_token');
            setToken(null);
          }
        } catch (error) {
          console.error('Auth check failed:', error);
        }
      }
      setAuthLoading(false);
    };
    checkAuth();
  }, [token]);

  // Auth Functions
  const sendOTP = async (phone) => {
    const response = await fetch(`${API_URL}/api/marketplace/auth/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone })
    });
    return response.json();
  };

  const verifyOTP = async (phone, otp) => {
    const response = await fetch(`${API_URL}/api/marketplace/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, otp })
    });
    const data = await response.json();
    if (data.success) {
      setToken(data.token);
      setUser(data.user);
      setIsAuthenticated(true);
      localStorage.setItem('marketplace_token', data.token);
    }
    return data;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('marketplace_token');
  };

  const updateProfile = async (profileData) => {
    const response = await fetch(`${API_URL}/api/marketplace/auth/profile?token=${token}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData)
    });
    return response.json();
  };

  // Cart Functions
  const addToCart = (product, quantity = 1) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prev, { ...product, quantity }];
    });
  };

  const removeFromCart = (productId) => {
    setCart(prev => prev.filter(item => item.id !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart(prev =>
      prev.map(item =>
        item.id === productId ? { ...item, quantity } : item
      )
    );
  };

  const clearCart = () => {
    setCart([]);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.final_price * item.quantity), 0);
  };

  const getCartCount = () => {
    return cart.reduce((count, item) => count + item.quantity, 0);
  };

  // Order Functions
  const createOrder = async (orderData) => {
    const response = await fetch(`${API_URL}/api/marketplace/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...orderData,
        user_role: userRole,
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        }))
      })
    });
    return response.json();
  };

  const value = {
    // Auth
    user,
    token,
    isAuthenticated,
    authLoading,
    userRole,
    sendOTP,
    verifyOTP,
    logout,
    updateProfile,
    // Cart
    cart,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    getCartTotal,
    getCartCount,
    // Orders
    createOrder
  };

  return (
    <MarketplaceContext.Provider value={value}>
      {children}
    </MarketplaceContext.Provider>
  );
};

export const useMarketplace = () => {
  const context = useContext(MarketplaceContext);
  if (!context) {
    throw new Error('useMarketplace must be used within MarketplaceProvider');
  }
  return context;
};

export default MarketplaceContext;

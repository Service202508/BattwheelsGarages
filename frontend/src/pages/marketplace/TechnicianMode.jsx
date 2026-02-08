/**
 * Technician Quick-Order Mode
 * High-speed operational interface for field technicians
 * Optimized for fast search, vehicle compatibility, and one-click ordering
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useMarketplace } from '../../context/MarketplaceContext';
import {
  Search,
  Zap,
  Package,
  CheckCircle,
  MapPin,
  Clock,
  Plus,
  ShoppingCart,
  AlertCircle,
  Truck,
  Wrench,
  Battery,
  Settings,
  Filter,
  X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Common failure types for quick filter
const FAILURE_TYPES = [
  { id: 'throttle', label: 'Throttle Issue', icon: Settings },
  { id: 'controller', label: 'Controller Fault', icon: Zap },
  { id: 'motor', label: 'Motor Problem', icon: Settings },
  { id: 'battery', label: 'Battery Issue', icon: Battery },
  { id: 'display', label: 'Display Error', icon: Package },
  { id: 'charger', label: 'Charging Issue', icon: Zap }
];

// Popular vehicle models for quick filter
const VEHICLE_MODELS = [
  'Ather 450X', 'Ola S1 Pro', 'TVS iQube', 'Bajaj Chetak', 'Hero Vida',
  'Bounce Infinity', 'Mahindra Treo', 'Piaggio Ape', 'Tata Nexon EV'
];

const TechnicianMode = () => {
  const navigate = useNavigate();
  const { addToCart, getCartCount, userRole, isAuthenticated } = useMarketplace();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState('');
  const [selectedFailure, setSelectedFailure] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);

  // Check if user is technician
  const isTechnician = userRole === 'technician';

  // Debounced search
  const performSearch = useCallback(async () => {
    if (!searchQuery && !selectedVehicle && !selectedFailure) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('q', searchQuery || selectedVehicle || selectedFailure);
      if (selectedVehicle) params.append('vehicle_model', selectedVehicle);
      if (selectedFailure) params.append('failure_type', selectedFailure);
      params.append('limit', '20');
      params.append('role', 'technician');

      const response = await fetch(`${API_URL}/api/marketplace/quick-search?${params}`);
      const data = await response.json();
      setResults(data.results || []);

      // Save to recent searches
      if (searchQuery && !recentSearches.includes(searchQuery)) {
        setRecentSearches(prev => [searchQuery, ...prev.slice(0, 4)]);
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedVehicle, selectedFailure, recentSearches]);

  useEffect(() => {
    const timer = setTimeout(performSearch, 300);
    return () => clearTimeout(timer);
  }, [performSearch]);

  const handleQuickAdd = (product) => {
    addToCart(product, 1);
    // Visual feedback could be added here
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedVehicle('');
    setSelectedFailure('');
    setResults([]);
  };

  return (
    <>
      <Helmet>
        <title>Quick Order - Technician Mode | Battwheels Marketplace</title>
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-900">
        {/* Hero Banner */}
        <div className="bg-gradient-to-r from-[#12B76A] to-[#0B8A44] text-white py-4">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-2 rounded-lg">
                  <Wrench className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-xl font-bold">Technician Quick-Order</h1>
                  <p className="text-sm text-white/80">Fast part search for field operations</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {isTechnician && (
                  <span className="bg-white/20 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" />
                    Technician Pricing Active
                  </span>
                )}
                <button
                  onClick={() => navigate('/marketplace/cart')}
                  className="relative bg-white text-gray-900 px-4 py-2 rounded-lg font-medium flex items-center gap-2"
                >
                  <ShoppingCart className="w-5 h-5" />
                  Cart
                  {getCartCount() > 0 && (
                    <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                      {getCartCount()}
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-6">
          {/* Search Section */}
          <div className="bg-gray-800 rounded-xl p-6 mb-6">
            {/* Main Search */}
            <div className="relative mb-6">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-6 h-6" />
              <Input
                type="text"
                placeholder="Search by part name, SKU, vehicle model, or issue type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-14 pr-4 py-6 text-lg bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 rounded-xl focus:ring-[#12B76A] focus:border-[#12B76A]"
                autoFocus
              />
              {(searchQuery || selectedVehicle || selectedFailure) && (
                <button
                  onClick={clearFilters}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* Quick Filters */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Vehicle Model Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Vehicle Model
                </label>
                <div className="flex flex-wrap gap-2">
                  {VEHICLE_MODELS.slice(0, 6).map((vehicle) => (
                    <button
                      key={vehicle}
                      onClick={() => setSelectedVehicle(selectedVehicle === vehicle ? '' : vehicle)}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                        selectedVehicle === vehicle
                          ? 'bg-[#12B76A] text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {vehicle}
                    </button>
                  ))}
                </div>
              </div>

              {/* Failure Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Failure Type
                </label>
                <div className="flex flex-wrap gap-2">
                  {FAILURE_TYPES.map((failure) => (
                    <button
                      key={failure.id}
                      onClick={() => setSelectedFailure(selectedFailure === failure.id ? '' : failure.id)}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-1 ${
                        selectedFailure === failure.id
                          ? 'bg-[#12B76A] text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      <failure.icon className="w-3 h-3" />
                      {failure.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Searches */}
            {recentSearches.length > 0 && !searchQuery && (
              <div className="mt-4 pt-4 border-t border-gray-700">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Recent Searches
                </label>
                <div className="flex flex-wrap gap-2">
                  {recentSearches.map((term, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSearchQuery(term)}
                      className="px-3 py-1 rounded-full text-sm bg-gray-700 text-gray-300 hover:bg-gray-600"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Results Section */}
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin w-8 h-8 border-2 border-[#12B76A] border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-gray-400">Searching...</p>
              </div>
            ) : results.length === 0 ? (
              <div className="text-center py-12">
                {searchQuery || selectedVehicle || selectedFailure ? (
                  <>
                    <AlertCircle className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">No parts found. Try different keywords.</p>
                  </>
                ) : (
                  <>
                    <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">Start typing to search for parts</p>
                    <p className="text-sm text-gray-500 mt-2">Or select a vehicle model / failure type above</p>
                  </>
                )}
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <p className="text-gray-400">
                    Found <span className="text-white font-medium">{results.length}</span> parts
                  </p>
                </div>

                {/* Results Grid - Compact Cards for Fast Scanning */}
                <div className="grid gap-3">
                  {results.map((product) => (
                    <QuickOrderCard
                      key={product.id}
                      product={product}
                      onAddToCart={handleQuickAdd}
                    />
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Floating Cart Button - Mobile */}
          {getCartCount() > 0 && (
            <div className="fixed bottom-6 right-6 lg:hidden">
              <button
                onClick={() => navigate('/marketplace/cart')}
                className="bg-[#12B76A] text-white p-4 rounded-full shadow-lg flex items-center gap-2"
              >
                <ShoppingCart className="w-6 h-6" />
                <span className="font-bold">{getCartCount()}</span>
              </button>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </>
  );
};

// Quick Order Card - Optimized for fast scanning and one-click add
const QuickOrderCard = ({ product, onAddToCart }) => {
  const [added, setAdded] = useState(false);

  const handleAdd = () => {
    onAddToCart(product);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <div className="bg-gray-800 rounded-xl p-4 flex items-center gap-4 hover:bg-gray-750 transition-colors border border-gray-700">
      {/* Product Image */}
      <div className="w-20 h-20 bg-gray-700 rounded-lg flex-shrink-0 flex items-center justify-center">
        {product.images?.[0] ? (
          <img src={product.images[0]} alt="" className="w-full h-full object-contain rounded-lg" />
        ) : (
          <Package className="w-10 h-10 text-gray-500" />
        )}
      </div>

      {/* Product Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="font-semibold text-white line-clamp-1">{product.name}</h3>
            <p className="text-sm text-gray-400 font-mono">{product.sku}</p>
          </div>
          {product.is_certified && (
            <span className="bg-[#12B76A]/20 text-[#12B76A] text-xs px-2 py-0.5 rounded-full flex items-center gap-1 flex-shrink-0">
              <CheckCircle className="w-3 h-3" />
              Certified
            </span>
          )}
        </div>

        {/* Compatibility */}
        {product.compatibility?.length > 0 && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-1">
            Fits: {product.compatibility.slice(0, 3).join(', ')}
          </p>
        )}

        {/* Stock & Location */}
        <div className="flex items-center gap-3 mt-2 text-xs">
          <span className={`flex items-center gap-1 ${
            product.stock_status === 'in_stock' ? 'text-green-400' :
            product.stock_status === 'low_stock' ? 'text-yellow-400' : 'text-red-400'
          }`}>
            <div className="w-2 h-2 rounded-full bg-current" />
            {product.stock_quantity} in stock
          </span>
          <span className="text-gray-500 flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            Nearby available
          </span>
        </div>
      </div>

      {/* Price & Add Button */}
      <div className="text-right flex-shrink-0">
        <p className="text-xl font-bold text-white">₹{product.final_price?.toLocaleString()}</p>
        {product.discount_percent > 0 && (
          <p className="text-xs text-[#12B76A]">{product.discount_percent}% off</p>
        )}
        <Button
          onClick={handleAdd}
          disabled={product.stock_status === 'out_of_stock'}
          className={`mt-2 ${
            added
              ? 'bg-green-600 hover:bg-green-600'
              : 'bg-[#12B76A] hover:bg-[#0F9F5F]'
          } text-white min-w-[100px]`}
        >
          {added ? (
            <>
              <CheckCircle className="w-4 h-4 mr-1" />
              Added
            </>
          ) : (
            <>
              <Plus className="w-4 h-4 mr-1" />
              Add
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default TechnicianMode;

/**
 * Electric Vehicles Marketplace - Refurbished 2W & 3W Only
 * Certified Refurbished EVs organized by OEM
 */
import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import GearBackground from '../../components/common/GearBackground';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useMarketplace } from '../../context/MarketplaceContext';
import {
  Search,
  Bike,
  Truck,
  CheckCircle,
  Shield,
  Filter,
  X,
  ChevronRight,
  Battery,
  Gauge,
  Phone,
  Sparkles,
  AlertCircle,
  Zap,
  RefreshCw,
  Package,
  Car,
  PhoneCall,
  Clock,
  User,
  MessageSquare,
  Loader2
} from 'lucide-react';
import { useToast } from '../../components/ui/use-toast';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Vehicle type config - Only 2W and 3W (refurbished)
const vehicleTypeConfig = {
  '2W': { icon: Bike, label: '2-Wheelers', sublabel: 'Scooters & Motorcycles', color: 'from-blue-500 to-indigo-600' },
  '3W': { icon: Truck, label: '3-Wheelers', sublabel: 'Autos & Cargo', color: 'from-orange-500 to-amber-600' }
};

// OEM brand colors - Updated with all brands
const oemBrands = {
  'Ola Electric': { color: '#2ECC71', bg: 'bg-green-500' },
  'Ather Energy': { color: '#00A86B', bg: 'bg-teal-500' },
  'TVS Motor': { color: '#1E90FF', bg: 'bg-blue-500' },
  'Bajaj Auto': { color: '#FF6B00', bg: 'bg-orange-500' },
  'Hero MotoCorp': { color: '#E31837', bg: 'bg-red-600' },
  'Hero Electric': { color: '#E31837', bg: 'bg-red-600' },
  'Greaves Electric': { color: '#4A90D9', bg: 'bg-blue-400' },
  'Okinawa': { color: '#FF4500', bg: 'bg-orange-600' },
  'Revolt Motors': { color: '#000000', bg: 'bg-gray-800' },
  'Tork Motors': { color: '#FF0000', bg: 'bg-red-500' },
  'Simple Energy': { color: '#6B5B95', bg: 'bg-purple-500' },
  'PURE EV': { color: '#32CD32', bg: 'bg-green-500' },
  'Oben Electric': { color: '#FF6347', bg: 'bg-red-400' },
  'Ultraviolette': { color: '#4B0082', bg: 'bg-indigo-700' },
  'Kinetic Green': { color: '#228B22', bg: 'bg-green-600' },
  'Wardwizard Joy e-Bike': { color: '#FFD700', bg: 'bg-yellow-500' },
  'Mahindra': { color: '#E31837', bg: 'bg-red-700' },
  'Piaggio': { color: '#00599C', bg: 'bg-blue-700' },
  'Euler Motors': { color: '#FF8C00', bg: 'bg-orange-500' },
  'Omega Seiki': { color: '#2F4F4F', bg: 'bg-gray-600' },
  'Lohia Auto': { color: '#8B4513', bg: 'bg-amber-700' },
  'Atul Auto': { color: '#006400', bg: 'bg-green-700' },
  'YC Electric': { color: '#4169E1', bg: 'bg-blue-500' },
  'Mini Metro': { color: '#808080', bg: 'bg-gray-500' },
  'Saarthi': { color: '#CD853F', bg: 'bg-amber-600' },
  'Udaan': { color: '#20B2AA', bg: 'bg-teal-400' },
  'Montra Electric': { color: '#9932CC', bg: 'bg-purple-600' }
};

const ElectricVehicles = () => {
  const [searchParams] = useSearchParams();
  const { getCartCount } = useMarketplace();
  const { toast } = useToast();
  
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalVehicles, setTotalVehicles] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [oems, setOems] = useState([]);
  
  // Callback modal state
  const [showCallbackModal, setShowCallbackModal] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [callbackForm, setCallbackForm] = useState({
    name: '',
    phone: '',
    preferred_time: '',
    message: ''
  });
  const [submittingCallback, setSubmittingCallback] = useState(false);
  
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    vehicleType: searchParams.get('type') || '',
    oem: searchParams.get('oem') || '',
    condition: searchParams.get('condition') || '',
    minPrice: searchParams.get('minPrice') || '',
    maxPrice: searchParams.get('maxPrice') || '',
    sort: searchParams.get('sort') || 'created_at'
  });

  // Fetch vehicles
  useEffect(() => {
    const fetchVehicles = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.search) params.append('search', filters.search);
        if (filters.vehicleType) params.append('vehicle_category', filters.vehicleType);
        if (filters.oem) params.append('brand', filters.oem);
        if (filters.condition === 'new') params.append('oem_aftermarket', 'oem');
        if (filters.condition === 'refurbished') params.append('oem_aftermarket', 'refurbished');
        if (filters.minPrice) params.append('min_price', filters.minPrice);
        if (filters.maxPrice) params.append('max_price', filters.maxPrice);
        params.append('page', currentPage);
        params.append('limit', 12);

        const response = await fetch(`${API_URL}/api/marketplace/vehicles?${params}`);
        const data = await response.json();
        setVehicles(data.vehicles || []);
        setTotalVehicles(data.total || 0);
        setTotalPages(data.pages || 1);
      } catch (error) {
        console.error('Error fetching vehicles:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchVehicles();
  }, [filters, currentPage]);

  // Fetch OEMs
  useEffect(() => {
    const fetchOems = async () => {
      try {
        const response = await fetch(`${API_URL}/api/marketplace/vehicles/oems`);
        const data = await response.json();
        if (data.oems) setOems(data.oems);
      } catch (error) {
        console.error('Error fetching OEMs:', error);
      }
    };
    fetchOems();
  }, []);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      search: '', vehicleType: '', oem: '', condition: '',
      minPrice: '', maxPrice: '', sort: 'created_at'
    });
    setCurrentPage(1);
  };

  const hasActiveFilters = filters.vehicleType || filters.oem || filters.condition || filters.minPrice || filters.maxPrice;

  // Open callback modal for a vehicle
  const openCallbackModal = (vehicle) => {
    setSelectedVehicle(vehicle);
    setCallbackForm({ name: '', phone: '', preferred_time: '', message: '' });
    setShowCallbackModal(true);
  };

  // Handle callback form submission
  const handleCallbackSubmit = async (e) => {
    e.preventDefault();
    if (!callbackForm.name || !callbackForm.phone || !callbackForm.preferred_time) {
      toast({ title: "Please fill all required fields", variant: "destructive" });
      return;
    }
    
    setSubmittingCallback(true);
    try {
      const response = await fetch(`${API_URL}/api/callbacks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...callbackForm,
          vehicle_id: selectedVehicle?.id,
          vehicle_name: selectedVehicle?.name,
          vehicle_slug: selectedVehicle?.slug
        })
      });
      
      const data = await response.json();
      if (data.success) {
        toast({ 
          title: "Callback Request Submitted!", 
          description: "Our team will contact you within 24 hours.",
        });
        setShowCallbackModal(false);
      } else {
        throw new Error(data.message || 'Failed to submit');
      }
    } catch (error) {
      toast({ 
        title: "Failed to submit request", 
        description: "Please try again or call us directly.",
        variant: "destructive" 
      });
    } finally {
      setSubmittingCallback(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 relative">
      <GearBackground variant="industries" />
      
      <Helmet>
        <title>Certified Refurbished Electric Vehicles - 2W & 3W | Battwheels Marketplace</title>
        <meta name="description" content="Browse certified refurbished electric 2-wheelers and 3-wheelers. Quality checked scooters, motorcycles, autos, and cargo EVs from top OEMs." />
      </Helmet>

      <Header />

      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-amber-500 via-orange-500 to-red-500 py-12 md:py-16 relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-10 right-10 w-64 h-64 bg-white rounded-full blur-3xl" />
            <div className="absolute bottom-10 left-10 w-48 h-48 bg-yellow-300 rounded-full blur-3xl" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-amber-100 text-sm mb-6">
              <Link to="/marketplace" className="hover:text-white transition-colors">Marketplace</Link>
              <ChevronRight className="w-4 h-4" />
              <span className="text-white font-medium">Electric Vehicles</span>
            </nav>
            
            <div className="max-w-4xl">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
                  <RefreshCw className="w-7 h-7 text-white" />
                </div>
                <div>
                  <span className="inline-flex items-center gap-1.5 bg-white/20 text-white text-xs font-semibold px-3 py-1 rounded-full mb-2">
                    <Shield className="w-3.5 h-3.5" />
                    CERTIFIED REFURBISHED
                  </span>
                  <h1 className="text-3xl md:text-4xl font-bold text-white">
                    Electric Vehicles
                  </h1>
                </div>
              </div>
              <p className="text-amber-50 text-lg mb-4 max-w-2xl">
                Quality-checked 2-Wheelers & 3-Wheelers from India&apos;s top OEMs
              </p>
              <div className="flex flex-wrap gap-3 mb-8">
                <span className="inline-flex items-center gap-1.5 bg-white/15 text-white text-sm px-3 py-1.5 rounded-full">
                  <Bike className="w-4 h-4" />
                  Scooters & Motorcycles
                </span>
                <span className="inline-flex items-center gap-1.5 bg-white/15 text-white text-sm px-3 py-1.5 rounded-full">
                  <Truck className="w-4 h-4" />
                  Autos & Cargo
                </span>
                <span className="inline-flex items-center gap-1.5 bg-white/15 text-white text-sm px-3 py-1.5 rounded-full">
                  <CheckCircle className="w-4 h-4" />
                  Battery Health Verified
                </span>
              </div>
              
              {/* Search Bar */}
              <div className="max-w-xl">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    type="text"
                    placeholder="Search by vehicle name, model, or OEM..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="pl-12 pr-4 py-4 text-base bg-white text-gray-900 border-0 rounded-xl shadow-lg focus:ring-2 focus:ring-blue-300"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Filter Tabs */}
        <section className="bg-white border-b border-gray-200 sticky top-[72px] z-40 shadow-sm">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-3 py-4 overflow-x-auto scrollbar-hide">
              {/* Vehicle Types */}
              <button
                onClick={() => handleFilterChange('vehicleType', '')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                  !filters.vehicleType
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All Vehicles
              </button>
              {Object.entries(vehicleTypeConfig).map(([key, config]) => {
                const Icon = config.icon;
                return (
                  <button
                    key={key}
                    onClick={() => handleFilterChange('vehicleType', key)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                      filters.vehicleType === key
                        ? `bg-gradient-to-r ${config.color} text-white shadow-md`
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {config.label}
                  </button>
                );
              })}
              
              <div className="h-8 w-px bg-gray-200 mx-2" />
              
              {/* Condition Filters */}
              <button
                onClick={() => handleFilterChange('condition', filters.condition === 'new' ? '' : 'new')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                  filters.condition === 'new'
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md'
                    : 'bg-green-50 text-green-700 hover:bg-green-100'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                New
              </button>
              <button
                onClick={() => handleFilterChange('condition', filters.condition === 'refurbished' ? '' : 'refurbished')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                  filters.condition === 'refurbished'
                    ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md'
                    : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                }`}
              >
                <Shield className="w-4 h-4" />
                Refurbished
              </button>
            </div>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-8">
          <div className="container mx-auto px-4">
            <div className="flex flex-col lg:flex-row gap-8">
              {/* Filters Sidebar */}
              <aside className="hidden lg:block w-72 flex-shrink-0">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sticky top-[160px]">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-bold text-gray-900 flex items-center gap-2">
                      <Filter className="w-5 h-5 text-blue-600" />
                      Filters
                    </h3>
                    {hasActiveFilters && (
                      <button onClick={clearFilters} className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                        Clear all
                      </button>
                    )}
                  </div>

                  {/* OEM Filter */}
                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-800 mb-3">Brand / OEM</label>
                    <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                      {oems.map((oem) => {
                        const brand = oemBrands[oem] || { bg: 'bg-gray-500' };
                        return (
                          <label key={oem} className="flex items-center gap-3 cursor-pointer group p-2 rounded-lg hover:bg-gray-50">
                            <input
                              type="radio"
                              name="oem"
                              checked={filters.oem === oem}
                              onChange={() => handleFilterChange('oem', oem)}
                              className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <span className={`w-3 h-3 rounded-full ${brand.bg}`} />
                            <span className="text-sm text-gray-700 group-hover:text-gray-900 font-medium">{oem}</span>
                          </label>
                        );
                      })}
                      {filters.oem && (
                        <label className="flex items-center gap-3 cursor-pointer p-2">
                          <input
                            type="radio"
                            name="oem"
                            checked={!filters.oem}
                            onChange={() => handleFilterChange('oem', '')}
                            className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <span className="text-sm text-gray-600">All Brands</span>
                        </label>
                      )}
                    </div>
                  </div>

                  {/* Price Range */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-800 mb-3">Price Range (₹)</label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={filters.minPrice}
                        onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                        className="text-sm"
                      />
                      <span className="text-gray-400">—</span>
                      <Input
                        type="number"
                        placeholder="Max"
                        value={filters.maxPrice}
                        onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                        className="text-sm"
                      />
                    </div>
                  </div>
                </div>
              </aside>

              {/* Mobile Filter Button */}
              <div className="lg:hidden flex items-center justify-between mb-4">
                <Button variant="outline" onClick={() => setShowMobileFilters(true)} className="flex items-center gap-2">
                  <Filter className="w-4 h-4" />
                  Filters
                  {hasActiveFilters && <span className="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">Active</span>}
                </Button>
              </div>

              {/* Vehicles Grid */}
              <div className="flex-1">
                {/* Results Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                  <p className="text-gray-600">
                    Showing <span className="font-semibold text-gray-900">{vehicles.length}</span> of{' '}
                    <span className="font-semibold text-gray-900">{totalVehicles}</span> vehicles
                  </p>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500">Sort:</span>
                    <select
                      value={filters.sort}
                      onChange={(e) => handleFilterChange('sort', e.target.value)}
                      className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                      <option value="created_at">Newest First</option>
                      <option value="price_asc">Price: Low to High</option>
                      <option value="price_desc">Price: High to Low</option>
                    </select>
                  </div>
                </div>

                {/* Vehicles */}
                {loading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 animate-pulse">
                        <div className="bg-gray-200 aspect-[4/3] rounded-xl mb-4" />
                        <div className="bg-gray-200 h-5 rounded w-3/4 mb-2" />
                        <div className="bg-gray-200 h-4 rounded w-1/2" />
                      </div>
                    ))}
                  </div>
                ) : vehicles.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-100">
                    <Car className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No vehicles found</h3>
                    <p className="text-gray-600 mb-6">Try adjusting your filters or check back later</p>
                    <Button onClick={clearFilters} className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700">
                      Clear Filters
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {vehicles.map((vehicle) => (
                      <VehicleCard key={vehicle.id} vehicle={vehicle} />
                    ))}
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-3 mt-8">
                    <Button variant="outline" disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)} className="shadow-sm">
                      Previous
                    </Button>
                    <span className="text-sm text-gray-600 bg-white px-4 py-2 rounded-lg border border-gray-200">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button variant="outline" disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)} className="shadow-sm">
                      Next
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />

      {/* Mobile Filters Modal */}
      {showMobileFilters && (
        <div className="fixed inset-0 bg-black/50 z-50 lg:hidden">
          <div className="absolute right-0 top-0 h-full w-80 bg-white shadow-xl overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
              <h3 className="font-bold text-gray-900">Filters</h3>
              <button onClick={() => setShowMobileFilters(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="p-4">
              {/* OEM Filter */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-800 mb-3">Brand / OEM</label>
                <div className="space-y-2">
                  {oems.slice(0, 6).map((oem) => (
                    <label key={oem} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="mobileOem"
                        checked={filters.oem === oem}
                        onChange={() => handleFilterChange('oem', oem)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-sm text-gray-600">{oem}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" onClick={clearFilters} className="flex-1">Clear</Button>
                <Button onClick={() => setShowMobileFilters(false)} className="flex-1 bg-blue-600 hover:bg-blue-700">Apply</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Request Callback Modal */}
      {showCallbackModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setShowCallbackModal(false)}>
          <div 
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-600 p-6 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <PhoneCall className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">Request Callback</h3>
                    <p className="text-amber-100 text-sm">We&apos;ll call you within 24 hours</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowCallbackModal(false)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              {selectedVehicle && (
                <div className="mt-4 p-3 bg-white/10 rounded-xl">
                  <p className="text-sm text-amber-100">Interested in:</p>
                  <p className="font-semibold">{selectedVehicle.name}</p>
                </div>
              )}
            </div>

            {/* Form */}
            <form onSubmit={handleCallbackSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  <User className="w-4 h-4 inline mr-1.5" />
                  Your Name *
                </label>
                <input
                  type="text"
                  value={callbackForm.name}
                  onChange={(e) => setCallbackForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter your full name"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
                  required
                  data-testid="callback-name-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  <Phone className="w-4 h-4 inline mr-1.5" />
                  Phone Number *
                </label>
                <input
                  type="tel"
                  value={callbackForm.phone}
                  onChange={(e) => setCallbackForm(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="Enter 10-digit mobile number"
                  pattern="[0-9]{10}"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
                  required
                  data-testid="callback-phone-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  <Clock className="w-4 h-4 inline mr-1.5" />
                  Preferred Time *
                </label>
                <select
                  value={callbackForm.preferred_time}
                  onChange={(e) => setCallbackForm(prev => ({ ...prev, preferred_time: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all bg-white"
                  required
                  data-testid="callback-time-select"
                >
                  <option value="">Select a time slot</option>
                  <option value="9am-12pm">Morning (9 AM - 12 PM)</option>
                  <option value="12pm-3pm">Afternoon (12 PM - 3 PM)</option>
                  <option value="3pm-6pm">Evening (3 PM - 6 PM)</option>
                  <option value="6pm-9pm">Night (6 PM - 9 PM)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  <MessageSquare className="w-4 h-4 inline mr-1.5" />
                  Message (Optional)
                </label>
                <textarea
                  value={callbackForm.message}
                  onChange={(e) => setCallbackForm(prev => ({ ...prev, message: e.target.value }))}
                  placeholder="Any specific questions or requirements?"
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all resize-none"
                  data-testid="callback-message-input"
                />
              </div>

              <button
                type="submit"
                disabled={submittingCallback}
                className="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white py-3.5 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                data-testid="callback-submit-btn"
              >
                {submittingCallback ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <PhoneCall className="w-5 h-5" />
                    Request Callback
                  </>
                )}
              </button>

              <p className="text-xs text-gray-500 text-center">
                By submitting, you agree to be contacted by our sales team
              </p>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Vehicle Card Component
const VehicleCard = ({ vehicle }) => {
  const brand = oemBrands[vehicle.brand] || { bg: 'bg-gray-500' };
  const typeConfig = vehicleTypeConfig[vehicle.vehicle_category] || { icon: Bike };
  const TypeIcon = typeConfig.icon || Bike;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 group">
      {/* Image */}
      <Link to={`/marketplace/vehicle/${vehicle.slug}`} className="block relative">
        <div className="aspect-[4/3] bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center overflow-hidden">
          {vehicle.images?.[0] ? (
            <img src={vehicle.images[0]} alt={vehicle.name} className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300" />
          ) : (
            <TypeIcon className="w-20 h-20 text-gray-300" />
          )}
        </div>
        
        {/* Badges */}
        <div className="absolute top-3 left-3 flex flex-col gap-2">
          {vehicle.condition === 'refurbished' && (
            <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm font-semibold">
              <RefreshCw className="w-3 h-3" /> Refurbished
            </span>
          )}
          {vehicle.is_certified && (
            <span className="bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xs px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm">
              <Shield className="w-3 h-3" /> Certified
            </span>
          )}
        </div>
        
        {/* Vehicle Type */}
        <div className="absolute top-3 right-3">
          <span className="bg-white/95 backdrop-blur text-gray-700 text-xs px-2.5 py-1.5 rounded-full flex items-center gap-1 shadow-sm font-medium">
            <TypeIcon className="w-3.5 h-3.5" />
            {vehicle.vehicle_category}
          </span>
        </div>
        
        {/* Low Stock Warning */}
        {vehicle.stock_status === 'low_stock' && (
          <div className="absolute bottom-3 left-3 right-3">
            <span className="bg-red-500/90 text-white text-xs px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 justify-center">
              <AlertCircle className="w-3.5 h-3.5" />
              Only {vehicle.stock_quantity} left
            </span>
          </div>
        )}
      </Link>

      {/* Content */}
      <div className="p-5">
        {/* OEM Badge */}
        <div className="flex items-center gap-2 mb-2">
          <span className={`w-2.5 h-2.5 rounded-full ${brand.bg}`} />
          <span className="text-sm font-semibold text-gray-600">{vehicle.brand}</span>
          {vehicle.vehicle_subtype && (
            <span className="text-xs text-gray-400">• {vehicle.vehicle_subtype}</span>
          )}
        </div>
        
        <Link to={`/marketplace/vehicle/${vehicle.slug}`}>
          <h3 className="font-bold text-gray-900 mb-3 line-clamp-2 hover:text-orange-600 transition-colors text-lg leading-snug">
            {vehicle.name}
          </h3>
        </Link>

        {/* Specs */}
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-4">
          {vehicle.specifications?.range_km && (
            <span className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-full">
              <Gauge className="w-3.5 h-3.5 text-blue-500" />
              {vehicle.specifications.range_km} km
            </span>
          )}
          {vehicle.specifications?.battery_kwh && (
            <span className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-full">
              <Battery className="w-3.5 h-3.5 text-green-500" />
              {vehicle.specifications.battery_kwh} kWh
            </span>
          )}
          {vehicle.specifications?.top_speed_kmph && (
            <span className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-full">
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              {vehicle.specifications.top_speed_kmph} km/h
            </span>
          )}
        </div>

        {/* Price */}
        <div className="mb-4">
          <span className="text-2xl font-bold text-gray-900">
            ₹{(vehicle.final_price || vehicle.price)?.toLocaleString()}
          </span>
        </div>

        {/* CTA */}
        <div className="flex gap-2">
          <Link
            to={`/marketplace/vehicle/${vehicle.slug}`}
            className="flex-1 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white text-center py-2.5 rounded-xl text-sm font-semibold transition-all shadow-sm"
          >
            View Details
          </Link>
          <a
            href="tel:+918076331607"
            className="px-4 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors flex items-center justify-center"
          >
            <Phone className="w-4 h-4 text-gray-600" />
          </a>
        </div>

        {/* Warranty */}
        {vehicle.warranty_months > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-1.5 text-xs text-gray-500">
            <Shield className="w-3.5 h-3.5 text-green-500" />
            {vehicle.warranty_months} months warranty included
          </div>
        )}
      </div>
    </div>
  );
};

export default ElectricVehicles;

/**
 * Electric Vehicles Marketplace
 * New & Certified Refurbished EVs organized by OEM and vehicle type
 */
import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useMarketplace } from '../../context/MarketplaceContext';
import {
  Search,
  Car,
  Bike,
  Truck,
  ShoppingCart,
  CheckCircle,
  Shield,
  ArrowLeft,
  Filter,
  X,
  Zap,
  Battery,
  Gauge,
  MapPin,
  Calendar,
  Star,
  Phone,
  ChevronDown
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Vehicle type icons
const vehicleTypeIcons = {
  '2W': <Bike className="w-5 h-5" />,
  '3W': <Truck className="w-5 h-5" />,
  '4W': <Car className="w-5 h-5" />
};

// OEM logos/colors
const oemColors = {
  'Ather': 'bg-teal-500',
  'Ola': 'bg-blue-500',
  'TVS': 'bg-red-500',
  'Bajaj': 'bg-blue-600',
  'Hero': 'bg-red-600',
  'Tata': 'bg-blue-700',
  'Mahindra': 'bg-red-700',
  'MG': 'bg-gray-700',
  'Hyundai': 'bg-blue-800',
  'Piaggio': 'bg-green-600'
};

const ElectricVehicles = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { addToCart, getCartCount } = useMarketplace();
  
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalVehicles, setTotalVehicles] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [oems, setOems] = useState([]);
  
  // Filters
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
        params.append('category', 'Electric Vehicles');
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
        
        // Extract unique OEMs
        const uniqueOems = [...new Set(data.vehicles?.map(v => v.brand).filter(Boolean))];
        if (uniqueOems.length > 0) setOems(uniqueOems);
      } catch (error) {
        console.error('Error fetching vehicles:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchVehicles();
  }, [filters, currentPage]);

  // Fetch OEMs list
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
      search: '',
      vehicleType: '',
      oem: '',
      condition: '',
      minPrice: '',
      maxPrice: '',
      sort: 'created_at'
    });
    setCurrentPage(1);
  };

  const hasActiveFilters = filters.vehicleType || filters.oem || filters.condition || filters.minPrice || filters.maxPrice;

  return (
    <>
      <Helmet>
        <title>Electric Vehicles - New & Refurbished | Battwheels Marketplace</title>
        <meta name="description" content="Browse certified new and refurbished electric vehicles. 2W, 3W, 4W EVs from top OEMs like Ather, Ola, TVS, Tata, Mahindra." />
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 text-white py-12">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-2 text-blue-300 text-sm mb-4">
              <Link to="/marketplace" className="hover:text-white">Marketplace</Link>
              <span>/</span>
              <span className="text-white">Electric Vehicles</span>
            </div>
            
            <div className="max-w-4xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-blue-500/30 p-2 rounded-lg">
                  <Car className="w-8 h-8" />
                </div>
                <h1 className="text-3xl md:text-4xl font-bold">
                  Electric Vehicles
                </h1>
              </div>
              <p className="text-blue-200 text-lg mb-6">
                New & Certified Refurbished EVs from Top OEMs
              </p>
              
              {/* Search Bar */}
              <div className="max-w-xl">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    type="text"
                    placeholder="Search by vehicle name, model, or OEM..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="pl-12 pr-4 py-5 text-base bg-white text-gray-900 border-0 rounded-xl"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Vehicle Type Tabs */}
        <section className="bg-white border-b border-gray-200 sticky top-[72px] z-40">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-2 py-4 overflow-x-auto">
              <button
                onClick={() => handleFilterChange('vehicleType', '')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  !filters.vehicleType
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All Vehicles
              </button>
              {['2W', '3W', '4W'].map((type) => (
                <button
                  key={type}
                  onClick={() => handleFilterChange('vehicleType', type)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                    filters.vehicleType === type
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {vehicleTypeIcons[type]}
                  {type === '2W' ? '2-Wheelers' : type === '3W' ? '3-Wheelers' : '4-Wheelers'}
                </button>
              ))}
              
              <div className="h-6 w-px bg-gray-300 mx-2" />
              
              {/* Condition Filter */}
              <button
                onClick={() => handleFilterChange('condition', filters.condition === 'new' ? '' : 'new')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  filters.condition === 'new'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <CheckCircle className="w-4 h-4" />
                New
              </button>
              <button
                onClick={() => handleFilterChange('condition', filters.condition === 'refurbished' ? '' : 'refurbished')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  filters.condition === 'refurbished'
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
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
              <aside className="hidden lg:block w-64 flex-shrink-0">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-[160px]">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-semibold text-gray-900">Filters</h3>
                    {hasActiveFilters && (
                      <button onClick={clearFilters} className="text-sm text-blue-500 hover:underline">
                        Clear all
                      </button>
                    )}
                  </div>

                  {/* OEM Filter */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Brand / OEM
                    </label>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {oems.map((oem) => (
                        <label key={oem} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="oem"
                            checked={filters.oem === oem}
                            onChange={() => handleFilterChange('oem', oem)}
                            className="text-blue-500 focus:ring-blue-500"
                          />
                          <span className={`w-3 h-3 rounded-full ${oemColors[oem] || 'bg-gray-400'}`} />
                          <span className="text-sm text-gray-600">{oem}</span>
                        </label>
                      ))}
                      {filters.oem && (
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="oem"
                            checked={!filters.oem}
                            onChange={() => handleFilterChange('oem', '')}
                            className="text-blue-500 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-600">All Brands</span>
                        </label>
                      )}
                    </div>
                  </div>

                  {/* Price Range */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Price Range (₹)
                    </label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={filters.minPrice}
                        onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                        className="text-sm"
                      />
                      <span className="text-gray-400">-</span>
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

              {/* Vehicles Grid */}
              <div className="flex-1">
                {/* Results Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                  <p className="text-gray-600">
                    Showing <span className="font-medium text-gray-900">{vehicles.length}</span> of{' '}
                    <span className="font-medium text-gray-900">{totalVehicles}</span> vehicles
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Sort by:</span>
                    <select
                      value={filters.sort}
                      onChange={(e) => handleFilterChange('sort', e.target.value)}
                      className="text-sm border border-gray-300 rounded-lg px-3 py-2"
                    >
                      <option value="created_at">Newest First</option>
                      <option value="price_asc">Price: Low to High</option>
                      <option value="price_desc">Price: High to Low</option>
                    </select>
                  </div>
                </div>

                {/* Vehicles */}
                {loading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse">
                        <div className="bg-gray-200 h-48 rounded-lg mb-4" />
                        <div className="bg-gray-200 h-5 rounded w-3/4 mb-2" />
                        <div className="bg-gray-200 h-4 rounded w-1/2" />
                      </div>
                    ))}
                  </div>
                ) : vehicles.length === 0 ? (
                  <div className="text-center py-16">
                    <Car className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No vehicles found</h3>
                    <p className="text-gray-600 mb-4">Try adjusting your filters or check back later</p>
                    <Button onClick={clearFilters} className="bg-blue-500 hover:bg-blue-600">
                      Clear Filters
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {vehicles.map((vehicle) => (
                      <VehicleCard key={vehicle.id} vehicle={vehicle} />
                    ))}
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-8">
                    <Button
                      variant="outline"
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage(p => p - 1)}
                    >
                      Previous
                    </Button>
                    <span className="text-sm text-gray-600">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      disabled={currentPage === totalPages}
                      onClick={() => setCurrentPage(p => p + 1)}
                    >
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
    </>
  );
};

// Vehicle Card Component
const VehicleCard = ({ vehicle }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-all group">
      {/* Image */}
      <Link to={`/marketplace/vehicle/${vehicle.slug}`} className="block relative">
        <div className="aspect-[4/3] bg-gray-100 flex items-center justify-center overflow-hidden">
          {vehicle.images?.[0] ? (
            <img
              src={vehicle.images[0]}
              alt={vehicle.name}
              className="object-cover w-full h-full group-hover:scale-105 transition-transform"
            />
          ) : (
            <Car className="w-20 h-20 text-gray-300" />
          )}
        </div>
        
        {/* Badges */}
        <div className="absolute top-3 left-3 flex flex-col gap-2">
          {vehicle.oem_aftermarket === 'oem' && (
            <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              New
            </span>
          )}
          {vehicle.oem_aftermarket === 'refurbished' && (
            <span className="bg-purple-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
              <Shield className="w-3 h-3" />
              Refurbished
            </span>
          )}
        </div>
        
        {/* Vehicle Type Badge */}
        <div className="absolute top-3 right-3">
          <span className="bg-white/90 backdrop-blur text-gray-700 text-xs px-2 py-1 rounded-full flex items-center gap-1">
            {vehicleTypeIcons[vehicle.vehicle_category?.[0]]}
            {vehicle.vehicle_category?.[0]}
          </span>
        </div>
      </Link>

      {/* Content */}
      <div className="p-4">
        {/* OEM Badge */}
        <div className="flex items-center gap-2 mb-2">
          <span className={`w-2 h-2 rounded-full ${oemColors[vehicle.brand] || 'bg-gray-400'}`} />
          <span className="text-sm font-medium text-gray-500">{vehicle.brand}</span>
        </div>
        
        <Link to={`/marketplace/vehicle/${vehicle.slug}`}>
          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-blue-500 transition-colors">
            {vehicle.name}
          </h3>
        </Link>

        {/* Specs */}
        <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
          {vehicle.specifications?.range && (
            <span className="flex items-center gap-1">
              <Gauge className="w-3 h-3" />
              {vehicle.specifications.range}
            </span>
          )}
          {vehicle.specifications?.battery && (
            <span className="flex items-center gap-1">
              <Battery className="w-3 h-3" />
              {vehicle.specifications.battery}
            </span>
          )}
        </div>

        {/* Price */}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xl font-bold text-gray-900">
              ₹{(vehicle.final_price || vehicle.base_price)?.toLocaleString()}
            </span>
            {vehicle.oem_aftermarket === 'refurbished' && vehicle.original_price && (
              <span className="text-sm text-gray-400 line-through ml-2">
                ₹{vehicle.original_price?.toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-4 flex gap-2">
          <Link
            to={`/marketplace/vehicle/${vehicle.slug}`}
            className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-center py-2 rounded-lg text-sm font-medium transition-colors"
          >
            View Details
          </Link>
          <a
            href="tel:+919876543210"
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Phone className="w-4 h-4 text-gray-600" />
          </a>
        </div>

        {/* Warranty */}
        {vehicle.warranty_months > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-1 text-xs text-gray-500">
            <Shield className="w-3 h-3 text-green-500" />
            {vehicle.warranty_months} months warranty
          </div>
        )}
      </div>
    </div>
  );
};

export default ElectricVehicles;

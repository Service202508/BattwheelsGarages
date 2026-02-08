/**
 * Spares & Components Marketplace - Premium Design
 * Matches Battwheels website design language
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
import { useToast } from '../../components/ui/use-toast';
import {
  Search,
  Filter,
  ShoppingCart,
  Package,
  Battery,
  Wrench,
  Truck,
  Recycle,
  CheckCircle,
  ChevronRight,
  X,
  Zap,
  AlertCircle,
  Settings,
  Bike,
  Car,
  Plus
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Category config with icons and colors
const categoryConfig = {
  '2W Parts': { icon: Bike, color: 'from-blue-500 to-blue-600', bg: 'bg-blue-50', text: 'text-blue-700' },
  '3W Parts': { icon: Truck, color: 'from-orange-500 to-orange-600', bg: 'bg-orange-50', text: 'text-orange-700' },
  '4W Parts': { icon: Car, color: 'from-purple-500 to-purple-600', bg: 'bg-purple-50', text: 'text-purple-700' },
  'Batteries': { icon: Battery, color: 'from-green-500 to-emerald-600', bg: 'bg-green-50', text: 'text-green-700' },
  'Diagnostic Tools': { icon: Settings, color: 'from-red-500 to-red-600', bg: 'bg-red-50', text: 'text-red-700' },
  'Refurbished Components': { icon: Recycle, color: 'from-teal-500 to-teal-600', bg: 'bg-teal-50', text: 'text-teal-700' }
};

const SPARES_CATEGORIES = ['2W Parts', '3W Parts', '4W Parts', 'Batteries', 'Diagnostic Tools', 'Refurbished Components'];

const SparesAndComponents = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { addToCart, getCartCount, userRole } = useMarketplace();
  const { toast } = useToast();
  
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalProducts, setTotalProducts] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    category: searchParams.get('category') || '',
    vehicleCategory: searchParams.get('vehicle') || '',
    oem_aftermarket: searchParams.get('type') || '',
    is_certified: searchParams.get('certified') === 'true',
    minPrice: searchParams.get('minPrice') || '',
    maxPrice: searchParams.get('maxPrice') || '',
    sort: searchParams.get('sort') || 'created_at'
  });

  // Fetch categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(`${API_URL}/api/marketplace/categories`);
        const data = await response.json();
        const sparesCategories = (data.categories || []).filter(cat => 
          SPARES_CATEGORIES.includes(cat.name)
        );
        setCategories(sparesCategories);
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    fetchCategories();
  }, []);

  // Fetch products
  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.search) params.append('search', filters.search);
        if (filters.category) params.append('category', filters.category);
        if (filters.vehicleCategory) params.append('vehicle_category', filters.vehicleCategory);
        if (filters.oem_aftermarket) params.append('oem_aftermarket', filters.oem_aftermarket);
        if (filters.is_certified) params.append('is_certified', 'true');
        if (filters.minPrice) params.append('min_price', filters.minPrice);
        if (filters.maxPrice) params.append('max_price', filters.maxPrice);
        params.append('sort_by', filters.sort.includes('price') ? 'base_price' : filters.sort);
        params.append('sort_order', filters.sort.includes('asc') ? 'asc' : 'desc');
        params.append('page', currentPage);
        params.append('limit', 12);
        params.append('role', userRole);
        params.append('exclude_category', 'Electric Vehicles');

        const response = await fetch(`${API_URL}/api/marketplace/products?${params}`);
        const data = await response.json();
        setProducts(data.products || []);
        setTotalProducts(data.total || 0);
        setTotalPages(data.pages || 1);
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [filters, currentPage, userRole]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      search: '', category: '', vehicleCategory: '', oem_aftermarket: '',
      is_certified: false, minPrice: '', maxPrice: '', sort: 'created_at'
    });
    setCurrentPage(1);
  };

  const hasActiveFilters = filters.category || filters.vehicleCategory || filters.oem_aftermarket || filters.is_certified || filters.minPrice || filters.maxPrice;

  return (
    <div className="min-h-screen bg-gray-50 relative">
      <GearBackground variant="services" />
      
      <Helmet>
        <title>Spares & Components | Battwheels Marketplace</title>
        <meta name="description" content="Shop genuine EV spare parts, batteries, controllers, motors, and diagnostic tools. Certified components for 2W, 3W, 4W electric vehicles." />
      </Helmet>

      <Header />

      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-green-600 to-emerald-700 py-12 md:py-16 relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-10 right-10 w-64 h-64 bg-white rounded-full blur-3xl" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-green-200 text-sm mb-6">
              <Link to="/marketplace" className="hover:text-white transition-colors">Marketplace</Link>
              <ChevronRight className="w-4 h-4" />
              <span className="text-white font-medium">Spares & Components</span>
            </nav>
            
            <div className="max-w-4xl">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
                  <Wrench className="w-7 h-7 text-white" />
                </div>
                <h1 className="text-3xl md:text-4xl font-bold text-white">
                  Spares & Components
                </h1>
              </div>
              <p className="text-green-100 text-lg mb-8 max-w-2xl">
                Certified EV spare parts, batteries, controllers & diagnostic tools for all vehicle types
              </p>
              
              {/* Search Bar */}
              <div className="max-w-xl">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    type="text"
                    placeholder="Search by part name, SKU, or vehicle model..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="pl-12 pr-4 py-4 text-base bg-white text-gray-900 border-0 rounded-xl shadow-lg focus:ring-2 focus:ring-green-300"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Categories Bar */}
        <section className="bg-white border-b border-gray-200 sticky top-[72px] z-40 shadow-sm">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-3 py-4 overflow-x-auto scrollbar-hide">
              <button
                onClick={() => handleFilterChange('category', '')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                  !filters.category
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Package className="w-4 h-4" />
                All Parts
              </button>
              {categories.map((cat) => {
                const config = categoryConfig[cat.name] || { icon: Package, bg: 'bg-gray-50', text: 'text-gray-700' };
                const Icon = config.icon;
                return (
                  <button
                    key={cat.name}
                    onClick={() => handleFilterChange('category', cat.name)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                      filters.category === cat.name
                        ? `bg-gradient-to-r ${config.color} text-white shadow-md`
                        : `${config.bg} ${config.text} hover:opacity-80`
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {cat.name}
                    <span className={`text-xs ${filters.category === cat.name ? 'text-white/80' : 'opacity-60'}`}>
                      ({cat.count})
                    </span>
                  </button>
                );
              })}
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
                      <Filter className="w-5 h-5 text-green-600" />
                      Filters
                    </h3>
                    {hasActiveFilters && (
                      <button onClick={clearFilters} className="text-sm text-green-600 hover:text-green-700 font-medium">
                        Clear all
                      </button>
                    )}
                  </div>

                  {/* Vehicle Type */}
                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-800 mb-3">Vehicle Type</label>
                    <div className="space-y-2">
                      {[
                        { value: '2W', label: '2-Wheeler EVs', icon: Bike },
                        { value: '3W', label: '3-Wheeler EVs', icon: Truck },
                        { value: '4W', label: '4-Wheeler EVs', icon: Car }
                      ].map((item) => (
                        <label key={item.value} className="flex items-center gap-3 cursor-pointer group">
                          <input
                            type="radio"
                            name="vehicleCategory"
                            checked={filters.vehicleCategory === item.value}
                            onChange={() => handleFilterChange('vehicleCategory', item.value)}
                            className="w-4 h-4 text-green-600 focus:ring-green-500 border-gray-300"
                          />
                          <item.icon className="w-4 h-4 text-gray-400 group-hover:text-green-600" />
                          <span className="text-sm text-gray-600 group-hover:text-gray-900">{item.label}</span>
                        </label>
                      ))}
                      {filters.vehicleCategory && (
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="vehicleCategory"
                            checked={!filters.vehicleCategory}
                            onChange={() => handleFilterChange('vehicleCategory', '')}
                            className="w-4 h-4 text-green-600 focus:ring-green-500 border-gray-300"
                          />
                          <span className="text-sm text-gray-600">All Vehicles</span>
                        </label>
                      )}
                    </div>
                  </div>

                  {/* Part Type */}
                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-800 mb-3">Part Type</label>
                    <div className="space-y-2">
                      {[
                        { value: 'oem', label: 'OEM Parts' },
                        { value: 'aftermarket', label: 'Aftermarket' },
                        { value: 'refurbished', label: 'Refurbished' }
                      ].map((type) => (
                        <label key={type.value} className="flex items-center gap-3 cursor-pointer group">
                          <input
                            type="radio"
                            name="oem_aftermarket"
                            checked={filters.oem_aftermarket === type.value}
                            onChange={() => handleFilterChange('oem_aftermarket', type.value)}
                            className="w-4 h-4 text-green-600 focus:ring-green-500 border-gray-300"
                          />
                          <span className="text-sm text-gray-600 group-hover:text-gray-900">{type.label}</span>
                        </label>
                      ))}
                      {filters.oem_aftermarket && (
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="oem_aftermarket"
                            checked={!filters.oem_aftermarket}
                            onChange={() => handleFilterChange('oem_aftermarket', '')}
                            className="w-4 h-4 text-green-600 focus:ring-green-500 border-gray-300"
                          />
                          <span className="text-sm text-gray-600">All Types</span>
                        </label>
                      )}
                    </div>
                  </div>

                  {/* Certified Only */}
                  <div className="mb-6">
                    <label className="flex items-center gap-3 cursor-pointer p-3 bg-green-50 rounded-xl hover:bg-green-100 transition-colors">
                      <input
                        type="checkbox"
                        checked={filters.is_certified}
                        onChange={(e) => handleFilterChange('is_certified', e.target.checked)}
                        className="w-4 h-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                      />
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="text-sm font-medium text-green-800">Battwheels Certified</span>
                      </div>
                    </label>
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
                <Button
                  variant="outline"
                  onClick={() => setShowMobileFilters(true)}
                  className="flex items-center gap-2"
                >
                  <Filter className="w-4 h-4" />
                  Filters
                  {hasActiveFilters && (
                    <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">Active</span>
                  )}
                </Button>
                <Link to="/marketplace/cart" className="relative p-2.5 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 shadow-sm">
                  <ShoppingCart className="w-5 h-5 text-gray-700" />
                  {getCartCount() > 0 && (
                    <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-medium">
                      {getCartCount()}
                    </span>
                  )}
                </Link>
              </div>

              {/* Products Grid */}
              <div className="flex-1">
                {/* Results Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                  <p className="text-gray-600">
                    Showing <span className="font-semibold text-gray-900">{products.length}</span> of{' '}
                    <span className="font-semibold text-gray-900">{totalProducts}</span> products
                  </p>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500">Sort:</span>
                    <select
                      value={filters.sort}
                      onChange={(e) => handleFilterChange('sort', e.target.value)}
                      className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
                    >
                      <option value="created_at">Newest First</option>
                      <option value="price_asc">Price: Low to High</option>
                      <option value="price_desc">Price: High to Low</option>
                      <option value="name">Name: A-Z</option>
                    </select>
                  </div>
                </div>

                {/* Products */}
                {loading ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 animate-pulse">
                        <div className="bg-gray-200 aspect-[4/3] rounded-xl mb-4" />
                        <div className="bg-gray-200 h-5 rounded w-3/4 mb-2" />
                        <div className="bg-gray-200 h-4 rounded w-1/2" />
                      </div>
                    ))}
                  </div>
                ) : products.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-100">
                    <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No products found</h3>
                    <p className="text-gray-600 mb-6">Try adjusting your filters or search terms</p>
                    <Button onClick={clearFilters} className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700">
                      Clear Filters
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                    {products.map((product) => (
                      <ProductCard key={product.id} product={product} onAddToCart={addToCart} toast={toast} />
                    ))}
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-3 mt-8">
                    <Button
                      variant="outline"
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage(p => p - 1)}
                      className="shadow-sm"
                    >
                      Previous
                    </Button>
                    <span className="text-sm text-gray-600 bg-white px-4 py-2 rounded-lg border border-gray-200">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      disabled={currentPage === totalPages}
                      onClick={() => setCurrentPage(p => p + 1)}
                      className="shadow-sm"
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
              {/* Vehicle Type */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-800 mb-3">Vehicle Type</label>
                <div className="space-y-2">
                  {['2W', '3W', '4W'].map((vc) => (
                    <label key={vc} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="mobileVehicleCategory"
                        checked={filters.vehicleCategory === vc}
                        onChange={() => handleFilterChange('vehicleCategory', vc)}
                        className="w-4 h-4 text-green-600"
                      />
                      <span className="text-sm text-gray-600">{vc} EVs</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" onClick={clearFilters} className="flex-1">Clear</Button>
                <Button onClick={() => setShowMobileFilters(false)} className="flex-1 bg-green-600 hover:bg-green-700">Apply</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product, onAddToCart, toast }) => {
  const stockStyles = {
    in_stock: 'bg-green-50 text-green-700',
    low_stock: 'bg-amber-50 text-amber-700',
    out_of_stock: 'bg-red-50 text-red-700'
  };

  const handleAddToCart = () => {
    onAddToCart(product);
    toast({
      title: "Added to Cart",
      description: `${product.name} has been added to your cart.`,
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 group">
      {/* Image */}
      <Link to={`/marketplace/product/${product.slug}`} className="block relative">
        <div className="aspect-[4/3] bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center overflow-hidden">
          {product.images?.[0] ? (
            <img src={product.images[0]} alt={product.name} className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300" />
          ) : (
            <Package className="w-16 h-16 text-gray-300" />
          )}
        </div>
        {/* Badges */}
        <div className="absolute top-3 left-3 flex flex-col gap-2">
          {product.is_certified && (
            <span className="bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xs px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm">
              <CheckCircle className="w-3 h-3" /> Certified
            </span>
          )}
          {product.oem_aftermarket === 'refurbished' && (
            <span className="bg-gradient-to-r from-purple-500 to-purple-600 text-white text-xs px-2.5 py-1 rounded-full shadow-sm">
              Refurbished
            </span>
          )}
        </div>
      </Link>

      {/* Content */}
      <div className="p-5">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <span className="font-medium">{product.category}</span>
          <span>•</span>
          <span className="font-mono text-gray-400">{product.sku}</span>
        </div>
        
        <Link to={`/marketplace/product/${product.slug}`}>
          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-green-600 transition-colors leading-snug">
            {product.name}
          </h3>
        </Link>

        {product.compatibility?.length > 0 && (
          <p className="text-xs text-gray-500 mb-3 line-clamp-1">
            Fits: {product.compatibility.slice(0, 2).join(', ')}
            {product.compatibility.length > 2 && ` +${product.compatibility.length - 2} more`}
          </p>
        )}

        {/* Price */}
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-xl font-bold text-gray-900">₹{product.final_price?.toLocaleString()}</span>
          {product.discount_percent > 0 && (
            <>
              <span className="text-sm text-gray-400 line-through">₹{product.base_price?.toLocaleString()}</span>
              <span className="text-xs font-medium text-green-600 bg-green-50 px-1.5 py-0.5 rounded">
                {product.discount_percent}% off
              </span>
            </>
          )}
        </div>

        {/* Stock & Add to Cart */}
        <div className="flex items-center justify-between">
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${stockStyles[product.stock_status]}`}>
            {product.stock_status === 'in_stock' ? 'In Stock' :
             product.stock_status === 'low_stock' ? `Only ${product.stock_quantity} left` : 'Out of Stock'}
          </span>
          <Button
            size="sm"
            disabled={product.stock_status === 'out_of_stock'}
            onClick={handleAddToCart}
            className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-sm"
            data-testid={`add-to-cart-${product.sku}`}
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Add
          </Button>
        </div>

        {/* Warranty */}
        {product.warranty_months > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-1.5 text-xs text-gray-500">
            <CheckCircle className="w-3.5 h-3.5 text-green-500" />
            {product.warranty_months} months warranty
          </div>
        )}
      </div>
    </div>
  );
};

export default SparesAndComponents;

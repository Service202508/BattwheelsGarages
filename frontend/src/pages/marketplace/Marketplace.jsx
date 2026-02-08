/**
 * Marketplace Main Page - Product Catalog with Filters
 * Extends Battwheels design system - industrial EV-tech aesthetic
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
  Filter,
  ShoppingCart,
  Package,
  Battery,
  Wrench,
  Truck,
  Recycle,
  CheckCircle,
  Star,
  ChevronDown,
  X,
  Zap,
  AlertCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Category Icons
const categoryIcons = {
  '2W Parts': <Zap className="w-5 h-5" />,
  '3W Parts': <Truck className="w-5 h-5" />,
  '4W Parts': <Package className="w-5 h-5" />,
  'Batteries': <Battery className="w-5 h-5" />,
  'Diagnostic Tools': <Wrench className="w-5 h-5" />,
  'Refurbished Components': <Recycle className="w-5 h-5" />
};

const Marketplace = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { addToCart, getCartCount, userRole } = useMarketplace();
  
  // State
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalProducts, setTotalProducts] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filters from URL
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
        setCategories(data.categories || []);
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

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    if (filters.category) params.set('category', filters.category);
    if (filters.vehicleCategory) params.set('vehicle', filters.vehicleCategory);
    if (filters.oem_aftermarket) params.set('type', filters.oem_aftermarket);
    if (filters.is_certified) params.set('certified', 'true');
    if (filters.minPrice) params.set('minPrice', filters.minPrice);
    if (filters.maxPrice) params.set('maxPrice', filters.maxPrice);
    if (filters.sort !== 'created_at') params.set('sort', filters.sort);
    setSearchParams(params);
  }, [filters, setSearchParams]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      category: '',
      vehicleCategory: '',
      oem_aftermarket: '',
      is_certified: false,
      minPrice: '',
      maxPrice: '',
      sort: 'created_at'
    });
    setCurrentPage(1);
  };

  const hasActiveFilters = filters.category || filters.vehicleCategory || filters.oem_aftermarket || filters.is_certified || filters.minPrice || filters.maxPrice;

  return (
    <>
      <Helmet>
        <title>EV Parts Marketplace | Battwheels Garages</title>
        <meta name="description" content="Shop genuine EV spare parts, batteries, controllers, and diagnostic tools. Certified components for 2W, 3W, 4W electric vehicles." />
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white py-12 md:py-16">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 bg-[#12B76A]/20 text-[#12B76A] px-4 py-2 rounded-full text-sm font-medium mb-4">
                <Zap className="w-4 h-4" />
                Powered by Battwheels OS
              </div>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
                EV Parts <span className="text-[#12B76A]">Marketplace</span>
              </h1>
              <p className="text-gray-300 text-lg mb-8">
                Certified spare parts, batteries & diagnostic tools for your electric vehicles
              </p>
              
              {/* Search Bar */}
              <div className="max-w-2xl mx-auto">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    type="text"
                    placeholder="Search by part name, SKU, or vehicle model..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="pl-12 pr-4 py-6 text-lg bg-white text-gray-900 border-0 rounded-xl shadow-lg"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Categories Bar */}
        <section className="bg-white border-b border-gray-200 sticky top-[72px] z-40">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-2 py-4 overflow-x-auto scrollbar-hide">
              <button
                onClick={() => handleFilterChange('category', '')}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  !filters.category
                    ? 'bg-[#12B76A] text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All Parts
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.name}
                  onClick={() => handleFilterChange('category', cat.name)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                    filters.category === cat.name
                      ? 'bg-[#12B76A] text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {categoryIcons[cat.name]}
                  {cat.name}
                  <span className="text-xs opacity-75">({cat.count})</span>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-8">
          <div className="container mx-auto px-4">
            <div className="flex flex-col lg:flex-row gap-8">
              {/* Filters Sidebar - Desktop */}
              <aside className="hidden lg:block w-64 flex-shrink-0">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-[160px]">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-semibold text-gray-900">Filters</h3>
                    {hasActiveFilters && (
                      <button
                        onClick={clearFilters}
                        className="text-sm text-[#12B76A] hover:underline"
                      >
                        Clear all
                      </button>
                    )}
                  </div>

                  {/* Vehicle Category */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Vehicle Type
                    </label>
                    <div className="space-y-2">
                      {['2W', '3W', '4W'].map((vc) => (
                        <label key={vc} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="vehicleCategory"
                            checked={filters.vehicleCategory === vc}
                            onChange={() => handleFilterChange('vehicleCategory', vc)}
                            className="text-[#12B76A] focus:ring-[#12B76A]"
                          />
                          <span className="text-sm text-gray-600">{vc} Electric Vehicles</span>
                        </label>
                      ))}
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="vehicleCategory"
                          checked={!filters.vehicleCategory}
                          onChange={() => handleFilterChange('vehicleCategory', '')}
                          className="text-[#12B76A] focus:ring-[#12B76A]"
                        />
                        <span className="text-sm text-gray-600">All Vehicles</span>
                      </label>
                    </div>
                  </div>

                  {/* Part Type */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Part Type
                    </label>
                    <div className="space-y-2">
                      {[
                        { value: 'oem', label: 'OEM Parts' },
                        { value: 'aftermarket', label: 'Aftermarket' },
                        { value: 'refurbished', label: 'Refurbished' }
                      ].map((type) => (
                        <label key={type.value} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="oem_aftermarket"
                            checked={filters.oem_aftermarket === type.value}
                            onChange={() => handleFilterChange('oem_aftermarket', type.value)}
                            className="text-[#12B76A] focus:ring-[#12B76A]"
                          />
                          <span className="text-sm text-gray-600">{type.label}</span>
                        </label>
                      ))}
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="oem_aftermarket"
                          checked={!filters.oem_aftermarket}
                          onChange={() => handleFilterChange('oem_aftermarket', '')}
                          className="text-[#12B76A] focus:ring-[#12B76A]"
                        />
                        <span className="text-sm text-gray-600">All Types</span>
                      </label>
                    </div>
                  </div>

                  {/* Certified Only */}
                  <div className="mb-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={filters.is_certified}
                        onChange={(e) => handleFilterChange('is_certified', e.target.checked)}
                        className="text-[#12B76A] focus:ring-[#12B76A] rounded"
                      />
                      <span className="text-sm text-gray-600 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-[#12B76A]" />
                        Battwheels Certified
                      </span>
                    </label>
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

              {/* Mobile Filter Button */}
              <div className="lg:hidden flex items-center justify-between mb-4">
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(true)}
                  className="flex items-center gap-2"
                >
                  <Filter className="w-4 h-4" />
                  Filters
                  {hasActiveFilters && (
                    <span className="bg-[#12B76A] text-white text-xs px-2 py-0.5 rounded-full">
                      Active
                    </span>
                  )}
                </Button>
                <Link
                  to="/marketplace/cart"
                  className="relative p-2 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  <ShoppingCart className="w-5 h-5 text-gray-700" />
                  {getCartCount() > 0 && (
                    <span className="absolute -top-1 -right-1 bg-[#12B76A] text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                      {getCartCount()}
                    </span>
                  )}
                </Link>
              </div>

              {/* Products Grid */}
              <div className="flex-1">
                {/* Results Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                  <p className="text-gray-600">
                    Showing <span className="font-medium text-gray-900">{products.length}</span> of{' '}
                    <span className="font-medium text-gray-900">{totalProducts}</span> products
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Sort by:</span>
                    <select
                      value={filters.sort}
                      onChange={(e) => handleFilterChange('sort', e.target.value)}
                      className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-[#12B76A] focus:border-[#12B76A]"
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
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse">
                        <div className="bg-gray-200 h-48 rounded-lg mb-4" />
                        <div className="bg-gray-200 h-4 rounded w-3/4 mb-2" />
                        <div className="bg-gray-200 h-4 rounded w-1/2" />
                      </div>
                    ))}
                  </div>
                ) : products.length === 0 ? (
                  <div className="text-center py-16">
                    <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No products found</h3>
                    <p className="text-gray-600 mb-4">Try adjusting your filters or search terms</p>
                    <Button onClick={clearFilters} className="bg-[#12B76A] hover:bg-[#0F9F5F]">
                      Clear Filters
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {products.map((product) => (
                      <ProductCard key={product.id} product={product} onAddToCart={addToCart} />
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

      {/* Mobile Filters Modal */}
      {showFilters && (
        <div className="fixed inset-0 bg-black/50 z-50 lg:hidden">
          <div className="absolute right-0 top-0 h-full w-80 bg-white shadow-xl overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Filters</h3>
              <button onClick={() => setShowFilters(false)}>
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="p-4">
              {/* Same filter content as sidebar */}
              {/* Vehicle Category */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Type</label>
                <div className="space-y-2">
                  {['2W', '3W', '4W'].map((vc) => (
                    <label key={vc} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="mobileVehicleCategory"
                        checked={filters.vehicleCategory === vc}
                        onChange={() => handleFilterChange('vehicleCategory', vc)}
                        className="text-[#12B76A]"
                      />
                      <span className="text-sm text-gray-600">{vc} EVs</span>
                    </label>
                  ))}
                </div>
              </div>
              {/* Add other filters... */}
              <div className="mt-6 flex gap-2">
                <Button variant="outline" onClick={clearFilters} className="flex-1">
                  Clear
                </Button>
                <Button onClick={() => setShowFilters(false)} className="flex-1 bg-[#12B76A] hover:bg-[#0F9F5F]">
                  Apply
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Product Card Component
const ProductCard = ({ product, onAddToCart }) => {
  const stockColor = {
    in_stock: 'text-green-600 bg-green-50',
    low_stock: 'text-orange-600 bg-orange-50',
    out_of_stock: 'text-red-600 bg-red-50'
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow group">
      {/* Image */}
      <Link to={`/marketplace/product/${product.slug}`} className="block relative">
        <div className="aspect-[4/3] bg-gray-100 flex items-center justify-center">
          {product.images?.[0] ? (
            <img
              src={product.images[0]}
              alt={product.name}
              className="object-cover w-full h-full group-hover:scale-105 transition-transform"
            />
          ) : (
            <Package className="w-16 h-16 text-gray-300" />
          )}
        </div>
        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          {product.is_certified && (
            <span className="bg-[#12B76A] text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Certified
            </span>
          )}
          {product.oem_aftermarket === 'refurbished' && (
            <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
              Refurbished
            </span>
          )}
        </div>
      </Link>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <span>{product.category}</span>
          <span>•</span>
          <span>SKU: {product.sku}</span>
        </div>
        
        <Link to={`/marketplace/product/${product.slug}`}>
          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-[#12B76A] transition-colors">
            {product.name}
          </h3>
        </Link>

        {/* Compatibility */}
        {product.compatibility?.length > 0 && (
          <p className="text-xs text-gray-500 mb-3 line-clamp-1">
            Fits: {product.compatibility.slice(0, 3).join(', ')}
            {product.compatibility.length > 3 && ` +${product.compatibility.length - 3} more`}
          </p>
        )}

        {/* Price & Stock */}
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="text-xl font-bold text-gray-900">₹{product.final_price?.toLocaleString()}</span>
            {product.discount_percent > 0 && (
              <>
                <span className="text-sm text-gray-400 line-through ml-2">
                  ₹{product.base_price?.toLocaleString()}
                </span>
                <span className="text-xs text-[#12B76A] ml-1">
                  {product.discount_percent}% off
                </span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className={`text-xs px-2 py-1 rounded-full ${stockColor[product.stock_status]}`}>
            {product.stock_status === 'in_stock' ? 'In Stock' :
             product.stock_status === 'low_stock' ? 'Low Stock' : 'Out of Stock'}
          </span>
          <Button
            size="sm"
            disabled={product.stock_status === 'out_of_stock'}
            onClick={() => onAddToCart(product)}
            className="bg-[#12B76A] hover:bg-[#0F9F5F] text-white"
          >
            <ShoppingCart className="w-4 h-4 mr-1" />
            Add
          </Button>
        </div>

        {/* Warranty Badge */}
        {product.warranty_months > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-1 text-xs text-gray-500">
            <CheckCircle className="w-3 h-3 text-[#12B76A]" />
            {product.warranty_months} months warranty
          </div>
        )}
      </div>
    </div>
  );
};

export default Marketplace;

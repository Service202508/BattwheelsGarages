/**
 * Product Detail Page
 * Detailed product view with specifications, compatibility, and add to cart
 */
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Button } from '../../components/ui/button';
import { useMarketplace } from '../../context/MarketplaceContext';
import { useToast } from '../../hooks/use-toast';
import {
  ShoppingCart,
  Package,
  CheckCircle,
  Truck,
  Shield,
  ArrowLeft,
  Plus,
  Minus,
  MapPin,
  Clock,
  AlertCircle,
  ChevronRight
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ProductDetail = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { addToCart, userRole, isAuthenticated } = useMarketplace();
  const { toast } = useToast();
  
  const [product, setProduct] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      try {
        // Fetch product by slug (need to search)
        const response = await fetch(`${API_URL}/api/marketplace/products?search=${slug}&role=${userRole}`);
        const data = await response.json();
        
        // Find exact match by slug
        const found = data.products?.find(p => p.slug === slug);
        if (found) {
          setProduct(found);
          // Fetch inventory
          const invResponse = await fetch(`${API_URL}/api/marketplace/inventory/${found.id}`);
          const invData = await invResponse.json();
          setInventory(invData);
        }
      } catch (error) {
        console.error('Error fetching product:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [slug, userRole]);

  const handleAddToCart = () => {
    if (product) {
      addToCart(product, quantity);
      toast({
        title: "Added to Cart",
        description: `${quantity}x ${product.name} has been added to your cart.`,
      });
    }
  };

  const handleBuyNow = () => {
    if (product) {
      addToCart(product, quantity);
      toast({
        title: "Proceeding to Checkout",
        description: `${quantity}x ${product.name} added.`,
      });
      navigate('/marketplace/checkout');
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-gray-50 py-8">
          <div className="container mx-auto px-4">
            <div className="animate-pulse">
              <div className="bg-gray-200 h-8 w-48 rounded mb-8" />
              <div className="grid md:grid-cols-2 gap-8">
                <div className="bg-gray-200 aspect-square rounded-xl" />
                <div className="space-y-4">
                  <div className="bg-gray-200 h-8 rounded w-3/4" />
                  <div className="bg-gray-200 h-4 rounded w-1/2" />
                  <div className="bg-gray-200 h-12 rounded w-1/3" />
                </div>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  if (!product) {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Product Not Found</h1>
            <p className="text-gray-600 mb-4">The product you&apos;re looking for doesn&apos;t exist.</p>
            <Button onClick={() => navigate('/marketplace')} className="bg-[#12B76A] hover:bg-[#0F9F5F]">
              Back to Marketplace
            </Button>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  const stockColor = {
    in_stock: 'text-green-600',
    low_stock: 'text-orange-600',
    out_of_stock: 'text-red-600'
  };

  return (
    <>
      <Helmet>
        <title>{product.name} | Battwheels Marketplace</title>
        <meta name="description" content={product.short_description || product.description?.slice(0, 160)} />
      </Helmet>

      <Header />

      <main className="min-h-screen bg-gray-50">
        {/* Breadcrumb */}
        <div className="bg-white border-b border-gray-200">
          <div className="container mx-auto px-4 py-3">
            <nav className="flex items-center gap-2 text-sm">
              <Link to="/marketplace" className="text-gray-500 hover:text-[#12B76A]">Marketplace</Link>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <Link to={`/marketplace?category=${encodeURIComponent(product.category)}`} className="text-gray-500 hover:text-[#12B76A]">
                {product.category}
              </Link>
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <span className="text-gray-900 font-medium truncate">{product.name}</span>
            </nav>
          </div>
        </div>

        <div className="container mx-auto px-4 py-8">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12">
            {/* Product Images */}
            <div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="aspect-square bg-gray-100 flex items-center justify-center">
                  {product.images?.[selectedImage] ? (
                    <img
                      src={product.images[selectedImage]}
                      alt={product.name}
                      className="object-contain w-full h-full"
                    />
                  ) : (
                    <Package className="w-32 h-32 text-gray-300" />
                  )}
                </div>
              </div>
              {/* Thumbnail Gallery */}
              {product.images?.length > 1 && (
                <div className="flex gap-2 mt-4">
                  {product.images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedImage(idx)}
                      className={`w-20 h-20 rounded-lg border-2 overflow-hidden ${
                        selectedImage === idx ? 'border-[#12B76A]' : 'border-gray-200'
                      }`}
                    >
                      <img src={img} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Product Info */}
            <div>
              {/* Badges */}
              <div className="flex flex-wrap gap-2 mb-4">
                {product.is_certified && (
                  <span className="inline-flex items-center gap-1 bg-[#12B76A]/10 text-[#12B76A] px-3 py-1 rounded-full text-sm font-medium">
                    <CheckCircle className="w-4 h-4" />
                    Battwheels Certified
                  </span>
                )}
                {product.oem_aftermarket === 'oem' && (
                  <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                    OEM Part
                  </span>
                )}
                {product.oem_aftermarket === 'refurbished' && (
                  <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-medium">
                    Refurbished
                  </span>
                )}
              </div>

              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                {product.name}
              </h1>

              <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                <span>SKU: <span className="font-mono text-gray-700">{product.sku}</span></span>
                <span>•</span>
                <span>{product.category}</span>
                {product.brand && (
                  <>
                    <span>•</span>
                    <span>Brand: {product.brand}</span>
                  </>
                )}
              </div>

              {/* Price */}
              <div className="bg-gray-50 rounded-xl p-4 mb-6">
                <div className="flex items-baseline gap-3">
                  <span className="text-3xl font-bold text-gray-900">
                    ₹{product.final_price?.toLocaleString()}
                  </span>
                  {product.discount_percent > 0 && (
                    <>
                      <span className="text-lg text-gray-400 line-through">
                        ₹{product.base_price?.toLocaleString()}
                      </span>
                      <span className="bg-[#12B76A] text-white px-2 py-0.5 rounded text-sm font-medium">
                        {product.discount_percent}% OFF
                      </span>
                    </>
                  )}
                </div>
                {product.discount_percent > 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    You save ₹{(product.base_price - product.final_price).toLocaleString()} with {userRole} pricing
                  </p>
                )}
              </div>

              {/* Stock Status */}
              <div className="flex items-center gap-4 mb-6">
                <span className={`flex items-center gap-1 font-medium ${stockColor[product.stock_status]}`}>
                  {product.stock_status === 'in_stock' && <CheckCircle className="w-5 h-5" />}
                  {product.stock_status === 'low_stock' && <AlertCircle className="w-5 h-5" />}
                  {product.stock_status === 'in_stock' ? 'In Stock' :
                   product.stock_status === 'low_stock' ? `Only ${product.stock_quantity} left` : 'Out of Stock'}
                </span>
              </div>

              {/* Quantity & Add to Cart */}
              {product.stock_status !== 'out_of_stock' && (
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                  <div className="flex items-center border border-gray-300 rounded-lg">
                    <button
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="p-3 hover:bg-gray-100"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                    <span className="px-6 py-3 font-medium min-w-[60px] text-center">{quantity}</span>
                    <button
                      onClick={() => setQuantity(Math.min(product.stock_quantity, quantity + 1))}
                      className="p-3 hover:bg-gray-100"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                  <Button
                    onClick={handleAddToCart}
                    className="flex-1 bg-white border-2 border-[#12B76A] text-[#12B76A] hover:bg-[#12B76A]/10"
                  >
                    <ShoppingCart className="w-5 h-5 mr-2" />
                    Add to Cart
                  </Button>
                  <Button
                    onClick={handleBuyNow}
                    className="flex-1 bg-[#12B76A] hover:bg-[#0F9F5F] text-white"
                  >
                    Buy Now
                  </Button>
                </div>
              )}

              {/* Delivery Info */}
              {inventory && (
                <div className="bg-blue-50 rounded-xl p-4 mb-6">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Truck className="w-5 h-5 text-blue-600" />
                    Delivery Information
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    <Clock className="w-4 h-4 inline mr-1" />
                    Estimated delivery: {inventory.estimated_delivery}
                  </p>
                  {inventory.nearest_locations?.length > 0 && (
                    <div className="text-sm text-gray-600">
                      <MapPin className="w-4 h-4 inline mr-1" />
                      Available at: {inventory.nearest_locations[0].location}
                    </div>
                  )}
                </div>
              )}

              {/* Warranty */}
              {product.warranty_months > 0 && (
                <div className="flex items-center gap-3 p-4 border border-gray-200 rounded-xl mb-6">
                  <Shield className="w-8 h-8 text-[#12B76A]" />
                  <div>
                    <p className="font-medium text-gray-900">{product.warranty_months} Months Warranty</p>
                    <p className="text-sm text-gray-500">Covered by Battwheels service guarantee</p>
                  </div>
                </div>
              )}

              {/* Short Description */}
              <p className="text-gray-600 mb-6">
                {product.short_description || product.description}
              </p>

              {/* Compatibility */}
              {product.compatibility?.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Compatible Vehicles</h3>
                  <div className="flex flex-wrap gap-2">
                    {product.compatibility.map((model, idx) => (
                      <span key={idx} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                        {model}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Product Details Tabs */}
          <div className="mt-12">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="border-b border-gray-200">
                <nav className="flex">
                  <button className="px-6 py-4 text-sm font-medium text-[#12B76A] border-b-2 border-[#12B76A]">
                    Description
                  </button>
                  <button className="px-6 py-4 text-sm font-medium text-gray-500 hover:text-gray-700">
                    Specifications
                  </button>
                </nav>
              </div>
              <div className="p-6">
                <div className="prose max-w-none">
                  <p className="text-gray-600 whitespace-pre-line">{product.description}</p>
                </div>

                {/* Specifications Table */}
                {product.specifications && Object.keys(product.specifications).length > 0 && (
                  <div className="mt-8">
                    <h3 className="font-semibold text-gray-900 mb-4">Technical Specifications</h3>
                    <table className="w-full">
                      <tbody className="divide-y divide-gray-200">
                        {Object.entries(product.specifications).map(([key, value]) => (
                          <tr key={key}>
                            <td className="py-3 text-sm text-gray-500 capitalize w-1/3">
                              {key.replace(/_/g, ' ')}
                            </td>
                            <td className="py-3 text-sm text-gray-900 font-medium">
                              {Array.isArray(value) ? value.join(', ') : String(value)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
};

export default ProductDetail;

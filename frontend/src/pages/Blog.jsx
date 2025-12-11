import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import SEO from '../components/common/SEO';
import GearBackground from '../components/common/GearBackground';
import { blogsApi } from '../utils/api';
import { blogPosts as mockBlogs } from '../data/mockData';
import { Calendar, User, ArrowRight, Loader2, Tag } from 'lucide-react';

const Blog = () => {
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = ['all', 'Fleet Ops', 'EV Tech Deep Dive', 'Industry News', 'Company Updates', 'Tips & Guides'];

  useEffect(() => {
    fetchBlogs();
  }, [selectedCategory]);

  const fetchBlogs = async () => {
    try {
      setLoading(true);
      const params = selectedCategory !== 'all' ? { category: selectedCategory } : {};
      const data = await blogsApi.getAll(params);
      
      if (data.blogs && data.blogs.length > 0) {
        setBlogs(data.blogs);
      } else {
        // Fallback to mock data
        console.log('No blogs from API, using mock data');
        const filtered = selectedCategory === 'all' 
          ? mockBlogs 
          : mockBlogs.filter(b => b.category === selectedCategory);
        setBlogs(filtered);
      }
    } catch (err) {
      console.error('Error fetching blogs:', err);
      // Fallback to mock data on error
      const filtered = selectedCategory === 'all' 
        ? mockBlogs 
        : mockBlogs.filter(b => b.category === selectedCategory);
      setBlogs(filtered);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {/* Rotating Gears Background */}
      <GearBackground variant="blog" />
      
      <SEO 
        title="Blog | Battwheels Garages - EV Industry Insights & Tips"
        description="Latest insights on EV maintenance, fleet operations, industry news, and expert tips from Battwheels Garages."
        url="/blog"
      />
      
      <Header />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-600 to-indigo-700 py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Battwheels Blog
          </h1>
          <p className="text-xl text-purple-100 max-w-3xl mx-auto">
            Insights, tips, and updates from India&apos;s EV aftersales experts
          </p>
        </div>
      </section>

      {/* Category Filter */}
      <section className="py-8 border-b bg-white sticky top-0 z-10">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap gap-2 justify-center">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {category === 'all' ? 'All Posts' : category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Blog Grid */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
              <span className="ml-3 text-gray-600">Loading posts...</span>
            </div>
          ) : blogs.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-500 text-lg">No blog posts found in this category.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {blogs.map((blog) => (
                <article
                  key={blog.id}
                  className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 group"
                >
                  {/* Thumbnail */}
                  <div className="relative h-48 bg-gradient-to-br from-purple-100 to-indigo-100 overflow-hidden">
                    {blog.thumbnail_image || blog.image ? (
                      <img
                        src={blog.thumbnail_image || blog.image}
                        alt={blog.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-6xl">📝</span>
                      </div>
                    )}
                    {blog.category && (
                      <span className="absolute top-4 left-4 px-3 py-1 bg-purple-600 text-white text-xs font-medium rounded-full">
                        {blog.category}
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-3 line-clamp-2 group-hover:text-purple-600 transition-colors">
                      {blog.title}
                    </h2>
                    <p className="text-gray-600 mb-4 line-clamp-3">
                      {blog.excerpt || blog.content?.substring(0, 150)}...
                    </p>

                    {/* Meta */}
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {formatDate(blog.created_at || blog.published_at || blog.date)}
                      </span>
                      {blog.author && (
                        <span className="flex items-center">
                          <User className="w-4 h-4 mr-1" />
                          {blog.author}
                        </span>
                      )}
                    </div>

                    {/* Read More */}
                    <Link
                      to={`/blog/${blog.slug}`}
                      className="inline-flex items-center text-purple-600 font-medium hover:text-purple-700"
                    >
                      Read More
                      <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Newsletter CTA */}
      <section className="py-16 bg-gradient-to-r from-purple-600 to-indigo-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Stay Updated with EV Industry Insights
          </h2>
          <p className="text-purple-100 mb-8 max-w-2xl mx-auto">
            Subscribe to our newsletter for the latest tips, industry news, and exclusive content
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 px-4 py-3 rounded-lg focus:ring-2 focus:ring-purple-300 outline-none"
            />
            <button className="px-6 py-3 bg-white text-purple-600 font-bold rounded-lg hover:bg-purple-50 transition-colors">
              Subscribe
            </button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Blog;

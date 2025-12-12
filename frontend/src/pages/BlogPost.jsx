import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import DOMPurify from 'dompurify';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import { blogsApi } from '../utils/api';
import { getBlogSchema } from '../utils/schema';
import { blogPosts as mockBlogs } from '../data/mockData';
import { Calendar, User, ArrowLeft, Loader2, Share2, Tag } from 'lucide-react';

const BlogPost = () => {
  const { slug } = useParams();
  const [blog, setBlog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBlog();
  }, [slug]);

  const fetchBlog = async () => {
    try {
      setLoading(true);
      const data = await blogsApi.getBySlug(slug);
      setBlog(data);
    } catch (err) {
      console.error('Error fetching blog:', err);
      // Fallback to mock data
      const mockBlog = mockBlogs.find(b => b.slug === slug);
      if (mockBlog) {
        setBlog(mockBlog);
      } else {
        setError('Blog post not found');
      }
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

  const renderContent = (content) => {
    if (!content) return null;
    // Sanitize HTML content to prevent XSS
    const sanitizedContent = DOMPurify.sanitize(content, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre'],
      ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'target', 'rel']
    });
    return <div dangerouslySetInnerHTML={{ __html: sanitizedContent }} />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center items-center py-40">
          <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading post...</span>
        </div>
        <Footer />
      </div>
    );
  }

  if (error || !blog) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Post Not Found</h1>
          <p className="text-gray-600 mb-8">The blog post you are looking for does not exist.</p>
          <Link to="/blog" className="text-purple-600 hover:text-purple-700 font-medium">
            ← Back to Blog
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  const siteUrl = 'https://battwheelsgarages.in';
  const pageUrl = `${siteUrl}/blog/${blog.slug}`;
  const pageTitle = blog.meta_title || blog.title;
  const pageDesc = blog.meta_desc || blog.excerpt || blog.content?.substring(0, 160);
  const pageImage = blog.og_image || blog.thumbnail_image || `${siteUrl}/assets/battwheels-logo-new.png`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* SEO Meta Tags */}
      <Helmet>
        <title>{pageTitle} | Battwheels Garages Blog</title>
        <meta name="description" content={pageDesc} />
        <link rel="canonical" href={pageUrl} />

        {/* OpenGraph */}
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={pageDesc} />
        <meta property="og:image" content={pageImage} />
        <meta property="og:url" content={pageUrl} />
        <meta property="og:type" content="article" />
        <meta property="og:site_name" content="Battwheels Garages" />
        
        {/* Article Meta */}
        <meta property="article:published_time" content={blog.created_at || blog.published_at} />
        {blog.category && <meta property="article:section" content={blog.category} />}

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={pageDesc} />
        <meta name="twitter:image" content={pageImage} />

        {/* JSON-LD Schema */}
        <script type="application/ld+json">
          {JSON.stringify(getBlogSchema(blog))}
        </script>
      </Helmet>

      <Header />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-600 to-indigo-700 py-16">
        <div className="container mx-auto px-4">
          <Link to="/blog" className="inline-flex items-center text-purple-200 hover:text-white mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Blog
          </Link>
          
          {blog.category && (
            <span className="inline-block px-3 py-1 bg-white/20 text-white text-sm font-medium rounded-full mb-4">
              {blog.category}
            </span>
          )}
          
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6 max-w-4xl">
            {blog.title}
          </h1>
          
          <div className="flex flex-wrap items-center gap-4 text-purple-200">
            <span className="flex items-center">
              <Calendar className="w-4 h-4 mr-2" />
              {formatDate(blog.created_at || blog.published_at || blog.date)}
            </span>
            {blog.author && (
              <span className="flex items-center">
                <User className="w-4 h-4 mr-2" />
                {blog.author}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Content Section */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            {/* Featured Image */}
            {(blog.thumbnail_image || blog.image) && (
              <div className="mb-8 rounded-xl overflow-hidden shadow-lg">
                <img
                  src={blog.thumbnail_image || blog.image}
                  alt={blog.title}
                  className="w-full h-auto"
                />
              </div>
            )}

            {/* Blog Content */}
            <article className="prose prose-lg max-w-none">
              {blog.content_html ? (
                renderContent(blog.content_html)
              ) : blog.content ? (
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {blog.content}
                </div>
              ) : (
                <p className="text-gray-600">No content available.</p>
              )}
            </article>

            {/* Tags */}
            {blog.tags && blog.tags.length > 0 && (
              <div className="mt-8 pt-8 border-t">
                <div className="flex items-center flex-wrap gap-2">
                  <Tag className="w-4 h-4 text-gray-500" />
                  {blog.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Share Section */}
            <div className="mt-8 pt-8 border-t">
              <div className="flex items-center justify-between">
                <span className="flex items-center text-gray-600">
                  <Share2 className="w-5 h-5 mr-2" />
                  Share this article
                </span>
                <div className="flex gap-3">
                  <a
                    href={`https://twitter.com/intent/tweet?url=${encodeURIComponent(pageUrl)}&text=${encodeURIComponent(blog.title)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    𝕏
                  </a>
                  <a
                    href={`https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(pageUrl)}&title=${encodeURIComponent(blog.title)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    in
                  </a>
                  <a
                    href={`https://wa.me/?text=${encodeURIComponent(blog.title + ' ' + pageUrl)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    📱
                  </a>
                </div>
              </div>
            </div>

            {/* CTA */}
            <div className="mt-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-8 text-center">
              <h3 className="text-2xl font-bold text-white mb-4">
                Need EV Service?
              </h3>
              <p className="text-green-100 mb-6">
                Book onsite diagnosis and repair for your electric vehicle
              </p>
              <Link
                to="/book-service"
                className="inline-block px-8 py-3 bg-white text-green-600 font-bold rounded-xl hover:bg-green-50 transition-colors"
              >
                Book Service Now
              </Link>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default BlogPost;

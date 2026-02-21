import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import DOMPurify from 'dompurify';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import GearBackground from '../components/common/GearBackground';
import { blogsApi } from '../utils/api';
import { getBlogSchema, getBreadcrumbSchema } from '../utils/schema';
import { blogPosts as mockBlogs } from '../data/mockData';
import { Calendar, User, ArrowLeft, Loader2, Share2, Tag, ChevronRight } from 'lucide-react';

const BlogPost = () => {
  const { slug } = useParams();
  const [blog, setBlog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBlog();
    // Scroll to top on page load
    window.scrollTo(0, 0);
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

  // Get related posts (same category, excluding current)
  const relatedPosts = useMemo(() => {
    if (!blog) return [];
    return mockBlogs
      .filter(b => b.slug !== slug && b.category === blog.category)
      .slice(0, 3);
  }, [blog, slug]);

  // Get more posts if not enough in same category
  const moreFromBlog = useMemo(() => {
    if (relatedPosts.length >= 3 || !blog) return [];
    const needed = 3 - relatedPosts.length;
    return mockBlogs
      .filter(b => b.slug !== slug && b.category !== blog.category)
      .slice(0, needed);
  }, [blog, slug, relatedPosts]);

  const allRelated = [...relatedPosts, ...moreFromBlog];

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDateISO = (dateString) => {
    if (!dateString) return new Date().toISOString();
    return new Date(dateString).toISOString();
  };

  // Convert markdown-style content to proper HTML with headings
  const renderContent = (content) => {
    if (!content) return null;
    
    // Convert markdown headers to HTML
    let htmlContent = content
      // Convert ## headings to h2
      .replace(/^## (.+)$/gm, '<h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">$1</h2>')
      // Convert ### headings to h3
      .replace(/^### (.+)$/gm, '<h3 class="text-xl font-semibold text-gray-800 mt-6 mb-3">$1</h3>')
      // Convert **bold** to strong
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Convert *italic* to em
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Convert - list items to ul/li
      .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
      // Convert numbered list items
      .replace(/^\d+\. (.+)$/gm, '<li class="ml-4">$1</li>')
      // Convert | table rows (simplified)
      .replace(/^\|(.+)\|$/gm, '<tr><td class="border px-4 py-2">$1</td></tr>')
      // Convert line breaks to paragraphs
      .replace(/\n\n/g, '</p><p class="text-gray-700 leading-relaxed mb-4">');
    
    // Wrap in paragraphs
    htmlContent = `<p class="text-gray-700 leading-relaxed mb-4">${htmlContent}</p>`;
    
    // Clean up empty paragraphs
    htmlContent = htmlContent.replace(/<p class="[^"]*"><\/p>/g, '');
    
    // Sanitize HTML content to prevent XSS
    const sanitizedContent = DOMPurify.sanitize(htmlContent, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'span', 'div'],
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
  const pageTitle = blog.metaTitle || blog.meta_title || blog.title;
  const pageDesc = blog.metaDescription || blog.meta_desc || blog.excerpt || blog.content?.substring(0, 160);
  const pageImage = blog.og_image || blog.thumbnail_image || blog.image || `${siteUrl}/assets/battwheels-logo-new.png`;

  // Breadcrumb schema
  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": siteUrl
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": "Blog",
        "item": `${siteUrl}/blog`
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": blog.title,
        "item": pageUrl
      }
    ]
  };

  // Enhanced BlogPosting schema
  const blogSchema = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": pageUrl
    },
    "headline": pageTitle,
    "description": pageDesc,
    "image": pageImage,
    "datePublished": formatDateISO(blog.date || blog.created_at || blog.published_at),
    "dateModified": formatDateISO(blog.updated_at || blog.date || blog.created_at),
    "author": {
      "@type": "Organization",
      "name": "Battwheels Garages",
      "url": siteUrl
    },
    "publisher": {
      "@type": "Organization",
      "name": "Battwheels Garages",
      "logo": {
        "@type": "ImageObject",
        "url": `${siteUrl}/assets/battwheels-logo-new.png`
      }
    },
    "keywords": blog.tags?.join(', ') || '',
    "articleSection": blog.category,
    "wordCount": blog.content?.split(/\s+/).length || 1000
  };

  return (
    <div className="min-h-screen bg-gray-50 relative">
      <GearBackground variant="default" />
      
      {/* Enhanced SEO Meta Tags */}
      <Helmet>
        {/* Primary Meta Tags */}
        <title>{pageTitle}</title>
        <meta name="description" content={pageDesc} />
        <meta name="keywords" content={blog.tags?.join(', ') || 'EV service, electric vehicle repair, EV maintenance'} />
        <link rel="canonical" href={pageUrl} />
        
        {/* Ensure indexing */}
        <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
        <meta name="googlebot" content="index, follow" />

        {/* OpenGraph Tags */}
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={pageDesc} />
        <meta property="og:image" content={pageImage} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:url" content={pageUrl} />
        <meta property="og:type" content="article" />
        <meta property="og:site_name" content="Battwheels Garages" />
        <meta property="og:locale" content="en_IN" />
        
        {/* Article Meta */}
        <meta property="article:published_time" content={formatDateISO(blog.date || blog.created_at)} />
        <meta property="article:modified_time" content={formatDateISO(blog.updated_at || blog.date)} />
        <meta property="article:author" content="Battwheels Garages" />
        {blog.category && <meta property="article:section" content={blog.category} />}
        {blog.tags?.map((tag, i) => (
          <meta key={i} property="article:tag" content={tag} />
        ))}

        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={pageDesc} />
        <meta name="twitter:image" content={pageImage} />

        {/* JSON-LD Structured Data */}
        <script type="application/ld+json">
          {JSON.stringify(blogSchema)}
        </script>
        <script type="application/ld+json">
          {JSON.stringify(breadcrumbSchema)}
        </script>
      </Helmet>

      <Header />

      {/* Breadcrumb Navigation */}
      <nav className="bg-white border-b" aria-label="Breadcrumb">
        <div className="container mx-auto px-4 py-3">
          <ol className="flex items-center space-x-2 text-sm">
            <li>
              <Link to="/" className="text-gray-500 hover:text-green-600">Home</Link>
            </li>
            <li className="flex items-center">
              <ChevronRight className="w-4 h-4 text-gray-400 mx-1" />
              <Link to="/blog" className="text-gray-500 hover:text-green-600">Blog</Link>
            </li>
            {blog.category && (
              <li className="flex items-center">
                <ChevronRight className="w-4 h-4 text-gray-400 mx-1" />
                <span className="text-gray-500">{blog.category}</span>
              </li>
            )}
            <li className="flex items-center">
              <ChevronRight className="w-4 h-4 text-gray-400 mx-1" />
              <span className="text-gray-900 font-medium truncate max-w-xs">{blog.title}</span>
            </li>
          </ol>
        </div>
      </nav>

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
          
          {/* H1 - Primary keyword in title */}
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6 max-w-4xl">
            {blog.title}
          </h1>
          
          <div className="flex flex-wrap items-center gap-4 text-purple-200">
            <span className="flex items-center">
              <Calendar className="w-4 h-4 mr-2" />
              <time dateTime={formatDateISO(blog.date || blog.created_at)}>
                {formatDate(blog.created_at || blog.published_at || blog.date)}
              </time>
            </span>
            {blog.author && (
              <span className="flex items-center">
                <User className="w-4 h-4 mr-2" />
                {blog.author}
              </span>
            )}
            {blog.content && (
              <span className="text-purple-300">
                {Math.ceil(blog.content.split(/\s+/).length / 200)} min read
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
              <figure className="mb-8 rounded-xl overflow-hidden shadow-lg">
                <img
                  src={blog.thumbnail_image || blog.image}
                  alt={blog.title}
                  className="w-full h-auto"
                  loading="eager"
                />
                <figcaption className="sr-only">{blog.title}</figcaption>
              </figure>
            )}

            {/* Blog Content - Rendered with proper H2/H3 hierarchy */}
            <article className="prose prose-lg max-w-none" itemScope itemType="https://schema.org/Article">
              <meta itemProp="headline" content={blog.title} />
              <meta itemProp="datePublished" content={formatDateISO(blog.date || blog.created_at)} />
              <meta itemProp="author" content="Battwheels Garages" />
              
              {blog.content_html ? (
                <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(blog.content_html) }} />
              ) : blog.content ? (
                renderContent(blog.content)
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
                      className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full hover:bg-gray-200 transition-colors"
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
                    aria-label="Share on Twitter"
                  >
                    𝕏
                  </a>
                  <a
                    href={`https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(pageUrl)}&title=${encodeURIComponent(blog.title)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                    aria-label="Share on LinkedIn"
                  >
                    in
                  </a>
                  <a
                    href={`https://wa.me/?text=${encodeURIComponent(blog.title + ' ' + pageUrl)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                    aria-label="Share on WhatsApp"
                  >
                    📱
                  </a>
                </div>
              </div>
            </div>

            {/* CTA */}
            <div className="mt-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-8 text-center">
              <h2 className="text-2xl font-bold text-white mb-4">
                Need EV Service in Delhi NCR?
              </h2>
              <p className="text-green-100 mb-6">
                Book onsite diagnosis and repair for your electric vehicle - no towing required
              </p>
              <a
                href="https://battwheelsgarages.battwheels.com/submit-ticket"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block px-8 py-3 bg-white text-green-600 font-bold rounded-xl hover:bg-green-50 transition-colors"
              >
                Book Service Now
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Related Articles Section - Critical for Internal Linking */}
      {allRelated.length > 0 && (
        <section className="py-16 bg-gray-100">
          <div className="container mx-auto px-4">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-8 text-center">
              Related Articles
            </h2>
            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {allRelated.map((post) => (
                <article key={post.id} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 group">
                  <Link to={`/blog/${post.slug}`}>
                    <div className="relative h-40 bg-gradient-to-br from-purple-100 to-indigo-100 overflow-hidden">
                      {post.image ? (
                        <img
                          src={post.image}
                          alt={post.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <span className="text-4xl">📝</span>
                        </div>
                      )}
                      {post.category && (
                        <span className="absolute top-3 left-3 px-2 py-1 bg-purple-600 text-white text-xs font-medium rounded-full">
                          {post.category}
                        </span>
                      )}
                    </div>
                    <div className="p-5">
                      <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2 group-hover:text-purple-600 transition-colors">
                        {post.title}
                      </h3>
                      <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                        {post.excerpt || post.content?.substring(0, 100)}...
                      </p>
                      <span className="text-purple-600 text-sm font-medium">
                        Read More →
                      </span>
                    </div>
                  </Link>
                </article>
              ))}
            </div>
            
            {/* View All Blogs Link */}
            <div className="text-center mt-10">
              <Link 
                to="/blog" 
                className="inline-flex items-center px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors"
              >
                View All Blog Posts
                <ChevronRight className="w-4 h-4 ml-2" />
              </Link>
            </div>
          </div>
        </section>
      )}

      <Footer />
    </div>
  );
};

export default BlogPost;

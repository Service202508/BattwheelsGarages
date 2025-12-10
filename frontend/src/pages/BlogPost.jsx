import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { Button } from '../components/ui/button';
import { blogPosts } from '../data/mockData';
import { Calendar, ArrowLeft } from 'lucide-react';

const BlogPost = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const post = blogPosts.find(p => p.slug === slug);

  if (!post) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Post Not Found</h1>
          <Button onClick={() => navigate('/blog')}>Back to Blog</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <Button 
                variant="ghost" 
                className="mb-6"
                onClick={() => navigate('/blog')}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Blog
              </Button>
              
              <div className="flex items-center space-x-4 mb-6">
                <span className="text-sm font-semibold text-green-600 bg-green-100 px-3 py-1 rounded-full">
                  {post.category}
                </span>
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="w-4 h-4 mr-1" />
                  {new Date(post.date).toLocaleDateString('en-US', { 
                    month: 'long', 
                    day: 'numeric', 
                    year: 'numeric' 
                  })}
                </div>
              </div>
              
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                {post.title}
              </h1>
              <p className="text-xl text-gray-600">{post.excerpt}</p>
            </div>
          </div>
        </section>

        {/* Featured Image */}
        <section className="py-12 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <img 
                src={post.image} 
                alt={post.title}
                className="w-full h-96 object-cover rounded-2xl shadow-xl"
              />
            </div>
          </div>
        </section>

        {/* Content */}
        <section className="pb-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto prose prose-lg">
              <p className="text-gray-700 leading-relaxed mb-6">
                {/* Sample content - in real app this would come from CMS */}
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
              </p>
              
              <h2 className="text-2xl font-bold text-gray-900 mt-8 mb-4">Key Takeaways</h2>
              <ul className="list-disc pl-6 text-gray-700 space-y-2">
                <li>Regular EV maintenance extends battery life and vehicle performance</li>
                <li>Onsite diagnostics reduce downtime for fleet operations</li>
                <li>Preventive maintenance is more cost-effective than reactive repairs</li>
                <li>Tech-enabled service tracking improves operational transparency</li>
              </ul>

              <p className="text-gray-700 leading-relaxed mt-6">
                Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
              </p>

              {/* CTA */}
              <div className="bg-green-50 border-l-4 border-green-600 p-6 rounded-lg mt-8">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Need EV Service?</h3>
                <p className="text-gray-700 mb-4">Get your EV serviced by our expert technicians with onsite support available.</p>
                <Button 
                  onClick={() => navigate('/book-service')}
                  className="bg-green-600 hover:bg-green-700"
                >
                  Book Service Now
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default BlogPost;
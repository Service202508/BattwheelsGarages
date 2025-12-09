import React from 'react';
import { Target, Eye, Leaf } from 'lucide-react';

const AboutSection = () => {
  return (
    <section id="about" className="py-20 bg-white">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Years Of Expertise in <span className="text-green-600">Electric Vehicle Maintenance</span>
            </h2>
            <p className="text-gray-600 mb-6 leading-relaxed">
              Battwheels Garages has redefined the after sales experience of EV customers with our immediate assistance for electric vehicle repair and maintenance service. Holding years of expertise in offering proactive care to electronic vehicles, we ensure minimal downtime and maximum efficiency of your electric vehicles.
            </p>
            <p className="text-gray-600 mb-8 leading-relaxed">
              We have a team of professional EV repair and servicing experts who put their best efforts to cater to the needs of customers. Whether it is an e-rickshaw, two-wheelers or other types of EVs, our dedicated team is always ready to resolve issues on the spot.
            </p>

            {/* Mission */}
            <div className="bg-green-50 p-6 rounded-xl mb-6">
              <div className="flex items-start space-x-4">
                <div className="bg-green-600 p-3 rounded-lg flex-shrink-0">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Our Mission</h3>
                  <p className="text-gray-600 text-sm">
                    To support India's eco-friendly movement through the EV revolution. Since our inception, we have served thousands of businesses and individual owners by offering reliable, swift and expert services.
                  </p>
                </div>
              </div>
            </div>

            {/* Vision */}
            <div className="bg-green-50 p-6 rounded-xl">
              <div className="flex items-start space-x-4">
                <div className="bg-green-600 p-3 rounded-lg flex-shrink-0">
                  <Eye className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Our Vision</h3>
                  <p className="text-gray-600 text-sm">
                    To constantly strive to keep ourselves updated with ongoing technological advancements so that we can meet our customer's requirements in the best way. We understand the value of time and deliver faster, smarter and efficient EV servicing.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Image */}
          <div className="relative">
            <img 
              src="https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=800&h=900&fit=crop" 
              alt="EV Mechanic at work" 
              className="rounded-2xl shadow-2xl"
            />
            {/* Sustainability Badge */}
            <div className="absolute -bottom-6 -right-6 bg-white p-6 rounded-xl shadow-xl">
              <div className="flex items-center space-x-4">
                <div className="bg-green-100 p-3 rounded-full">
                  <Leaf className="w-8 h-8 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Sustainability</p>
                  <p className="text-xs text-gray-600">That Serves You Better</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sustainability Section */}
        <div className="mt-20 bg-gradient-to-r from-green-600 to-green-500 rounded-2xl p-8 md:p-12 text-white">
          <div className="text-center max-w-3xl mx-auto">
            <Leaf className="w-12 h-12 mx-auto mb-4" />
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              Sustainability That Serves You Better
            </h3>
            <p className="text-green-50 leading-relaxed">
              Sustainability is the main factor in whatever we deliver to our customers. By choosing our eco-friendly EV repair and servicing, we can conserve energy and create a greener future. Our commitment to creating a greener planet will give us better products, smarter services, and happy customers because a healthier earth means a healthy life for everyone.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
import React from 'react';
import { Star, Award, TrendingUp, Trophy, Medal } from 'lucide-react';

const AchievementsSection = () => {
  const achievements = [
    {
      id: 1,
      icon: Star,
      title: '4.9',
      subtitle: 'Star Rated',
      description: 'on Google',
      color: 'from-yellow-400 to-orange-500',
      bgColor: 'bg-yellow-50',
      iconColor: 'text-yellow-500'
    },
    {
      id: 2,
      icon: Award,
      title: 'Rising Startup',
      subtitle: 'Award',
      description: 'By Business Connect India',
      color: 'from-blue-500 to-indigo-600',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-500'
    },
    {
      id: 3,
      icon: TrendingUp,
      title: '72',
      subtitle: 'NPS Score',
      description: 'Customer Satisfaction',
      color: 'from-green-500 to-emerald-600',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-500'
    },
    {
      id: 4,
      icon: Trophy,
      title: 'Young Entrepreneur',
      subtitle: 'Award',
      description: 'By DPIIT',
      color: 'from-purple-500 to-pink-500',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-500'
    },
    {
      id: 5,
      icon: Medal,
      title: 'Recognition',
      subtitle: 'Certificate',
      description: 'By Skill India Development',
      color: 'from-teal-500 to-cyan-500',
      bgColor: 'bg-teal-50',
      iconColor: 'text-teal-500'
    }
  ];

  return (
    <section className="py-12 md:py-16 bg-gradient-to-b from-white to-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm font-medium mb-4">
            <Award className="w-4 h-4 mr-2" />
            Awards & Recognition
          </div>
          <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
            Trusted & Recognized Nationwide
          </h2>
          <p className="text-base md:text-lg text-gray-600 max-w-2xl mx-auto">
            Our commitment to excellence has been acknowledged by leading organizations
          </p>
        </div>

        {/* Achievements Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 md:gap-6 max-w-6xl mx-auto">
          {achievements.map((achievement, index) => (
            <div
              key={achievement.id}
              className="group relative bg-white rounded-2xl p-5 md:p-6 shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-100 overflow-hidden"
              style={{
                animationDelay: `${index * 100}ms`
              }}
            >
              {/* Background Gradient on Hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${achievement.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              
              {/* Icon */}
              <div className={`${achievement.bgColor} w-12 h-12 md:w-14 md:h-14 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <achievement.icon className={`w-6 h-6 md:w-7 md:h-7 ${achievement.iconColor}`} />
              </div>

              {/* Content */}
              <div>
                <h3 className={`text-xl md:text-2xl font-bold bg-gradient-to-r ${achievement.color} bg-clip-text text-transparent mb-1`}>
                  {achievement.title}
                </h3>
                <p className="text-sm md:text-base font-semibold text-gray-800 mb-1">
                  {achievement.subtitle}
                </p>
                <p className="text-xs md:text-sm text-gray-500">
                  {achievement.description}
                </p>
              </div>

              {/* Decorative Element */}
              <div className={`absolute -bottom-4 -right-4 w-20 h-20 bg-gradient-to-br ${achievement.color} opacity-10 rounded-full blur-xl group-hover:opacity-20 transition-opacity`} />
            </div>
          ))}
        </div>

        {/* Trust Indicators */}
        <div className="mt-10 flex flex-wrap justify-center items-center gap-6 md:gap-10">
          <div className="flex items-center gap-2 text-gray-500">
            <div className="flex -space-x-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <Star key={i} className="w-4 h-4 text-yellow-400 fill-yellow-400" />
              ))}
            </div>
            <span className="text-sm font-medium">10,000+ Happy Customers</span>
          </div>
          <div className="h-4 w-px bg-gray-300 hidden md:block" />
          <div className="flex items-center gap-2 text-gray-500">
            <Trophy className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium">5+ Industry Awards</span>
          </div>
          <div className="h-4 w-px bg-gray-300 hidden md:block" />
          <div className="flex items-center gap-2 text-gray-500">
            <Award className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium">Government Recognized</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AchievementsSection;

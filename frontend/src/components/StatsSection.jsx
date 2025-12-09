import React, { useState, useEffect, useRef } from 'react';
import { stats } from '../mockData';

const StatsSection = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [counters, setCounters] = useState(stats.map(() => 0));
  const sectionRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => {
      if (sectionRef.current) {
        observer.unobserve(sectionRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (isVisible) {
      stats.forEach((stat, index) => {
        const target = parseInt(stat.value);
        const duration = 2000; // 2 seconds
        const steps = 60;
        const increment = target / steps;
        let current = 0;

        const timer = setInterval(() => {
          current += increment;
          if (current >= target) {
            current = target;
            clearInterval(timer);
          }
          setCounters((prev) => {
            const newCounters = [...prev];
            newCounters[index] = Math.floor(current);
            return newCounters;
          });
        }, duration / steps);
      });
    }
  }, [isVisible]);

  return (
    <section ref={sectionRef} className="py-16 bg-gray-900 text-white">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={stat.id} className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-green-400 mb-2">
                {counters[index].toLocaleString()}{stat.suffix}
              </div>
              <div className="text-gray-300 text-sm md:text-base">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
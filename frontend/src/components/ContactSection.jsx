import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Phone, Mail, MapPin } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const ContactSection = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    role: '',
    fleetSize: '',
    message: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSelectChange = (name, value) => {
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    console.log('B2B Lead captured:', formData);
    
    toast({
      title: "Request Received!",
      description: "Our team will contact you within 24 hours.",
    });

    setFormData({
      name: '',
      email: '',
      phone: '',
      company: '',
      role: '',
      fleetSize: '',
      message: ''
    });
  };

  return (
    <section id="contact" className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Partner with Battwheels Garages
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Fleet operators, OEMs, and mobility platforms—let's build India's EV infrastructure together
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
          {/* Contact Info */}
          <div className="space-y-8">
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Get in Touch
              </h3>
              <p className="text-gray-600 mb-8">
                Whether you're running a fleet of 10 or 10,000 EVs, we have the infrastructure and expertise to support your operations.
              </p>
            </div>

            {/* Contact Details */}
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="bg-green-100 p-3 rounded-lg flex-shrink-0">
                  <MapPin className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">Head Office</h4>
                  <p className="text-gray-600">Dwarka Sector 23, Delhi, India</p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="bg-green-100 p-3 rounded-lg flex-shrink-0">
                  <Phone className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">Phone</h4>
                  <p className="text-gray-600">+91 9876543210</p>
                  <p className="text-sm text-green-600 mt-1">24x7 Operations</p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="bg-green-100 p-3 rounded-lg flex-shrink-0">
                  <Mail className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">Email</h4>
                  <p className="text-gray-600">partnerships@battwheelsgarages.in</p>
                  <p className="text-gray-600">support@battwheelsgarages.in</p>
                </div>
              </div>
            </div>

            {/* Stats Box */}
            <div className="bg-gray-900 text-white p-6 rounded-lg">
              <p className="text-green-400 font-semibold mb-2">Response Guarantee</p>
              <p className="text-sm text-gray-300">
                All partnership inquiries are reviewed within 24 hours. For urgent fleet breakdowns, call our 24x7 operations line.
              </p>
            </div>
          </div>

          {/* Contact Form - B2B Focused */}
          <div className="bg-white p-8 rounded-lg border border-gray-200 shadow-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Request Partnership / Demo</h3>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="mt-2"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <Label htmlFor="email">Business Email *</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="mt-2"
                  placeholder="john@company.com"
                />
              </div>

              <div>
                <Label htmlFor="phone">Phone Number *</Label>
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                  className="mt-2"
                  placeholder="+91 9876543210"
                />
              </div>

              <div>
                <Label htmlFor="company">Company / Fleet Name *</Label>
                <Input
                  id="company"
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  required
                  className="mt-2"
                  placeholder="ABC Logistics Pvt Ltd"
                />
              </div>

              <div>
                <Label htmlFor="role">Your Role</Label>
                <Select onValueChange={(value) => handleSelectChange('role', value)}>
                  <SelectTrigger className="mt-2">
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fleet-manager">Fleet Manager</SelectItem>
                    <SelectItem value="operations-head">Operations Head</SelectItem>
                    <SelectItem value="cxo">CXO / Founder</SelectItem>
                    <SelectItem value="procurement">Procurement Manager</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="fleetSize">Fleet Size</Label>
                <Select onValueChange={(value) => handleSelectChange('fleetSize', value)}>
                  <SelectTrigger className="mt-2">
                    <SelectValue placeholder="Select fleet size" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1-10">1-10 vehicles</SelectItem>
                    <SelectItem value="10-50">10-50 vehicles</SelectItem>
                    <SelectItem value="50-200">50-200 vehicles</SelectItem>
                    <SelectItem value="200+">200+ vehicles</SelectItem>
                    <SelectItem value="individual">Individual Owner</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="message">Message / Requirements</Label>
                <Textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  className="mt-2"
                  rows={4}
                  placeholder="Tell us about your fleet operations and service requirements..."
                />
              </div>

              <Button 
                type="submit" 
                className="w-full bg-green-600 hover:bg-green-700 text-white"
                size="lg"
              >
                Submit Partnership Request
              </Button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ContactSection;
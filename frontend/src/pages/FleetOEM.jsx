import React, { useState } from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { useToast } from '../hooks/use-toast';
import { Building, Users, Truck } from 'lucide-react';

const FleetOEM = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    companyName: '',
    contactPerson: '',
    role: '',
    email: '',
    phone: '',
    city: '',
    vehicleCount2W: '',
    vehicleCount3W: '',
    vehicleCount4W: '',
    vehicleCountCommercial: '',
    requirements: [],
    details: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSelectChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
  };

  const handleCheckboxChange = (requirement) => {
    const current = formData.requirements;
    if (current.includes(requirement)) {
      setFormData({ ...formData, requirements: current.filter(r => r !== requirement) });
    } else {
      setFormData({ ...formData, requirements: [...current, requirement] });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/fleet-enquiries/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: formData.companyName,
          contact_person: formData.contactPerson,
          role: formData.role,
          email: formData.email,
          phone: formData.phone,
          city: formData.city,
          vehicle_count_2w: parseInt(formData.vehicleCount2W) || 0,
          vehicle_count_3w: parseInt(formData.vehicleCount3W) || 0,
          vehicle_count_4w: parseInt(formData.vehicleCount4W) || 0,
          vehicle_count_commercial: parseInt(formData.vehicleCountCommercial) || 0,
          requirements: formData.requirements,
          details: formData.details
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Fleet enquiry created:', data);
        toast({
          title: "Enquiry Submitted!",
          description: "Our team will contact you within 24 hours to discuss your requirements.",
        });
        setFormData({
          companyName: '',
          contactPerson: '',
          role: '',
          email: '',
          phone: '',
          city: '',
          vehicleCount2W: '',
          vehicleCount3W: '',
          vehicleCount4W: '',
          vehicleCountCommercial: '',
          requirements: [],
          details: ''
        });
      } else {
        throw new Error('Failed to submit enquiry');
      }
    } catch (error) {
      console.error('Error submitting enquiry:', error);
      toast({
        title: "Error",
        description: "Failed to submit enquiry. Please try again.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero */}
        <section className="py-20 bg-gradient-to-br from-green-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Fleet & OEM Partnership
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Custom solutions for fleet operators, OEMs, and large-scale EV operations with dedicated support and SLAs
              </p>
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-12 bg-white">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              <div className="bg-green-50 p-6 rounded-xl text-center">
                <div className="bg-green-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Building className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Custom SLAs</h3>
                <p className="text-sm text-gray-600">Tailored service agreements with guaranteed response times</p>
              </div>
              <div className="bg-blue-50 p-6 rounded-xl text-center">
                <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Dedicated Manager</h3>
                <p className="text-sm text-gray-600">Single point of contact for all your fleet needs</p>
              </div>
              <div className="bg-purple-50 p-6 rounded-xl text-center">
                <div className="bg-purple-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Truck className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Onsite Teams</h3>
                <p className="text-sm text-gray-600">Option for dedicated onsite technicians at your facility</p>
              </div>
            </div>
          </div>
        </section>

        {/* Form */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto bg-gray-50 p-8 rounded-xl">
              <h2 className="text-3xl font-bold text-gray-900 mb-8">Submit Your Enquiry</h2>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <Label htmlFor="companyName">Company / Fleet Name *</Label>
                  <Input
                    id="companyName"
                    name="companyName"
                    value={formData.companyName}
                    onChange={handleChange}
                    required
                    className="mt-2"
                    placeholder="ABC Logistics Pvt Ltd"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="contactPerson">Contact Person *</Label>
                    <Input
                      id="contactPerson"
                      name="contactPerson"
                      value={formData.contactPerson}
                      onChange={handleChange}
                      required
                      className="mt-2"
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <Label htmlFor="role">Your Role *</Label>
                    <Select onValueChange={(value) => handleSelectChange('role', value)} required>
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
                </div>

                <div className="grid grid-cols-2 gap-4">
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
                </div>

                <div>
                  <Label htmlFor="city">City / Operating Regions *</Label>
                  <Input
                    id="city"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    required
                    className="mt-2"
                    placeholder="Delhi NCR, Mumbai, etc."
                  />
                </div>

                <div>
                  <Label className="mb-3 block">Vehicle Count by Segment</Label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="vehicleCount2W" className="text-sm">2-Wheelers</Label>
                      <Input
                        id="vehicleCount2W"
                        name="vehicleCount2W"
                        type="number"
                        value={formData.vehicleCount2W}
                        onChange={handleChange}
                        className="mt-1"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <Label htmlFor="vehicleCount3W" className="text-sm">3-Wheelers</Label>
                      <Input
                        id="vehicleCount3W"
                        name="vehicleCount3W"
                        type="number"
                        value={formData.vehicleCount3W}
                        onChange={handleChange}
                        className="mt-1"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <Label htmlFor="vehicleCount4W" className="text-sm">4-Wheelers</Label>
                      <Input
                        id="vehicleCount4W"
                        name="vehicleCount4W"
                        type="number"
                        value={formData.vehicleCount4W}
                        onChange={handleChange}
                        className="mt-1"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <Label htmlFor="vehicleCountCommercial" className="text-sm">Commercial EVs</Label>
                      <Input
                        id="vehicleCountCommercial"
                        name="vehicleCountCommercial"
                        type="number"
                        value={formData.vehicleCountCommercial}
                        onChange={handleChange}
                        className="mt-1"
                        placeholder="0"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <Label className="mb-3 block">Nature of Requirement (Select all that apply)</Label>
                  <div className="space-y-3">
                    {['Periodic Maintenance', 'Breakdown Support', 'SLA Agreement', 'Dedicated Onsite Team', 'Battwheels OS™ Integration'].map((req) => (
                      <div key={req} className="flex items-center space-x-2">
                        <Checkbox 
                          id={req}
                          checked={formData.requirements.includes(req)}
                          onCheckedChange={() => handleCheckboxChange(req)}
                        />
                        <Label htmlFor={req} className="font-normal cursor-pointer">{req}</Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label htmlFor="details">Additional Details</Label>
                  <Textarea
                    id="details"
                    name="details"
                    value={formData.details}
                    onChange={handleChange}
                    className="mt-2"
                    rows={5}
                    placeholder="Tell us more about your requirements..."
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full bg-green-600 hover:bg-green-700"
                  size="lg"
                >
                  Submit Enquiry
                </Button>
              </form>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default FleetOEM;
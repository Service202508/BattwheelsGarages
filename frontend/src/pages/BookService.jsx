import React, { useState } from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useToast } from '../hooks/use-toast';
import { CheckCircle } from 'lucide-react';

const BookService = () => {
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    vehicleCategory: '',
    customerType: '',
    brand: '',
    model: '',
    serviceNeeded: [],
    preferredDate: '',
    timeSlot: '',
    address: '',
    city: '',
    name: '',
    phone: '',
    email: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSelectChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/bookings/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vehicle_category: formData.vehicleCategory,
          customer_type: formData.customerType,
          brand: formData.brand,
          model: formData.model,
          service_needed: formData.serviceNeeded,
          preferred_date: formData.preferredDate,
          time_slot: formData.timeSlot,
          address: formData.address,
          city: formData.city,
          name: formData.name,
          phone: formData.phone,
          email: formData.email
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Booking created:', data);
        toast({
          title: "Booking Confirmed!",
          description: "We'll contact you within 2 hours to confirm your service.",
        });
        // Reset form
        setFormData({
          vehicleCategory: '',
          customerType: '',
          brand: '',
          model: '',
          serviceNeeded: [],
          preferredDate: '',
          timeSlot: '',
          address: '',
          city: '',
          name: '',
          phone: '',
          email: ''
        });
        setStep(1);
      } else {
        throw new Error('Failed to submit booking');
      }
    } catch (error) {
      console.error('Error submitting booking:', error);
      toast({
        title: "Error",
        description: "Failed to submit booking. Please try again.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">Book EV Service</h1>
              <p className="text-gray-600">Fill in the details and we'll get your EV serviced</p>
            </div>

            {/* Progress Steps */}
            <div className="flex items-center justify-center mb-12">
              {[1, 2, 3].map((s) => (
                <React.Fragment key={s}>
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                    step >= s ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-600'
                  } font-semibold`}>
                    {step > s ? <CheckCircle className="w-6 h-6" /> : s}
                  </div>
                  {s < 3 && <div className={`h-1 w-24 ${
                    step > s ? 'bg-green-600' : 'bg-gray-200'
                  }`} />}
                </React.Fragment>
              ))}
            </div>

            {/* Form */}
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <form onSubmit={handleSubmit} className="space-y-6">
                {step === 1 && (
                  <>
                    <div>
                      <Label htmlFor="vehicleCategory">Vehicle Category *</Label>
                      <Select onValueChange={(value) => handleSelectChange('vehicleCategory', value)} required>
                        <SelectTrigger className="mt-2">
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="2w">2-Wheeler (Scooter/Bike)</SelectItem>
                          <SelectItem value="3w">3-Wheeler (E-Rickshaw/Cargo)</SelectItem>
                          <SelectItem value="4w">4-Wheeler (Car)</SelectItem>
                          <SelectItem value="commercial">Commercial EV</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="customerType">Customer Type *</Label>
                      <Select onValueChange={(value) => handleSelectChange('customerType', value)} required>
                        <SelectTrigger className="mt-2">
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="individual">Individual Owner</SelectItem>
                          <SelectItem value="fleet">Fleet Operator</SelectItem>
                          <SelectItem value="oem">OEM</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="brand">Brand</Label>
                        <Input
                          id="brand"
                          name="brand"
                          value={formData.brand}
                          onChange={handleChange}
                          className="mt-2"
                          placeholder="e.g., Ather"
                        />
                      </div>
                      <div>
                        <Label htmlFor="model">Model</Label>
                        <Input
                          id="model"
                          name="model"
                          value={formData.model}
                          onChange={handleChange}
                          className="mt-2"
                          placeholder="e.g., 450X"
                        />
                      </div>
                    </div>

                    <Button 
                      type="button" 
                      className="w-full bg-green-600 hover:bg-green-700"
                      onClick={() => setStep(2)}
                    >
                      Next
                    </Button>
                  </>
                )}

                {step === 2 && (
                  <>
                    <div>
                      <Label>Service Needed</Label>
                      <Textarea
                        name="serviceNeeded"
                        value={formData.serviceNeeded}
                        onChange={handleChange}
                        className="mt-2"
                        rows={4}
                        placeholder="Describe the service you need (e.g., periodic service, motor repair, battery diagnostics)"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="preferredDate">Preferred Date *</Label>
                        <Input
                          id="preferredDate"
                          name="preferredDate"
                          type="date"
                          value={formData.preferredDate}
                          onChange={handleChange}
                          className="mt-2"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="timeSlot">Time Slot</Label>
                        <Select onValueChange={(value) => handleSelectChange('timeSlot', value)}>
                          <SelectTrigger className="mt-2">
                            <SelectValue placeholder="Select time" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="morning">Morning (9 AM - 12 PM)</SelectItem>
                            <SelectItem value="afternoon">Afternoon (12 PM - 4 PM)</SelectItem>
                            <SelectItem value="evening">Evening (4 PM - 8 PM)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="address">Service Address *</Label>
                      <Textarea
                        id="address"
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        className="mt-2"
                        rows={3}
                        placeholder="Full address where service is needed"
                        required
                      />
                    </div>

                    <div>
                      <Label htmlFor="city">City *</Label>
                      <Input
                        id="city"
                        name="city"
                        value={formData.city}
                        onChange={handleChange}
                        className="mt-2"
                        placeholder="e.g., Delhi"
                        required
                      />
                    </div>

                    <div className="flex gap-4">
                      <Button 
                        type="button" 
                        variant="outline"
                        className="flex-1"
                        onClick={() => setStep(1)}
                      >
                        Back
                      </Button>
                      <Button 
                        type="button" 
                        className="flex-1 bg-green-600 hover:bg-green-700"
                        onClick={() => setStep(3)}
                      >
                        Next
                      </Button>
                    </div>
                  </>
                )}

                {step === 3 && (
                  <>
                    <div>
                      <Label htmlFor="name">Full Name *</Label>
                      <Input
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="mt-2"
                        placeholder="John Doe"
                        required
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
                        className="mt-2"
                        placeholder="+91 9876543210"
                        required
                      />
                    </div>

                    <div>
                      <Label htmlFor="email">Email *</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="mt-2"
                        placeholder="john@example.com"
                        required
                      />
                    </div>

                    <div className="flex gap-4">
                      <Button 
                        type="button" 
                        variant="outline"
                        className="flex-1"
                        onClick={() => setStep(2)}
                      >
                        Back
                      </Button>
                      <Button 
                        type="submit" 
                        className="flex-1 bg-green-600 hover:bg-green-700"
                      >
                        Confirm Booking
                      </Button>
                    </div>
                  </>
                )}
              </form>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default BookService;
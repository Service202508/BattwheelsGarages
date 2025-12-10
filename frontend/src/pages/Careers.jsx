import React, { useState } from 'react';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { useToast } from '../hooks/use-toast';
import { Briefcase, MapPin, Clock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

const Careers = () => {
  const { toast } = useToast();
  const [selectedJob, setSelectedJob] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    experience: '',
    cv: null
  });

  // Sample job listings
  const jobs = [
    {
      id: 1,
      title: 'Senior EV Technician',
      location: 'Delhi NCR',
      type: 'Full-time',
      description: 'Experienced EV technician for motor, controller, and battery diagnostics and repair.',
      requirements: ['3+ years EV experience', 'Knowledge of BMS and motor controllers', 'Valid driving license']
    },
    {
      id: 2,
      title: 'Service Manager',
      location: 'Delhi NCR',
      type: 'Full-time',
      description: 'Manage service operations, technician teams, and customer relationships.',
      requirements: ['5+ years in automotive service management', 'Strong leadership skills', 'EV knowledge preferred']
    },
    {
      id: 3,
      title: 'Field Operations Executive',
      location: 'Multiple Cities',
      type: 'Full-time',
      description: 'Coordinate onsite service operations and manage field technician schedules.',
      requirements: ['2+ years operations experience', 'Strong organizational skills', 'Familiarity with logistics']
    }
  ];

  const handleChange = (e) => {
    if (e.target.type === 'file') {
      setFormData({ ...formData, cv: e.target.files[0] });
    } else {
      setFormData({ ...formData, [e.target.name]: e.target.value });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Application submitted:', { ...formData, jobId: selectedJob });
    toast({
      title: "Application Submitted!",
      description: "We'll review your application and get back to you soon.",
    });
    setFormData({
      name: '',
      email: '',
      phone: '',
      experience: '',
      cv: null
    });
    setSelectedJob(null);
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
                Join Our Team
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Be part of India's EV revolution. We're looking for skilled technicians, service managers, and operations professionals.
              </p>
            </div>
          </div>
        </section>

        {/* Job Listings */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4">
            <div className="max-w-5xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 mb-8">Open Positions</h2>
              
              <div className="grid gap-6 mb-12">
                {jobs.map((job) => (
                  <Card key={job.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-2xl mb-2">{job.title}</CardTitle>
                          <CardDescription className="flex flex-wrap gap-4 text-sm">
                            <span className="flex items-center">
                              <MapPin className="w-4 h-4 mr-1" />
                              {job.location}
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              {job.type}
                            </span>
                          </CardDescription>
                        </div>
                        <Button 
                          onClick={() => setSelectedJob(job.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Apply Now
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700 mb-4">{job.description}</p>
                      <div>
                        <p className="font-semibold text-gray-900 mb-2">Requirements:</p>
                        <ul className="list-disc pl-6 text-gray-700 space-y-1">
                          {job.requirements.map((req, index) => (
                            <li key={index}>{req}</li>
                          ))}
                        </ul>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Application Form */}
              {selectedJob && (
                <div className="bg-gray-50 p-8 rounded-xl">
                  <h3 className="text-2xl font-bold text-gray-900 mb-6">Application Form</h3>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                      <Label htmlFor="name">Full Name *</Label>
                      <Input
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="mt-2"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="email">Email *</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleChange}
                          required
                          className="mt-2"
                        />
                      </div>
                      <div>
                        <Label htmlFor="phone">Phone *</Label>
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          value={formData.phone}
                          onChange={handleChange}
                          required
                          className="mt-2"
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="experience">Experience (in years)</Label>
                      <Input
                        id="experience"
                        name="experience"
                        value={formData.experience}
                        onChange={handleChange}
                        className="mt-2"
                      />
                    </div>

                    <div>
                      <Label htmlFor="cv">Upload CV *</Label>
                      <Input
                        id="cv"
                        name="cv"
                        type="file"
                        accept=".pdf,.doc,.docx"
                        onChange={handleChange}
                        required
                        className="mt-2"
                      />
                    </div>

                    <div className="flex gap-4">
                      <Button 
                        type="button" 
                        variant="outline"
                        onClick={() => setSelectedJob(null)}
                      >
                        Cancel
                      </Button>
                      <Button 
                        type="submit" 
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Submit Application
                      </Button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Careers;
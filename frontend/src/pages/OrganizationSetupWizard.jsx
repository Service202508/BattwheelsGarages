import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { API, getAuthHeaders } from "@/App";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Building2, 
  Users, 
  Settings, 
  Check, 
  ChevronRight, 
  ChevronLeft,
  MapPin,
  Phone,
  Globe,
  Briefcase,
  Clock,
  IndianRupee,
  Sparkles,
  UserPlus,
  Mail
} from "lucide-react";
import { toast } from "sonner";

const STEPS = [
  { id: 1, title: "Organization Profile", icon: Building2, description: "Basic details about your business" },
  { id: 2, title: "Business Settings", icon: Settings, description: "Configure your preferences" },
  { id: 3, title: "Invite Team", icon: Users, description: "Add your first team members" },
  { id: 4, title: "Get Started", icon: Sparkles, description: "You're all set!" }
];

export default function OrganizationSetupWizard({ user, onComplete }) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [orgData, setOrgData] = useState({
    // Step 1: Profile
    name: "",
    industry_type: "ev_garage",
    address: "",
    city: "",
    state: "",
    pincode: "",
    phone: "",
    website: "",
    gst_number: "",
    // Step 2: Settings
    timezone: "Asia/Kolkata",
    currency: "INR",
    fiscal_year_start: "april",
    working_hours_start: "09:00",
    working_hours_end: "18:00",
    working_days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    // Step 3: Team
    team_invites: []
  });
  const [newInvite, setNewInvite] = useState({ name: "", email: "", role: "technician" });

  useEffect(() => {
    // Load existing org data if available
    fetchOrgData();
  }, []);

  const fetchOrgData = async () => {
    try {
      const response = await fetch(`${API}/organizations/me`, { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        if (data.organization) {
          setOrgData(prev => ({
            ...prev,
            name: data.organization.name || "",
            industry_type: data.organization.industry_type || "ev_garage",
            address: data.organization.settings?.address || "",
            city: data.organization.settings?.city || "",
            state: data.organization.settings?.state || "",
            pincode: data.organization.settings?.pincode || "",
            phone: data.organization.settings?.phone || "",
            website: data.organization.settings?.website || "",
            gst_number: data.organization.settings?.gst_number || "",
            timezone: data.organization.settings?.timezone || "Asia/Kolkata",
            currency: data.organization.settings?.currency || "INR"
          }));
        }
      }
    } catch (error) {
      console.error("Failed to fetch org data:", error);
    }
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/organizations/me/settings`, {
        method: "PATCH",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          name: orgData.name,
          industry_type: orgData.industry_type,
          settings: {
            address: orgData.address,
            city: orgData.city,
            state: orgData.state,
            pincode: orgData.pincode,
            phone: orgData.phone,
            website: orgData.website,
            gst_number: orgData.gst_number
          }
        })
      });

      if (response.ok) {
        toast.success("Profile saved!");
        setCurrentStep(2);
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save profile");
      }
    } catch (error) {
      toast.error("Failed to save profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/organizations/me/settings`, {
        method: "PATCH",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          settings: {
            timezone: orgData.timezone,
            currency: orgData.currency,
            fiscal_year_start: orgData.fiscal_year_start,
            working_hours: {
              start: orgData.working_hours_start,
              end: orgData.working_hours_end,
              days: orgData.working_days
            }
          }
        })
      });

      if (response.ok) {
        toast.success("Settings saved!");
        setCurrentStep(3);
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save settings");
      }
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setLoading(false);
    }
  };

  const handleAddInvite = () => {
    if (!newInvite.name || !newInvite.email) {
      toast.error("Please enter name and email");
      return;
    }
    setOrgData(prev => ({
      ...prev,
      team_invites: [...prev.team_invites, { ...newInvite, id: Date.now() }]
    }));
    setNewInvite({ name: "", email: "", role: "technician" });
  };

  const handleRemoveInvite = (id) => {
    setOrgData(prev => ({
      ...prev,
      team_invites: prev.team_invites.filter(i => i.id !== id)
    }));
  };

  const handleSendInvites = async () => {
    setLoading(true);
    let successCount = 0;
    
    for (const invite of orgData.team_invites) {
      try {
        const response = await fetch(`${API}/organizations/me/invite`, {
          method: "POST",
          headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            name: invite.name,
            email: invite.email,
            role: invite.role
          })
        });
        
        if (response.ok) {
          successCount++;
        }
      } catch (error) {
        console.error(`Failed to invite ${invite.email}:`, error);
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} invitation(s) sent!`);
    }
    setCurrentStep(4);
    setLoading(false);
  };

  const handleComplete = async () => {
    // Mark setup as complete
    try {
      await fetch(`${API}/organizations/me/complete-setup`, {
        method: "POST",
        headers: getAuthHeaders()
      });
    } catch (error) {
      // Non-blocking
    }
    
    if (onComplete) {
      onComplete();
    } else {
      navigate("/dashboard");
    }
  };

  const progress = (currentStep / STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4" data-testid="setup-wizard">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#F4F6F0] mb-2">Welcome to Battwheels OS</h1>
          <p className="text-gray-600">Let's set up your organization in just a few steps</p>
        </div>

        {/* Progress */}
        <div className="mb-8">
          <Progress value={progress} className="h-2 mb-4" />
          <div className="flex justify-between">
            {STEPS.map((step) => {
              const StepIcon = step.icon;
              const isActive = currentStep === step.id;
              const isComplete = currentStep > step.id;
              
              return (
                <div 
                  key={step.id}
                  className={`flex flex-col items-center ${
                    isActive ? "text-[#C8FF00] text-600" : isComplete ? "text-[#C8FF00] text-500" : "text-gray-400"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${
                    isActive ? "bg-[rgba(200,255,0,0.10)] ring-2 ring-emerald-500" :
                    isComplete ? "bg-[#C8FF00] text-[#080C0F]" : "bg-[rgba(255,255,255,0.05)]"
                  }`}>
                    {isComplete ? <Check className="h-5 w-5" /> : <StepIcon className="h-5 w-5" />}
                  </div>
                  <span className="text-xs font-medium hidden sm:block">{step.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <Card className="border border-[rgba(255,255,255,0.07)]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {(() => {
                const StepIcon = STEPS[currentStep - 1].icon;
                return <StepIcon className="h-5 w-5 text-[#C8FF00] text-500" />;
              })()}
              {STEPS[currentStep - 1].title}
            </CardTitle>
            <CardDescription>{STEPS[currentStep - 1].description}</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Step 1: Organization Profile */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Organization Name *</Label>
                    <Input
                      id="name"
                      placeholder="My EV Workshop"
                      value={orgData.name}
                      onChange={(e) => setOrgData({ ...orgData, name: e.target.value })}
                      data-testid="org-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="industry">Industry Type</Label>
                    <Select
                      value={orgData.industry_type}
                      onValueChange={(v) => setOrgData({ ...orgData, industry_type: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ev_garage">EV Service Center</SelectItem>
                        <SelectItem value="ev_dealership">EV Dealership</SelectItem>
                        <SelectItem value="ev_fleet">Fleet Operator</SelectItem>
                        <SelectItem value="ev_manufacturer">EV Manufacturer</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address">Business Address</Label>
                  <Textarea
                    id="address"
                    placeholder="Street address"
                    value={orgData.address}
                    onChange={(e) => setOrgData({ ...orgData, address: e.target.value })}
                    rows={2}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      placeholder="Mumbai"
                      value={orgData.city}
                      onChange={(e) => setOrgData({ ...orgData, city: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state">State</Label>
                    <Input
                      id="state"
                      placeholder="Maharashtra"
                      value={orgData.state}
                      onChange={(e) => setOrgData({ ...orgData, state: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pincode">PIN Code</Label>
                    <Input
                      id="pincode"
                      placeholder="400001"
                      value={orgData.pincode}
                      onChange={(e) => setOrgData({ ...orgData, pincode: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      placeholder="+91 98765 43210"
                      value={orgData.phone}
                      onChange={(e) => setOrgData({ ...orgData, phone: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gst">GST Number</Label>
                    <Input
                      id="gst"
                      placeholder="22AAAAA0000A1Z5"
                      value={orgData.gst_number}
                      onChange={(e) => setOrgData({ ...orgData, gst_number: e.target.value })}
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveProfile} disabled={loading || !orgData.name}>
                    {loading ? "Saving..." : "Continue"}
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {/* Step 2: Business Settings */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Timezone</Label>
                    <Select
                      value={orgData.timezone}
                      onValueChange={(v) => setOrgData({ ...orgData, timezone: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Asia/Kolkata">India (IST)</SelectItem>
                        <SelectItem value="Asia/Dubai">Dubai (GST)</SelectItem>
                        <SelectItem value="Asia/Singapore">Singapore (SGT)</SelectItem>
                        <SelectItem value="Europe/London">London (GMT)</SelectItem>
                        <SelectItem value="America/New_York">New York (EST)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Currency</Label>
                    <Select
                      value={orgData.currency}
                      onValueChange={(v) => setOrgData({ ...orgData, currency: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="INR">Indian Rupee (₹)</SelectItem>
                        <SelectItem value="USD">US Dollar ($)</SelectItem>
                        <SelectItem value="EUR">Euro (€)</SelectItem>
                        <SelectItem value="AED">UAE Dirham (د.إ)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Fiscal Year Starts</Label>
                  <Select
                    value={orgData.fiscal_year_start}
                    onValueChange={(v) => setOrgData({ ...orgData, fiscal_year_start: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="january">January</SelectItem>
                      <SelectItem value="april">April (India)</SelectItem>
                      <SelectItem value="july">July</SelectItem>
                      <SelectItem value="october">October</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Working Hours Start</Label>
                    <Input
                      type="time"
                      value={orgData.working_hours_start}
                      onChange={(e) => setOrgData({ ...orgData, working_hours_start: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Working Hours End</Label>
                    <Input
                      type="time"
                      value={orgData.working_hours_end}
                      onChange={(e) => setOrgData({ ...orgData, working_hours_end: e.target.value })}
                    />
                  </div>
                </div>

                <div className="flex justify-between pt-4">
                  <Button variant="outline" onClick={() => setCurrentStep(1)}>
                    <ChevronLeft className="h-4 w-4 mr-2" />
                    Back
                  </Button>
                  <Button onClick={handleSaveSettings} disabled={loading}>
                    {loading ? "Saving..." : "Continue"}
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {/* Step 3: Invite Team */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <p className="text-sm text-gray-600">
                  Invite your team members to get started. You can always add more later from Settings → Team Management.
                </p>

                <div className="border rounded-lg p-4 bg-[#111820]">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <Input
                      placeholder="Name"
                      value={newInvite.name}
                      onChange={(e) => setNewInvite({ ...newInvite, name: e.target.value })}
                    />
                    <Input
                      type="email"
                      placeholder="Email"
                      value={newInvite.email}
                      onChange={(e) => setNewInvite({ ...newInvite, email: e.target.value })}
                    />
                    <Select
                      value={newInvite.role}
                      onValueChange={(v) => setNewInvite({ ...newInvite, role: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="manager">Manager</SelectItem>
                        <SelectItem value="technician">Technician</SelectItem>
                        <SelectItem value="accountant">Accountant</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button onClick={handleAddInvite} variant="outline">
                      <UserPlus className="h-4 w-4 mr-2" />
                      Add
                    </Button>
                  </div>
                </div>

                {orgData.team_invites.length > 0 && (
                  <div className="space-y-2">
                    {orgData.team_invites.map((invite) => (
                      <div key={invite.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[rgba(200,255,0,0.10)] flex items-center justify-center">
                            <Mail className="h-4 w-4 text-[#C8FF00] text-600" />
                          </div>
                          <div>
                            <p className="font-medium">{invite.name}</p>
                            <p className="text-sm text-gray-500">{invite.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{invite.role}</Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveInvite(invite.id)}
                            className="text-red-500 hover:text-red-600"
                          >
                            Remove
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex justify-between pt-4">
                  <Button variant="outline" onClick={() => setCurrentStep(2)}>
                    <ChevronLeft className="h-4 w-4 mr-2" />
                    Back
                  </Button>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setCurrentStep(4)}>
                      Skip for now
                    </Button>
                    <Button 
                      onClick={handleSendInvites} 
                      disabled={loading || orgData.team_invites.length === 0}
                    >
                      {loading ? "Sending..." : `Send ${orgData.team_invites.length} Invite(s)`}
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Complete */}
            {currentStep === 4 && (
              <div className="text-center py-8">
                <div className="w-20 h-20 bg-[rgba(200,255,0,0.10)] rounded-full flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="h-10 w-10 text-[#C8FF00] text-500" />
                </div>
                <h2 className="text-2xl font-bold text-[#F4F6F0] mb-2">You're All Set! 🎉</h2>
                <p className="text-gray-600 mb-8 max-w-md mx-auto">
                  Your organization is ready to go. Start managing your EV workshop with AI-powered diagnostics, 
                  invoicing, inventory, and more.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 text-left">
                  <div className="p-4 border rounded-lg">
                    <Briefcase className="h-6 w-6 text-[#C8FF00] text-500 mb-2" />
                    <h3 className="font-medium">Create Tickets</h3>
                    <p className="text-sm text-gray-500">Log service requests and track repairs</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <IndianRupee className="h-6 w-6 text-[#C8FF00] text-500 mb-2" />
                    <h3 className="font-medium">Send Invoices</h3>
                    <p className="text-sm text-gray-500">Generate GST-compliant invoices</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <Sparkles className="h-6 w-6 text-[#C8FF00] text-500 mb-2" />
                    <h3 className="font-medium">AI Diagnostics</h3>
                    <p className="text-sm text-gray-500">Get AI-powered repair guidance</p>
                  </div>
                </div>

                <Button size="lg" onClick={handleComplete} className="px-8">
                  Go to Dashboard
                  <ChevronRight className="h-5 w-5 ml-2" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

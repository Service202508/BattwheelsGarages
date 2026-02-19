import { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel } from "@/components/ui/select";
import { toast } from "sonner";
import { 
  Bot, Send, Loader2, Zap, Battery, Plug, Wrench, AlertCircle, 
  Bike, Car, Truck, Cog, Cpu, ArrowUpDown, Disc, Thermometer, Wind,
  Shield, DollarSign, Clock, CheckCircle, AlertTriangle
} from "lucide-react";
import { API } from "@/App";

// Issue Categories - comprehensive list for EV diagnostics
const issueCategories = [
  { value: "battery", label: "Battery Issues", icon: Battery, description: "Battery performance, charging issues, BMS problems" },
  { value: "motor", label: "Motor Problems", icon: Wrench, description: "Motor noise, power loss, vibration" },
  { value: "charging", label: "Charging System", icon: Plug, description: "Charging port, cable, onboard charger" },
  { value: "electrical", label: "Electrical", icon: Zap, description: "Wiring, fuses, relays, short circuits" },
  { value: "mechanical", label: "Mechanical", icon: Cog, description: "Drivetrain, gears, belts, transmission" },
  { value: "software", label: "Software Issues", icon: Cpu, description: "ECU errors, firmware, display glitches" },
  { value: "suspension", label: "Suspension", icon: ArrowUpDown, description: "Shocks, springs, alignment issues" },
  { value: "braking", label: "Braking System", icon: Disc, description: "Brake pads, rotors, ABS, regenerative" },
  { value: "cooling", label: "Cooling System", icon: Thermometer, description: "Overheating, coolant, fans, thermal" },
  { value: "hvac", label: "AC/Heating", icon: Wind, description: "Climate control, AC, heater issues" },
  { value: "other", label: "Other", icon: AlertCircle, description: "Other issues not listed above" },
];

// Vehicle Categories
const vehicleCategories = [
  { value: "2_wheeler", label: "2 Wheeler", icon: Bike },
  { value: "3_wheeler", label: "3 Wheeler", icon: Truck },
  { value: "4_wheeler_commercial", label: "4 Wheeler Commercial", icon: Truck },
  { value: "car", label: "Car", icon: Car },
];

// Comprehensive EV Models by Category
const vehicleModelsByCategory = {
  "2_wheeler": [
    // Ola Electric
    { name: "Ola S1 Pro", brand: "Ola Electric" },
    { name: "Ola S1 Air", brand: "Ola Electric" },
    // Ather Energy
    { name: "Ather 450X", brand: "Ather Energy" },
    { name: "Ather 450S", brand: "Ather Energy" },
    // TVS Motor
    { name: "TVS iQube", brand: "TVS Motor" },
    // Bajaj Auto
    { name: "Bajaj Chetak Electric", brand: "Bajaj Auto" },
    // Hero
    { name: "Hero Vida V1", brand: "Hero MotoCorp" },
    { name: "Hero Optima", brand: "Hero Electric" },
    // Greaves Electric (Ampere)
    { name: "Ampere Magnus EX", brand: "Greaves Electric" },
    { name: "Ampere Nexus", brand: "Greaves Electric" },
    // Okinawa
    { name: "Okinawa Praise Pro", brand: "Okinawa" },
    { name: "Okinawa iPraise+", brand: "Okinawa" },
    // Revolt Motors
    { name: "Revolt RV400", brand: "Revolt Motors" },
    // Tork Motors
    { name: "Tork Kratos R", brand: "Tork Motors" },
    // Simple Energy
    { name: "Simple One", brand: "Simple Energy" },
    // PURE EV
    { name: "Pure EV EPluto 7G", brand: "PURE EV" },
    // Oben Electric
    { name: "Oben Rorr", brand: "Oben Electric" },
    // Ultraviolette
    { name: "Ultraviolette F77", brand: "Ultraviolette" },
    // Kinetic Green
    { name: "Kinetic Green Zing", brand: "Kinetic Green" },
    // Joy e-Bike
    { name: "Wardwizard Joy e-Bike Mihos", brand: "Joy e-Bike" },
  ],
  "3_wheeler": [
    // Mahindra
    { name: "Mahindra Treo", brand: "Mahindra" },
    { name: "Mahindra Treo Zor (cargo)", brand: "Mahindra" },
    { name: "Mahindra e-Alfa Mini", brand: "Mahindra" },
    // Bajaj
    { name: "Bajaj RE E-TEC", brand: "Bajaj Auto" },
    // Piaggio
    { name: "Piaggio Ape E-City", brand: "Piaggio" },
    { name: "Piaggio Ape E-Xtra (cargo)", brand: "Piaggio" },
    // Euler
    { name: "Euler HiLoad EV (cargo)", brand: "Euler Motors" },
    { name: "Euler Storm EV", brand: "Euler Motors" },
    // Omega Seiki
    { name: "Omega Seiki Rage+", brand: "Omega Seiki" },
    { name: "Omega Seiki Stream", brand: "Omega Seiki" },
    // Kinetic
    { name: "Kinetic Safar Jumbo (cargo)", brand: "Kinetic Green" },
    // Lohia
    { name: "Lohia Humsafar", brand: "Lohia Auto" },
    { name: "Lohia Narain ICE-converted EV", brand: "Lohia Auto" },
    // Atul
    { name: "Atul Elite Cargo", brand: "Atul Auto" },
    // YC Electric
    { name: "YC Electric Yatri", brand: "YC Electric" },
    // E-Rickshaws
    { name: "Mini Metro E-Rickshaw", brand: "Mini Metro" },
    { name: "Saarthi DLX E-Rickshaw", brand: "Saarthi" },
    { name: "Udaan E-Rickshaw", brand: "Udaan" },
    // TVS
    { name: "TVS King EV Max", brand: "TVS Motor" },
    // Montra
    { name: "Montra Super Auto EV", brand: "Montra Electric" },
  ],
  "4_wheeler_commercial": [
    // Tata
    { name: "Tata Ace EV", brand: "Tata Motors" },
    { name: "Tata Ace EV Zip", brand: "Tata Motors" },
    // Mahindra
    { name: "Mahindra Treo Zor Pickup", brand: "Mahindra" },
    { name: "Mahindra eSupro Cargo Van", brand: "Mahindra" },
    // Switch Mobility (Ashok Leyland)
    { name: "Ashok Leyland Dost Electric (Switch IeV)", brand: "Switch Mobility" },
    { name: "Switch Mobility IeV3", brand: "Switch Mobility" },
    { name: "Switch Mobility IeV4", brand: "Switch Mobility" },
    // Euler
    { name: "Euler HiLoad EV (4W)", brand: "Euler Motors" },
    // EKA (Pinnacle Mobility)
    { name: "EKA K1.5", brand: "Pinnacle Mobility" },
    // Altigreen
    { name: "Altigreen neEV Tez", brand: "Altigreen" },
    { name: "Altigreen neEV Low Deck", brand: "Altigreen" },
    // Montra
    { name: "Montra Eviator", brand: "Montra Electric" },
    { name: "Montra Electric Super Cargo", brand: "Montra Electric" },
    // Omega Seiki
    { name: "Omega Seiki M1KA", brand: "Omega Seiki" },
    { name: "Omega Seiki Rage+ Rapid", brand: "Omega Seiki" },
    // Others
    { name: "Gayam Motor Works eLCV", brand: "Gayam Motor Works" },
    { name: "PMV Eas-E Cargo", brand: "PMV Electric" },
    { name: "Force Electric Traveller", brand: "Force Motors" },
    { name: "Tata Winger EV", brand: "Tata Motors" },
    { name: "JBM ECOLIFE Electric LCV", brand: "JBM Auto" },
  ],
  "car": [
    // Tata Motors
    { name: "Tata Nexon EV", brand: "Tata Motors" },
    { name: "Tata Punch EV", brand: "Tata Motors" },
    { name: "Tata Tiago EV", brand: "Tata Motors" },
    { name: "Tata Tigor EV", brand: "Tata Motors" },
    // Mahindra
    { name: "Mahindra XUV400", brand: "Mahindra" },
    { name: "Mahindra BE 6", brand: "Mahindra" },
    { name: "Mahindra XEV 9e", brand: "Mahindra" },
    // MG Motor
    { name: "MG Comet EV", brand: "MG Motor" },
    { name: "MG Windsor EV", brand: "MG Motor" },
    { name: "MG ZS EV", brand: "MG Motor" },
    // Hyundai
    { name: "Hyundai Kona Electric", brand: "Hyundai" },
    // BYD
    { name: "BYD Atto 3", brand: "BYD" },
    { name: "BYD e6", brand: "BYD" },
    // Citroën
    { name: "Citroën ë-C3", brand: "Citroën" },
    // Premium/Luxury
    { name: "Volvo XC40 Recharge", brand: "Volvo" },
    { name: "Kia EV6", brand: "Kia" },
    { name: "BMW i4", brand: "BMW" },
    { name: "Mercedes-Benz EQB", brand: "Mercedes-Benz" },
    { name: "Audi Q8 e-tron", brand: "Audi" },
    // Maruti Suzuki
    { name: "Maruti Suzuki e-Vitara", brand: "Maruti Suzuki" },
  ],
};

export default function AIAssistant({ user }) {
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState({
    issue_description: "",
    vehicle_model: "",
    vehicle_category: "",
    category: "",
  });
  const [response, setResponse] = useState(null);

  // Get filtered vehicle models based on selected category
  const filteredModels = useMemo(() => {
    if (!query.vehicle_category) return [];
    return vehicleModelsByCategory[query.vehicle_category] || [];
  }, [query.vehicle_category]);

  // Reset vehicle model when category changes
  const handleCategoryChange = (category) => {
    setQuery({ ...query, vehicle_category: category, vehicle_model: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.issue_description) {
      toast.error("Please describe your issue");
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/ai/diagnose`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(query),
      });

      if (res.ok) {
        const data = await res.json();
        setResponse(data);
      } else {
        toast.error("Failed to get diagnosis");
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="ai-assistant-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-14 w-14 rounded-xl bg-primary/20 flex items-center justify-center animate-pulse-glow">
          <Bot className="h-8 w-8 text-primary" />
        </div>
        <div>
          <h1 className="text-4xl font-bold tracking-tight">AI Diagnostic Assistant</h1>
          <p className="text-muted-foreground mt-1">
            Get instant AI-powered diagnosis for your EV issues.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Form */}
        <Card className="border-white/10 bg-card/50">
          <CardHeader>
            <CardTitle>Describe Your Issue</CardTitle>
            <CardDescription>
              Provide details about the problem you're experiencing with your EV.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Issue Category Selection */}
              <div className="space-y-3">
                <Label>Issue Category</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  {issueCategories.map((cat) => {
                    const Icon = cat.icon;
                    return (
                      <button
                        key={cat.value}
                        type="button"
                        onClick={() => setQuery({ ...query, category: cat.value })}
                        className={`p-3 rounded-lg border transition-all text-left group ${
                          query.category === cat.value
                            ? "border-primary bg-primary/10"
                            : "border-white/10 hover:border-white/20 bg-background/50"
                        }`}
                        data-testid={`category-btn-${cat.value}`}
                        title={cat.description}
                      >
                        <Icon className={`h-4 w-4 mb-1 ${
                          query.category === cat.value ? "text-primary" : "text-muted-foreground group-hover:text-white"
                        }`} />
                        <p className="text-xs font-medium truncate">{cat.label}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Vehicle Category Selection */}
              <div className="space-y-3">
                <Label>Vehicle Category</Label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {vehicleCategories.map((cat) => {
                    const Icon = cat.icon;
                    return (
                      <button
                        key={cat.value}
                        type="button"
                        onClick={() => handleCategoryChange(cat.value)}
                        className={`p-3 rounded-lg border transition-all text-center ${
                          query.vehicle_category === cat.value
                            ? "border-primary bg-primary/10"
                            : "border-white/10 hover:border-white/20 bg-background/50"
                        }`}
                        data-testid={`vehicle-category-btn-${cat.value}`}
                      >
                        <Icon className={`h-5 w-5 mx-auto mb-1 ${
                          query.vehicle_category === cat.value ? "text-primary" : "text-muted-foreground"
                        }`} />
                        <p className="text-xs font-medium">{cat.label}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Vehicle Model */}
              <div className="space-y-2">
                <Label>Vehicle Model</Label>
                <Select
                  value={query.vehicle_model}
                  onValueChange={(value) => setQuery({ ...query, vehicle_model: value })}
                  disabled={!query.vehicle_category}
                >
                  <SelectTrigger className="bg-background/50" data-testid="vehicle-model-select">
                    <SelectValue placeholder={query.vehicle_category ? "Select your vehicle model" : "Select vehicle category first"} />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {filteredModels.length > 0 ? (
                      <>
                        {/* Group by brand */}
                        {Object.entries(
                          filteredModels.reduce((acc, model) => {
                            if (!acc[model.brand]) acc[model.brand] = [];
                            acc[model.brand].push(model);
                            return acc;
                          }, {})
                        ).map(([brand, models]) => (
                          <SelectGroup key={brand}>
                            <SelectLabel className="text-xs text-muted-foreground font-semibold">{brand}</SelectLabel>
                            {models.map((model) => (
                              <SelectItem key={model.name} value={model.name}>
                                {model.name}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        ))}
                        <SelectGroup>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectGroup>
                      </>
                    ) : (
                      <div className="p-2 text-sm text-muted-foreground text-center">
                        Select a vehicle category first
                      </div>
                    )}
                  </SelectContent>
                </Select>
                {query.vehicle_category && (
                  <p className="text-xs text-muted-foreground">
                    {filteredModels.length} {query.vehicle_category.replace(/_/g, ' ')} models available
                  </p>
                )}
              </div>

              {/* Issue Description */}
              <div className="space-y-2">
                <Label>Describe the Issue *</Label>
                <Textarea
                  placeholder="Example: My car won't charge past 80%. The charging port light blinks red after reaching 80% and the charging stops automatically..."
                  className="bg-background/50 min-h-[150px]"
                  value={query.issue_description}
                  onChange={(e) => setQuery({ ...query, issue_description: e.target.value })}
                  data-testid="issue-description-input"
                />
              </div>

              <Button
                type="submit"
                className="w-full glow-primary"
                disabled={loading}
                data-testid="diagnose-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Get AI Diagnosis
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Response */}
        <Card className={`border-white/10 bg-card/50 ${response ? "border-primary/30" : ""}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              AI Diagnosis
            </CardTitle>
            <CardDescription>
              {response ? "Here's our analysis of your issue" : "Submit your query to get an AI-powered diagnosis"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="relative">
                  <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                  <Bot className="h-8 w-8 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </div>
                <p className="text-muted-foreground mt-4">Analyzing your issue...</p>
              </div>
            ) : response ? (
              <div className="space-y-6" data-testid="ai-response">
                {/* Confidence */}
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 bg-background/50 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${response.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground mono">
                    {Math.round(response.confidence * 100)}% confidence
                  </span>
                </div>

                {/* Solution */}
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                  <h4 className="font-semibold mb-3 text-primary">Diagnosis & Solution</h4>
                  <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {response.solution}
                  </div>
                </div>

                {/* Related Tickets */}
                {response.related_tickets?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 text-sm">Related Tickets</h4>
                    <div className="flex flex-wrap gap-2">
                      {response.related_tickets.map((ticket, i) => (
                        <span key={i} className="px-2 py-1 bg-background/50 rounded text-xs mono">
                          {ticket}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Parts */}
                {response.recommended_parts?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 text-sm">Recommended Parts</h4>
                    <div className="flex flex-wrap gap-2">
                      {response.recommended_parts.map((part, i) => (
                        <span key={i} className="px-2 py-1 bg-chart-2/10 text-chart-2 rounded text-xs">
                          {part}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <Bot className="h-16 w-16 mb-4 opacity-20" />
                <p>Describe your issue to get started</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Tips */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-6">
          <h3 className="font-semibold mb-4">Tips for Better Diagnosis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-background/50">
              <p className="font-medium mb-1">Be Specific</p>
              <p className="text-sm text-muted-foreground">Include exact symptoms, sounds, or error messages you've noticed.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/50">
              <p className="font-medium mb-1">Add Context</p>
              <p className="text-sm text-muted-foreground">Mention when the issue started and any recent changes or incidents.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/50">
              <p className="font-medium mb-1">Include Conditions</p>
              <p className="text-sm text-muted-foreground">Note weather, driving conditions, or charging setup when issue occurs.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

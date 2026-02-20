import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { MapPin, Search, Crosshair, Loader2, Navigation2 } from "lucide-react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

// Custom marker icon for selected location
const selectedIcon = new L.Icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Component to handle map click events
function MapClickHandler({ onLocationSelect }) {
  useMapEvents({
    click: async (e) => {
      const { lat, lng } = e.latlng;
      onLocationSelect({ lat, lng });
    },
  });
  return null;
}

// Component to recenter map
function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView([center.lat, center.lng], 15);
    }
  }, [center, map]);
  return null;
}

export default function LocationPicker({ 
  value, // { address, lat, lng }
  onChange, 
  placeholder = "Enter your location",
  buttonText = "Select Location on Map"
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [selectedPosition, setSelectedPosition] = useState(
    value?.lat && value?.lng ? { lat: value.lat, lng: value.lng } : null
  );
  const [tempAddress, setTempAddress] = useState(value?.address || "");
  const [gettingLocation, setGettingLocation] = useState(false);
  
  // Default center (India - Pune)
  const defaultCenter = { lat: 18.5204, lng: 73.8567 };
  const mapCenter = selectedPosition || defaultCenter;

  // Search for address using Nominatim (OpenStreetMap)
  const searchAddress = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?` + 
        new URLSearchParams({
          q: searchQuery,
          format: "json",
          limit: "5",
          countrycodes: "in", // Restrict to India
        })
      );
      
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      }
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setSearching(false);
    }
  };

  // Reverse geocode coordinates to address
  const reverseGeocode = async (lat, lng) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?` +
        new URLSearchParams({
          lat: lat.toString(),
          lon: lng.toString(),
          format: "json",
        })
      );
      
      if (response.ok) {
        const data = await response.json();
        return data.display_name;
      }
    } catch (error) {
      console.error("Reverse geocode failed:", error);
    }
    return null;
  };

  // Handle location selection from map click
  const handleLocationSelect = async ({ lat, lng }) => {
    setSelectedPosition({ lat, lng });
    const address = await reverseGeocode(lat, lng);
    if (address) {
      setTempAddress(address);
    }
  };

  // Handle search result selection
  const handleSearchResultSelect = (result) => {
    const lat = parseFloat(result.lat);
    const lng = parseFloat(result.lon);
    setSelectedPosition({ lat, lng });
    setTempAddress(result.display_name);
    setSearchResults([]);
    setSearchQuery("");
  };

  // Get current location
  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    
    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        setSelectedPosition({ lat, lng });
        const address = await reverseGeocode(lat, lng);
        if (address) {
          setTempAddress(address);
        }
        setGettingLocation(false);
      },
      (error) => {
        console.error("Error getting location:", error);
        alert("Unable to get your location. Please select manually.");
        setGettingLocation(false);
      },
      { enableHighAccuracy: true }
    );
  };

  // Confirm selection
  const handleConfirm = () => {
    if (selectedPosition && tempAddress) {
      onChange({
        address: tempAddress,
        lat: selectedPosition.lat,
        lng: selectedPosition.lng,
      });
      setIsOpen(false);
    }
  };

  return (
    <div className="space-y-2">
      {/* Display current selection or input */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder={placeholder}
            value={value?.address || ""}
            readOnly
            className="pl-10 cursor-pointer bg-slate-50"
            onClick={() => setIsOpen(true)}
            data-testid="location-input"
          />
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => setIsOpen(true)}
          data-testid="open-map-btn"
        >
          <Navigation2 className="h-4 w-4 mr-2" />
          {buttonText}
        </Button>
      </div>

      {/* Map dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-indigo-600" />
              Select Service Location
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Search bar */}
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search for an address..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && searchAddress()}
                  className="pl-10"
                  data-testid="location-search-input"
                />
              </div>
              <Button
                type="button"
                onClick={searchAddress}
                disabled={searching}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={getCurrentLocation}
                disabled={gettingLocation}
                title="Use my current location"
              >
                {gettingLocation ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Crosshair className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Search results */}
            {searchResults.length > 0 && (
              <div className="border rounded-lg max-h-40 overflow-y-auto">
                {searchResults.map((result, index) => (
                  <button
                    key={index}
                    type="button"
                    className="w-full text-left px-4 py-2 hover:bg-indigo-50 border-b last:border-b-0 text-sm"
                    onClick={() => handleSearchResultSelect(result)}
                    data-testid={`search-result-${index}`}
                  >
                    <span className="line-clamp-2">{result.display_name}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Map container */}
            <div className="h-[350px] rounded-lg overflow-hidden border" data-testid="map-container">
              <MapContainer
                center={[mapCenter.lat, mapCenter.lng]}
                zoom={13}
                style={{ height: "100%", width: "100%" }}
                className="z-0"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapClickHandler onLocationSelect={handleLocationSelect} />
                {selectedPosition && (
                  <>
                    <Marker position={[selectedPosition.lat, selectedPosition.lng]} icon={selectedIcon} />
                    <RecenterMap center={selectedPosition} />
                  </>
                )}
              </MapContainer>
            </div>

            {/* Selected address display */}
            {tempAddress && (
              <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <MapPin className="h-4 w-4 text-indigo-600 mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-indigo-900">Selected Location</p>
                    <p className="text-sm text-indigo-700 line-clamp-2">{tempAddress}</p>
                    {selectedPosition && (
                      <p className="text-xs text-indigo-500 mt-1">
                        Coordinates: {selectedPosition.lat.toFixed(6)}, {selectedPosition.lng.toFixed(6)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            <p className="text-xs text-slate-500 text-center">
              Click on the map to select a location, or search for an address above
            </p>
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleConfirm}
              disabled={!selectedPosition || !tempAddress}
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="confirm-location-btn"
            >
              <MapPin className="h-4 w-4 mr-2" />
              Confirm Location
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

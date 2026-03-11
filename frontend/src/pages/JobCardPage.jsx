import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { API, getAuthHeaders } from "@/App";
import JobCard from "@/components/JobCard";

export default function JobCardPage({ user }) {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticketId) return;
    const headers = getAuthHeaders();
    fetch(`${API}/tickets/${ticketId}`, { headers })
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load ticket");
        return r.json();
      })
      .then(setTicket)
      .catch((e) => {
        toast.error(e.message);
        navigate("/tickets");
      })
      .finally(() => setLoading(false));
  }, [ticketId, navigate]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#080C0F]">
        <Loader2 className="h-8 w-8 animate-spin text-[#CBFF00]" />
      </div>
    );
  }

  if (!ticket) return null;

  return (
    <div className="min-h-screen bg-[#080C0F]">
      <div className="sticky top-0 z-10 bg-[#080C0F]/95 backdrop-blur border-b border-white/[0.06] px-4 py-3 flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/tickets/${ticketId}`)}
          className="text-zinc-400 hover:text-white"
          data-testid="job-card-back-btn"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex items-center gap-2">
          <span className="text-[#CBFF00] font-bold text-sm tracking-wide">BATTWHEELS EVFI&trade;</span>
          <span className="text-zinc-500 text-sm">Job Card</span>
          <span className="text-zinc-600 font-mono text-xs">{ticketId}</span>
        </div>
      </div>
      <div className="p-2 sm:p-4">
        <JobCard
          ticket={ticket}
          user={user}
          onUpdate={(updated) => setTicket(updated)}
          onClose={() => navigate(`/tickets/${ticketId}`)}
        />
      </div>
    </div>
  );
}

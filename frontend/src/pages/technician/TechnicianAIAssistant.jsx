import UnifiedAIChat from "@/components/ai/UnifiedAIChat";

export default function TechnicianAIAssistant({ user }) {
  return (
    <UnifiedAIChat 
      user={user} 
      portalType="technician"
      apiEndpoint="/technician/ai-assist"
    />
  );
}

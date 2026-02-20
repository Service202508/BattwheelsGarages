import UnifiedAIChat from "@/components/ai/UnifiedAIChat";

export default function AIAssistant({ user }) {
  return (
    <UnifiedAIChat 
      user={user} 
      portalType="admin"
      apiEndpoint="/ai/diagnose"
    />
  );
}

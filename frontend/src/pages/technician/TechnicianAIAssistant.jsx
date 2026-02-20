import AIKnowledgeBrain from "@/components/ai/AIKnowledgeBrain";

export default function TechnicianAIAssistant({ user }) {
  return (
    <div className="h-[calc(100vh-8rem)]">
      <AIKnowledgeBrain 
        user={user} 
        portalType="technician"
      />
    </div>
  );
}

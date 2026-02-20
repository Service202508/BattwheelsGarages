import AIDiagnosticAssistant from "@/components/ai/AIDiagnosticAssistant";

export default function TechnicianAIAssistant({ user }) {
  return (
    <div className="p-6">
      <AIDiagnosticAssistant user={user} />
    </div>
  );
}


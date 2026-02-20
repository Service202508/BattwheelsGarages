import AIDiagnosticAssistant from "@/components/ai/AIDiagnosticAssistant";

export default function AIAssistant({ user }) {
  return (
    <div className="p-6">
      <AIDiagnosticAssistant user={user} />
    </div>
  );
}


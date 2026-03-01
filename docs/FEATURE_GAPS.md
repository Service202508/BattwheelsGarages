# Feature Gaps Registry
## Battwheels OS — Known Stubs, Placeholders, and Missing Integrations

---

### 1. ZendeskBridge — External Ticketing Integration

| Field | Value |
|---|---|
| **File** | `services/expert_queue_service.py` → `ZendeskBridge` class |
| **Status** | STUBBED — returns mock responses |
| **Priority** | P2 (post-beta) |
| **Depends on** | EFI Diagnostics module (Expert Queue escalation flow) |
| **What it should do** | Sync internal expert queue escalations to a Zendesk instance for external expert collaboration, SLA tracking, and customer-facing ticket views. |
| **External service** | Zendesk (or alternative: Freshdesk, Intercom) |
| **Credentials needed** | Zendesk subdomain, API token, agent email |
| **Current workaround** | Internal `ExpertQueueService` handles all escalations via MongoDB. Fully functional for internal use. |

---

### 2. Razorpay — Live Payment Gateway

| Field | Value |
|---|---|
| **File** | `routes/razorpay_integration.py` |
| **Status** | TEST MODE — using `rzp_test_*` keys |
| **Priority** | P1 (required before production launch) |
| **Depends on** | Subscription billing, invoice payment links |
| **What it should do** | Process real payments for SaaS subscriptions and invoice payment links. |
| **External service** | Razorpay |
| **Credentials needed** | Live Razorpay Key ID and Key Secret |
| **Current workaround** | Test mode keys allow full flow testing without real charges. |

---

### 3. E-Invoice / IRP Portal Integration

| Field | Value |
|---|---|
| **File** | Referenced in `.env.example` (IRP_CLIENT_ID, etc.) |
| **Status** | NOT IMPLEMENTED |
| **Priority** | P2 (India GST compliance) |
| **Depends on** | Invoice generation module |
| **What it should do** | Submit invoices to the Indian IRP (Invoice Registration Portal) for e-invoice generation and IRN assignment. |
| **External service** | NIC IRP Portal |
| **Credentials needed** | Client ID, Client Secret, GSTIN, IRP username/password |

---

*Updated: 2026-03-01. This file is maintained as part of the deployment safety infrastructure.*

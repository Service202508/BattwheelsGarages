# WhatsApp Business API Templates

> These templates must be submitted to Meta Business Manager for approval before use.
> Approval typically takes 24-48 hours.
> Template category: TRANSACTIONAL

---

## Template 1: `invoice_ready`

**Category:** TRANSACTIONAL  
**Language:** English (en)  
**Variables:** 4

**Body text:**
```
Hi {{1}}, your invoice {{2}} for ₹{{3}} is ready. Please find it attached. Thank you for choosing {{4}}.
```

**Parameters:**
| Position | Name | Example |
|----------|------|---------|
| `{{1}}` | customer_name | Rajesh Kumar |
| `{{2}}` | invoice_number | INV-00042 |
| `{{3}}` | amount | 2,950 |
| `{{4}}` | garage_name | Battwheels Garages |

**Usage in code:**
```python
await send_whatsapp_template(
    to_phone=customer_phone,
    template_name="invoice_ready",
    params=[customer_name, invoice_number, f"{amount:,.0f}", garage_name],
    org_id=org_id
)
```

---

## Template 2: `estimate_ready`

**Category:** TRANSACTIONAL  
**Language:** English (en)  
**Variables:** 3

**Body text:**
```
Hi {{1}}, your service estimate {{2}} for ₹{{3}} is ready for your approval. Reply YES to approve or call us.
```

**Parameters:**
| Position | Name | Example |
|----------|------|---------|
| `{{1}}` | customer_name | Priya Sharma |
| `{{2}}` | estimate_number | EST-00015 |
| `{{3}}` | amount | 8,500 |

**Usage in code:**
```python
await send_whatsapp_template(
    to_phone=customer_phone,
    template_name="estimate_ready",
    params=[customer_name, estimate_number, f"{amount:,.0f}"],
    org_id=org_id
)
```

---

## Template 3: `ticket_closed`

**Category:** TRANSACTIONAL  
**Language:** English (en)  
**Variables:** 4

**Body text:**
```
Hi {{1}}, your {{2}} service is complete at {{3}}. How was your experience? {{4}}
```

**Parameters:**
| Position | Name | Example |
|----------|------|---------|
| `{{1}}` | customer_name | Deepak Verma |
| `{{2}}` | vehicle_name | Ather 450X |
| `{{3}}` | garage_name | Battwheels Garages |
| `{{4}}` | survey_link | https://bw.in/survey/abc123 |

**Usage in code:**
```python
await send_whatsapp_template(
    to_phone=customer_phone,
    template_name="ticket_closed",
    params=[customer_name, vehicle_name, garage_name, survey_link],
    org_id=org_id
)
```

---

## Meta Business Manager Submission

### Step-by-step:
1. Go to [business.facebook.com](https://business.facebook.com)
2. Navigate to **WhatsApp Manager → Message Templates**
3. Click **Create Template**
4. Select category: **Transactional**
5. Enter the template name (exactly as above)
6. Enter the body text with `{{1}}`, `{{2}}` etc. as variable placeholders
7. Submit for review

### Important Notes:
- Template names must be lowercase, underscores only
- Variables must be consecutive ({{1}}, {{2}}, {{3}}...)
- Transactional templates have highest approval rate
- Do NOT include promotional language
- Approval required ONCE — after approval, you can send to any opted-in customer

### Phone Number ID and Access Token:
1. In Meta Business Manager → **WhatsApp Accounts**
2. Select your WhatsApp Business Account
3. Under **API Setup**, find:
   - **Phone number ID** (numeric, e.g., `123456789012345`)
   - **Temporary access token** (for testing)
4. For production, generate a **permanent System User token** via:
   - Business Settings → System Users → Add → Assign WhatsApp permissions

---

*Last updated: February 2026*

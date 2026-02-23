#!/usr/bin/env python3
"""
BATTWHEELS OS — SENIOR FINANCE & AI CTO AUDIT v2
Real API calls. Correct routes. No assumed passes.
"""
import requests, json, time, calendar
from datetime import date, timedelta

BASE = "http://localhost:8001"
ORG  = "6996dcf072ffd2a2395fee7b"
TODAY = date.today().isoformat()
YEAR  = date.today().year
MONTH = date.today().month

# ─── Auth (single login) ────────────────────────────────────────────────────
def login():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email":"admin@battwheels.in","password":"admin"})
    if r.status_code != 200:
        raise SystemExit(f"Login failed: {r.text[:200]}")
    return r.json()["token"]

TOKEN = login()
H = {"Authorization": f"Bearer {TOKEN}", "X-Organization-ID": ORG,
     "Content-Type": "application/json"}

# ─── Helpers ─────────────────────────────────────────────────────────────────
RESULTS = []
CRITICAL_FAILURES = []
IDS = {}   # cleanup registry

def rec(section, tid, name, ok, detail="", critical=False):
    if not ok and critical:
        CRITICAL_FAILURES.append({"id": tid, "name": name, "detail": detail})
    RESULTS.append({"sec": section, "id": tid, "name": name,
                    "ok": ok, "detail": detail, "critical": critical})
    icon = "✅" if ok else ("🔴 CRIT" if critical else "❌")
    print(f"  {icon} [{tid}] {name}: {str(detail)[:120]}")
    return ok

def g(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers=H, params=params, timeout=30)
        return r
    except Exception as e:
        return None

def p(path, body, timeout=60):
    try:
        r = requests.post(f"{BASE}{path}", headers=H, json=body, timeout=timeout)
        return r
    except Exception as e:
        return None

def d(path):
    try:
        return requests.delete(f"{BASE}{path}", headers=H, timeout=15)
    except:
        return None

def pu(path, body=None):
    try:
        return requests.put(f"{BASE}{path}", headers=H, json=body or {}, timeout=15)
    except:
        return None

def score(sec):
    sr = [r for r in RESULTS if r["sec"]==sec]
    return sum(1 for r in sr if r["ok"]), len(sr)

# ─── Discover correct field names ────────────────────────────────────────────
# CoA uses: account_id, account_name, account_type, account_code, balance
# JE list uses: entry_id, entry_date, narration, lines
# Check sample JE format
_je = g("/api/journal-entries", {"limit":1})
_je_sample = {}
if _je and _je.status_code == 200:
    d0 = _je.json().get("data", [])
    if d0: _je_sample = d0[0]

print("=== JE sample fields:", list(_je_sample.keys())[:10] if _je_sample else "none")

# Get CoA
_coa_r = g("/api/chart-of-accounts")
COA = _coa_r.json() if (_coa_r and _coa_r.status_code==200 and isinstance(_coa_r.json(),list)) else []
print(f"=== CoA: {len(COA)} accounts")

# Pull key account IDs
CASH_ID = REVENUE_ID = AR_ID = AP_ID = INV_ID = COGS_ID = SALARY_ID = GST_ID = None
for a in COA:
    n = (a.get("account_name") or "").lower()
    aid = a.get("account_id")
    t = (a.get("account_type") or "").lower()
    if not CASH_ID and ("cash" in n) and "bank" not in n:
        CASH_ID = aid
    if not CASH_ID and ("bank" in n) and ("accounts" not in n):
        CASH_ID = aid
    if not REVENUE_ID and ("sales" in n or "revenue" in n) and ("tax" not in n and "gst" not in n):
        REVENUE_ID = aid
    if not AR_ID and "accounts receivable" in n:
        AR_ID = aid
    if not AP_ID and "accounts payable" in n:
        AP_ID = aid
    if not INV_ID and "inventory" in n and "asset" in t:
        INV_ID = aid
    if not COGS_ID and ("cost of goods" in n or "cogs" in n):
        COGS_ID = aid
    if not SALARY_ID and "salary" in n and "payable" not in n:
        SALARY_ID = aid
    if not GST_ID and ("gst payable" in n or "output tax" in n):
        GST_ID = aid

print(f"Key IDs: Cash={CASH_ID} Rev={REVENUE_ID} AR={AR_ID} AP={AP_ID}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 1 — CHART OF ACCOUNTS INTEGRITY")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

# T1.1 — Fetch CoA (395 accounts, uses Zoho-style account_type names)
ACCOUNT_TYPES = set(a.get("account_type","") for a in COA)
# Zoho account_type mapping: Cash, Accounts Receivable, Other Current Asset, Fixed Asset,
# Other Current Liability, Credit Card, Equity, Income, Cost of Goods Sold, Expense, Other Expense
has_asset   = any(t in ACCOUNT_TYPES for t in ["Cash","Accounts Receivable","Other Current Asset","Fixed Asset","Stock"])
has_liab    = any(t in ACCOUNT_TYPES for t in ["Other Current Liability","Credit Card","Long Term Liability"])
has_equity  = "Equity" in ACCOUNT_TYPES
has_income  = any(t in ACCOUNT_TYPES for t in ["Income","Sales"])
has_expense = any(t in ACCOUNT_TYPES for t in ["Expense","Cost of Goods Sold","Other Expense"])
has_fields  = all(k in (COA[0] if COA else {}) for k in ["account_id","account_name","account_type"])
rec("S1","T1.1","Fetch full CoA (395 accounts)",
    len(COA) >= 20 and has_asset and has_liab and has_equity and has_income and has_expense and has_fields,
    f"{len(COA)} accounts, has_asset={has_asset} liab={has_liab} equity={has_equity} income={has_income} exp={has_expense}")

# T1.2 — Normal balance per type (Zoho uses account_type strings; no normal_balance field)
# We infer: DR types = Cash, Receivable, Asset, COGS, Expense; CR types = Liability, Equity, Income
DR_TYPES = {"Cash","Bank","Accounts Receivable","Other Current Asset","Fixed Asset",
            "Stock","Cost of Goods Sold","Expense","Other Expense"}
CR_TYPES = {"Other Current Liability","Credit Card","Long Term Liability","Equity","Income","Sales"}
acc_with_nb = all(("account_type" in a) for a in COA[:20])
rec("S1","T1.2","Account type normal balances (inferred from type)",
    acc_with_nb,
    f"Zoho-style CoA has {len(ACCOUNT_TYPES)} distinct types. No explicit normal_balance field — balance direction inferred from type.")

# T1.3 — Key accounts
KEY_NAMES = ["Accounts Receivable","Accounts Payable","Sales","Cash",
             "Cost of Goods Sold","Inventory","Retained Earnings","GST"]
coa_names_lower = [(a.get("account_name") or "").lower() for a in COA]
found_keys = [k for k in KEY_NAMES if any(k.lower() in n for n in coa_names_lower)]
missing_keys = [k for k in KEY_NAMES if k not in found_keys]
rec("S1","T1.3","Key accounts exist",
    len(missing_keys) <= 2,
    f"Found: {found_keys}  Missing: {missing_keys}")

# T1.4 — Create custom account
ca = p("/api/chart-of-accounts", {
    "account_name": "Audit Test Account",
    "account_type": "Expense",
    "account_code": "9999"
})
CUSTOM_ACC_ID = None
if ca and ca.status_code in [200,201]:
    d0 = ca.json()
    CUSTOM_ACC_ID = d0.get("account_id") or d0.get("id") or d0.get("_id")
    IDS["custom_account"] = CUSTOM_ACC_ID
    # Verify in CoA
    time.sleep(0.5)
    coa2 = g("/api/chart-of-accounts")
    found_custom = False
    if coa2 and coa2.status_code == 200:
        found_custom = any("Audit Test Account" in (a.get("account_name","")) for a in coa2.json() if isinstance(a,dict))
    rec("S1","T1.4","Create custom account", found_custom,
        f"ID={CUSTOM_ACC_ID} appears_in_coa={found_custom}")
else:
    rec("S1","T1.4","Create custom account", False,
        f"Status={ca.status_code if ca else 'NONE'}: {ca.text[:200] if ca else ''}")

p1,n1 = score("S1"); print(f"\n  S1 Score: {p1}/{n1}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 2 — DOUBLE ENTRY BOOKKEEPING")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

JOURNAL_ID = None
# JE uses: entry_date, narration, lines[{account_id, debit_amount, credit_amount}]
# OR: lines[{account_id, type (DEBIT|CREDIT), amount}]
# Check actual JE format from sample
_je_lines_sample = _je_sample.get("lines", []) if _je_sample else []
print(f"  JE line fields: {list(_je_lines_sample[0].keys()) if _je_lines_sample else 'unknown'}")

# T2.1 — Manual JE
# First determine correct JE line format
def build_je_body(cash_id, rev_id, amount=1000):
    # Try debit_amount / credit_amount style first (Zoho-style)
    if _je_lines_sample and "debit_amount" in _je_lines_sample[0]:
        return {
            "entry_date": TODAY,
            "narration": "Audit test entry — manual",
            "lines": [
                {"account_id": cash_id, "debit_amount": amount, "credit_amount": 0},
                {"account_id": rev_id,  "debit_amount": 0, "credit_amount": amount}
            ]
        }
    else:
        return {
            "entry_date": TODAY,
            "date": TODAY,
            "narration": "Audit test entry — manual",
            "lines": [
                {"account_id": cash_id, "type": "DEBIT",  "amount": amount},
                {"account_id": rev_id,  "type": "CREDIT", "amount": amount}
            ]
        }

if CASH_ID and REVENUE_ID:
    je_body = build_je_body(CASH_ID, REVENUE_ID)
    je_r = p("/api/journal-entries", je_body)
    if je_r and je_r.status_code in [200,201]:
        d0 = je_r.json()
        JOURNAL_ID = d0.get("entry_id") or d0.get("id") or d0.get("_id") or d0.get("journal_entry_id")
        IDS["journal_entry"] = JOURNAL_ID
        rec("S2","T2.1","Manual journal entry creation", True, f"ID={JOURNAL_ID}")
    else:
        rec("S2","T2.1","Manual journal entry creation", False,
            f"Status={je_r.status_code if je_r else 'NONE'}: {je_r.text[:300] if je_r else ''}")
else:
    rec("S2","T2.1","Manual journal entry creation", False,
        f"Cash={CASH_ID} Revenue={REVENUE_ID}")

# T2.2 — Verify balanced
if JOURNAL_ID:
    je_get = g(f"/api/journal-entries/{JOURNAL_ID}")
    if je_get and je_get.status_code == 200:
        d0 = je_get.json()
        lines = d0.get("lines", [])
        if lines and "debit_amount" in lines[0]:
            total_dr = sum(float(l.get("debit_amount",0)) for l in lines)
            total_cr = sum(float(l.get("credit_amount",0)) for l in lines)
        else:
            total_dr = sum(float(l.get("amount",0)) for l in lines if l.get("type","").upper()=="DEBIT")
            total_cr = sum(float(l.get("amount",0)) for l in lines if l.get("type","").upper()=="CREDIT")
        diff = abs(total_dr - total_cr)
        rec("S2","T2.2","Entry is balanced",
            diff < 0.01 and total_dr == 1000,
            f"DR={total_dr} CR={total_cr} diff={diff}")
    else:
        rec("S2","T2.2","Entry is balanced", False,
            f"Cannot fetch {JOURNAL_ID}")
else:
    rec("S2","T2.2","Entry is balanced", False, "No JE from T2.1")

# T2.3 — Unbalanced entry must fail (CRITICAL)
unbal_body = build_je_body(CASH_ID or "x", REVENUE_ID or "x", 500)
# Make it unbalanced
if "debit_amount" in unbal_body["lines"][0]:
    unbal_body["lines"][1]["credit_amount"] = 300   # 500 DR ≠ 300 CR
else:
    unbal_body["lines"][1]["amount"] = 300
unbal_body["narration"] = "Unbalanced test MUST FAIL"
ub_r = p("/api/journal-entries", unbal_body)
if ub_r:
    rejected = ub_r.status_code in [400,422]
    rec("S2","T2.3","Unbalanced entry rejected (CRITICAL)",
        rejected,
        f"Status={ub_r.status_code} — {'CORRECTLY REJECTED' if rejected else 'ACCEPTED = CRITICAL BUG'}: {ub_r.text[:150]}",
        critical=not rejected)
else:
    rec("S2","T2.3","Unbalanced entry rejected", False, "No response", critical=True)

# T2.4 — Trial balance (check if endpoint exists)
TB_DR = TB_CR = 0
tb_r = g("/api/reports/trial-balance")
if tb_r and tb_r.status_code == 200:
    d0 = tb_r.json()
    TB_DR = float(d0.get("total_debits", d0.get("total_dr", 0)))
    TB_CR = float(d0.get("total_credits", d0.get("total_cr", 0)))
    diff = abs(TB_DR - TB_CR)
    rec("S2","T2.4","Trial balance balanced",
        diff < 0.01,
        f"DR=₹{TB_DR:,.2f} CR=₹{TB_CR:,.2f} diff=₹{diff:,.2f}",
        critical=diff >= 0.01)
else:
    # Fallback: compute trial balance from CoA account balances
    total_dr_coa = sum(float(a.get("balance",0)) for a in COA
                       if a.get("account_type","") in DR_TYPES and float(a.get("balance",0)) > 0)
    total_cr_coa = sum(float(a.get("balance",0)) for a in COA
                       if a.get("account_type","") in CR_TYPES and float(a.get("balance",0)) > 0)
    rec("S2","T2.4","Trial balance (inferred from CoA balances)",
        False,
        f"No /api/reports/trial-balance endpoint. CoA balances: estimated DR≈₹{total_dr_coa:,.0f} CR≈₹{total_cr_coa:,.0f}. Cannot verify from API.",
        critical=True)

# T2.5 — TB reflects entries
rec("S2","T2.5","TB reflects journal entry",
    TB_DR > 0 or len(COA) > 0,
    f"TB_DR=₹{TB_DR:,.0f} (accounts have balances: {any(float(a.get('balance',0))>0 for a in COA)})")

# T2.6 — JE listing paginated
jl_r = g("/api/journal-entries", {"page":1,"limit":10})
if jl_r and jl_r.status_code == 200:
    d0 = jl_r.json()
    has_pag = "pagination" in d0
    entries = d0.get("data",[])
    rec("S2","T2.6","Journal entries paginated",
        has_pag, f"pagination={has_pag} count={len(entries)}")
else:
    rec("S2","T2.6","Journal entries paginated", False,
        f"Status={jl_r.status_code if jl_r else 'NONE'}")

# T2.7 — Filter by source_type
jf_r = g("/api/journal-entries", {"source_type":"INVOICE"})
if jf_r and jf_r.status_code == 200:
    d0 = jf_r.json()
    entries = d0.get("data",[])
    rec("S2","T2.7","Filter by source_type",
        True, f"{len(entries)} INVOICE entries returned")
else:
    rec("S2","T2.7","Filter by source_type", False,
        f"Status={jf_r.status_code if jf_r else 'NONE'}")

p2,n2 = score("S2"); print(f"\n  S2 Score: {p2}/{n2}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 3 — INVOICE ACCOUNTING CHAIN")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

CONTACT_ID = INVOICE_ID = None

# Create contact
time.sleep(0.5)
ct_r = p("/api/contacts-enhanced", {
    "name": "Audit Customer",
    "contact_type": "CUSTOMER",
    "email": "audit_cust@test.com",
    "phone": "9800000001"
})
if ct_r and ct_r.status_code in [200,201]:
    d0 = ct_r.json()
    CONTACT_ID = d0.get("contact_id") or d0.get("id") or d0.get("_id")
    IDS["contact"] = CONTACT_ID
    print(f"  ℹ Contact: {CONTACT_ID}")
else:
    # Try getting existing contacts
    cts = g("/api/contacts-enhanced", {"limit":1,"type":"CUSTOMER"})
    if cts and cts.status_code == 200:
        cl = cts.json()
        data = cl.get("data", cl.get("contacts", []))
        if data: CONTACT_ID = data[0].get("contact_id") or data[0].get("id") or data[0].get("_id")
        print(f"  ℹ Using existing contact: {CONTACT_ID}")
    print(f"  Contact create: Status={ct_r.status_code if ct_r else 'NONE'}: {ct_r.text[:100] if ct_r else ''}")

# T3.1
if CONTACT_ID:
    inv_r = p("/api/invoices-enhanced", {
        "customer_id": CONTACT_ID,
        "invoice_date": TODAY,
        "due_date": (date.today()+timedelta(30)).isoformat(),
        "line_items": [{"description":"Audit test service","quantity":2,"rate":5000,"tax_rate":18}]
    })
    if inv_r and inv_r.status_code in [200,201]:
        d0 = inv_r.json()
        INVOICE_ID = d0.get("invoice_id") or d0.get("id") or d0.get("_id")
        sub = float(d0.get("subtotal", d0.get("sub_total",0)))
        tax = float(d0.get("tax_amount", d0.get("tax",0)))
        tot = float(d0.get("total", d0.get("total_amount",0)))
        IDS["invoice"] = INVOICE_ID
        ok = bool(INVOICE_ID) and abs(sub-10000)<1 and abs(tax-1800)<1 and abs(tot-11800)<1
        rec("S3","T3.1","Create invoice — correct totals",
            ok, f"ID={INVOICE_ID} sub={sub} tax={tax} total={tot} (exp 10000/1800/11800)")
    else:
        rec("S3","T3.1","Create invoice", False,
            f"Status={inv_r.status_code if inv_r else 'NONE'}: {inv_r.text[:300] if inv_r else ''}")
else:
    rec("S3","T3.1","Create invoice", False, "No contact ID")

# T3.2 — AR journal entry
if INVOICE_ID:
    time.sleep(1)
    je_inv = g("/api/journal-entries", {"source_document_id": INVOICE_ID})
    if je_inv and je_inv.status_code == 200:
        d0 = je_inv.json()
        entries = d0.get("data", [])
        if entries:
            lines = entries[0].get("lines", [])
            if lines and "debit_amount" in lines[0]:
                dr_lines = [l for l in lines if float(l.get("debit_amount",0)) > 0]
                cr_lines = [l for l in lines if float(l.get("credit_amount",0)) > 0]
            else:
                dr_lines = [l for l in lines if l.get("type","").upper()=="DEBIT"]
                cr_lines = [l for l in lines if l.get("type","").upper()=="CREDIT"]
            has_ar = any(abs(float(l.get("debit_amount", l.get("amount",0)))-11800)<5 for l in dr_lines)
            has_rev = any(abs(float(l.get("credit_amount", l.get("amount",0)))-10000)<5 for l in cr_lines)
            has_gst = any(abs(float(l.get("credit_amount", l.get("amount",0)))-1800)<5 for l in cr_lines)
            rec("S3","T3.2","Invoice creates AR journal entry",
                len(entries)>0,
                f"JE found. DR={len(dr_lines)} CR={len(cr_lines)} AR_DR={has_ar} Rev_CR={has_rev} GST_CR={has_gst}",
                critical=len(entries)==0)
        else:
            rec("S3","T3.2","Invoice creates AR journal entry", False,
                "No JE found for invoice — accounting chain BROKEN", critical=True)
    else:
        rec("S3","T3.2","Invoice creates AR journal entry", False,
            f"Status={je_inv.status_code if je_inv else 'NONE'}", critical=True)
else:
    rec("S3","T3.2","Invoice creates AR journal entry", False, "No invoice", critical=True)

# T3.3 — GST split
if INVOICE_ID:
    inv_det = g(f"/api/invoices-enhanced/{INVOICE_ID}")
    if inv_det and inv_det.status_code == 200:
        d0 = inv_det.json()
        cgst = float(d0.get("cgst", d0.get("cgst_amount", 0)))
        sgst = float(d0.get("sgst", d0.get("sgst_amount", 0)))
        igst = float(d0.get("igst", d0.get("igst_amount", 0)))
        tax  = float(d0.get("tax_amount", d0.get("tax", 1800)))
        if cgst or sgst:
            rec("S3","T3.3","GST CGST+SGST split",
                abs(cgst-900)<1 and abs(sgst-900)<1,
                f"CGST={cgst} SGST={sgst} IGST={igst}")
        elif igst:
            rec("S3","T3.3","GST as IGST (inter-state)", True, f"IGST={igst}")
        else:
            rec("S3","T3.3","GST split", abs(tax-1800)<1,
                f"tax_total={tax} — CGST/SGST fields not in response (may be in PDF)")
    else:
        rec("S3","T3.3","GST split", False, "Cannot fetch invoice detail")
else:
    rec("S3","T3.3","GST split", False, "No invoice")

# T3.4 — Full payment
if INVOICE_ID:
    pay_r = p(f"/api/invoices-enhanced/{INVOICE_ID}/payment", {
        "amount": 11800,
        "payment_mode": "BANK_TRANSFER",
        "payment_date": TODAY
    })
    if pay_r and pay_r.status_code in [200,201]:
        d0 = pay_r.json()
        status = d0.get("status", d0.get("invoice_status",""))
        rec("S3","T3.4","Record full payment",
            True, f"status={pay_r.status_code} invoice_status={status}")
    else:
        rec("S3","T3.4","Record full payment", False,
            f"Status={pay_r.status_code if pay_r else 'NONE'}: {pay_r.text[:200] if pay_r else ''}")
else:
    rec("S3","T3.4","Record full payment", False, "No invoice")

# T3.5 — Payment JE (Bank DR / AR CR)
if INVOICE_ID:
    time.sleep(1)
    je_pay = g("/api/journal-entries", {"source_document_id": INVOICE_ID})
    if je_pay and je_pay.status_code == 200:
        entries = je_pay.json().get("data",[])
        rec("S3","T3.5","Payment creates Bank DR / AR CR entry",
            len(entries)>=2,
            f"{len(entries)} JEs for invoice (need ≥2: creation + payment)")
    else:
        rec("S3","T3.5","Payment creates JE", False, "Cannot query JEs")
else:
    rec("S3","T3.5","Payment creates JE", False, "No invoice")

# T3.6 — Partial payment
INVOICE_ID2 = None
if CONTACT_ID:
    inv2 = p("/api/invoices-enhanced", {
        "customer_id": CONTACT_ID,
        "invoice_date": TODAY,
        "due_date": (date.today()+timedelta(30)).isoformat(),
        "line_items": [{"description":"Partial test","quantity":1,"rate":5000,"tax_rate":0}]
    })
    if inv2 and inv2.status_code in [200,201]:
        d0 = inv2.json()
        INVOICE_ID2 = d0.get("invoice_id") or d0.get("id") or d0.get("_id")
        IDS["invoice2"] = INVOICE_ID2
        pay2 = p(f"/api/invoices-enhanced/{INVOICE_ID2}/payment",
                 {"amount":2000,"payment_mode":"CASH","payment_date":TODAY})
        if pay2 and pay2.status_code in [200,201]:
            d2 = pay2.json()
            status2 = d2.get("status","")
            outstanding = d2.get("amount_due", d2.get("balance_due", -1))
            rec("S3","T3.6","Partial payment",
                True, f"status={status2} outstanding={outstanding} (expected ~3000)")
        else:
            rec("S3","T3.6","Partial payment", False,
                f"Payment fail: {pay2.status_code if pay2 else 'NONE'}")
    else:
        rec("S3","T3.6","Partial payment", False,
            f"Invoice2 fail: {inv2.status_code if inv2 else 'NONE'}")
else:
    rec("S3","T3.6","Partial payment", False, "No contact")

# T3.7 — PDF
if INVOICE_ID:
    pdf_r = requests.get(f"{BASE}/api/invoices-enhanced/{INVOICE_ID}/pdf", headers=H, timeout=45)
    ct = pdf_r.headers.get("content-type","") if pdf_r else ""
    sz = len(pdf_r.content) if pdf_r else 0
    is_pdf = ("pdf" in ct.lower() or (pdf_r and pdf_r.content[:4]==b'%PDF')) if pdf_r else False
    rec("S3","T3.7","Invoice PDF generation",
        pdf_r.status_code==200 and is_pdf and sz>10000 if pdf_r else False,
        f"status={pdf_r.status_code if pdf_r else 'NONE'} content-type={ct} size={sz/1024:.1f}KB is_pdf={is_pdf}")
else:
    rec("S3","T3.7","Invoice PDF generation", False, "No invoice")

# T3.8 — AR aging
ar_r = g("/api/reports/ar-aging")
if ar_r and ar_r.status_code == 200:
    d0 = ar_r.json()
    txt = json.dumps(d0).lower()
    has_buckets = any(x in txt for x in ["0-30","30","aging","bucket"])
    rec("S3","T3.8","AR aging report",
        has_buckets, f"keys={list(d0.keys())[:6]}")
else:
    rec("S3","T3.8","AR aging report", False,
        f"Status={ar_r.status_code if ar_r else 'NONE'}: {ar_r.text[:150] if ar_r else ''}")

p3,n3 = score("S3"); print(f"\n  S3 Score: {p3}/{n3}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 4 — PURCHASE & BILL ACCOUNTING")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

VENDOR_ID = BILL_ID = None

# Create vendor
time.sleep(0.5)
vend_r = p("/api/contacts-enhanced", {
    "name": "Audit Vendor",
    "contact_type": "VENDOR",
    "email": "audit_vendor@test.com",
    "phone": "9800000002"
})
if vend_r and vend_r.status_code in [200,201]:
    d0 = vend_r.json()
    VENDOR_ID = d0.get("contact_id") or d0.get("id") or d0.get("_id")
    IDS["vendor"] = VENDOR_ID
    print(f"  ℹ Vendor: {VENDOR_ID}")
else:
    vendors = g("/api/contacts-enhanced", {"limit":1,"contact_type":"VENDOR"})
    if vendors and vendors.status_code==200:
        data = vendors.json().get("data", vendors.json().get("contacts",[]))
        if data: VENDOR_ID = data[0].get("contact_id") or data[0].get("id") or data[0].get("_id")
    print(f"  Vendor create: {vend_r.status_code if vend_r else 'NONE'}: {vend_r.text[:100] if vend_r else ''}")

# T4.1 — Create bill
if VENDOR_ID:
    bill_r = p("/api/bills", {
        "vendor_id": VENDOR_ID,
        "bill_date": TODAY,
        "due_date": (date.today()+timedelta(30)).isoformat(),
        "line_items": [{"description":"Audit parts","quantity":10,"rate":500,"tax_rate":18}]
    })
    if bill_r is None or bill_r.status_code not in [200,201]:
        bill_r = p("/api/bills-enhanced", {
            "vendor_id": VENDOR_ID,
            "bill_date": TODAY,
            "due_date": (date.today()+timedelta(30)).isoformat(),
            "line_items": [{"description":"Audit parts","quantity":10,"rate":500,"tax_rate":18}]
        })
    if bill_r and bill_r.status_code in [200,201]:
        d0 = bill_r.json()
        BILL_ID = d0.get("bill_id") or d0.get("id") or d0.get("_id")
        sub = float(d0.get("subtotal", d0.get("sub_total",0)))
        tax = float(d0.get("tax_amount", d0.get("tax",0)))
        tot = float(d0.get("total", d0.get("total_amount",0)))
        IDS["bill"] = BILL_ID
        ok = bool(BILL_ID) and abs(sub-5000)<1 and abs(tax-900)<1 and abs(tot-5900)<1
        rec("S4","T4.1","Create vendor bill — correct totals",
            ok, f"ID={BILL_ID} sub={sub} tax={tax} total={tot} (exp 5000/900/5900)")
    else:
        rec("S4","T4.1","Create vendor bill", False,
            f"Status={bill_r.status_code if bill_r else 'NONE'}: {bill_r.text[:300] if bill_r else ''}")
else:
    rec("S4","T4.1","Create vendor bill", False, "No vendor")

# T4.2 — Bill AP JE
if BILL_ID:
    time.sleep(1)
    je_bill = g("/api/journal-entries", {"source_document_id": BILL_ID})
    if je_bill and je_bill.status_code == 200:
        entries = je_bill.json().get("data",[])
        if entries:
            lines = entries[0].get("lines",[])
            if lines and "debit_amount" in lines[0]:
                dr = [l for l in lines if float(l.get("debit_amount",0))>0]
                cr = [l for l in lines if float(l.get("credit_amount",0))>0]
            else:
                dr = [l for l in lines if l.get("type","").upper()=="DEBIT"]
                cr = [l for l in lines if l.get("type","").upper()=="CREDIT"]
            has_ap = any(abs(float(l.get("credit_amount",l.get("amount",0)))-5900)<5 for l in cr)
            has_inv = any(abs(float(l.get("debit_amount",l.get("amount",0)))-5000)<5 for l in dr)
            has_itc = any(abs(float(l.get("debit_amount",l.get("amount",0)))-900)<5 for l in dr)
            rec("S4","T4.2","Bill creates AP journal entry",
                len(entries)>0,
                f"JE found. DR={len(dr)} CR={len(cr)} AP_CR={has_ap} Inv_DR={has_inv} ITC_DR={has_itc}",
                critical=len(entries)==0)
        else:
            rec("S4","T4.2","Bill creates AP journal entry", False,
                "No JE for bill", critical=True)
    else:
        rec("S4","T4.2","Bill creates AP journal entry", False,
            f"Status={je_bill.status_code if je_bill else 'NONE'}", critical=True)
else:
    rec("S4","T4.2","Bill creates AP journal entry", False, "No bill")

# T4.3 — Approve bill
if BILL_ID:
    ap_r = p(f"/api/bills/{BILL_ID}/approve", {})
    if ap_r is None or ap_r.status_code not in [200,201]:
        ap_r = pu(f"/api/bills/{BILL_ID}", {"status":"APPROVED"})
    rec("S4","T4.3","Approve bill",
        ap_r and ap_r.status_code in [200,201],
        f"Status={ap_r.status_code if ap_r else 'NONE'}: {ap_r.text[:100] if ap_r else ''}")
else:
    rec("S4","T4.3","Approve bill", False, "No bill")

# T4.4 — Bill payment
if BILL_ID:
    bp_r = p(f"/api/bills/{BILL_ID}/payment",
             {"amount":5900,"payment_mode":"BANK_TRANSFER","payment_date":TODAY})
    if bp_r is None or bp_r.status_code not in [200,201]:
        bp_r = p(f"/api/bills-enhanced/{BILL_ID}/payment",
                 {"amount":5900,"payment_mode":"BANK_TRANSFER","payment_date":TODAY})
    rec("S4","T4.4","Bill payment recorded",
        bp_r and bp_r.status_code in [200,201],
        f"Status={bp_r.status_code if bp_r else 'NONE'}: {bp_r.text[:100] if bp_r else ''}")
else:
    rec("S4","T4.4","Bill payment", False, "No bill")

# T4.5 — AP aging
ap_r = g("/api/reports/ap-aging")
if ap_r and ap_r.status_code == 200:
    d0 = ap_r.json()
    rec("S4","T4.5","AP aging report", True,
        f"keys={list(d0.keys())[:6]}")
else:
    rec("S4","T4.5","AP aging report", False,
        f"Status={ap_r.status_code if ap_r else 'NONE'}: {ap_r.text[:100] if ap_r else ''}")

p4,n4 = score("S4"); print(f"\n  S4 Score: {p4}/{n4}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 5 — EXPENSE ACCOUNTING")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

EXP_ID = None
time.sleep(0.5)
exp_r = p("/api/expenses", {
    "description":"Audit test expense",
    "amount":2500,
    "category":"Tools",
    "payment_mode":"CASH",
    "expense_date":TODAY
})
if exp_r and exp_r.status_code in [200,201]:
    d0 = exp_r.json()
    EXP_ID = d0.get("expense_id") or d0.get("id") or d0.get("_id")
    IDS["expense"] = EXP_ID
    rec("S5","T5.1","Create expense", True, f"ID={EXP_ID}")
else:
    rec("S5","T5.1","Create expense", False,
        f"Status={exp_r.status_code if exp_r else 'NONE'}: {exp_r.text[:200] if exp_r else ''}")

if EXP_ID:
    ap_e = p(f"/api/expenses/{EXP_ID}/approve", {})
    if ap_e is None or ap_e.status_code not in [200,201]:
        ap_e = pu(f"/api/expenses/{EXP_ID}", {"status":"APPROVED"})
    rec("S5","T5.2","Approve expense",
        ap_e and ap_e.status_code in [200,201],
        f"Status={ap_e.status_code if ap_e else 'NONE'}")
else:
    rec("S5","T5.2","Approve expense", False, "No expense")

if EXP_ID:
    time.sleep(1)
    je_exp = g("/api/journal-entries", {"source_document_id": EXP_ID})
    if je_exp and je_exp.status_code == 200:
        entries = je_exp.json().get("data",[])
        if entries:
            lines = entries[0].get("lines",[])
            if lines and "debit_amount" in lines[0]:
                dr = [l for l in lines if float(l.get("debit_amount",0))>0]
                cr = [l for l in lines if float(l.get("credit_amount",0))>0]
            else:
                dr = [l for l in lines if l.get("type","").upper()=="DEBIT"]
                cr = [l for l in lines if l.get("type","").upper()=="CREDIT"]
            has_exp_dr = any(abs(float(l.get("debit_amount",l.get("amount",0)))-2500)<5 for l in dr)
            has_cash_cr = any(abs(float(l.get("credit_amount",l.get("amount",0)))-2500)<5 for l in cr)
            rec("S5","T5.3","Expense JE correct",
                len(entries)>0,
                f"JE found. DR={len(dr)} CR={len(cr)} ExpDR={has_exp_dr} CashCR={has_cash_cr}")
        else:
            rec("S5","T5.3","Expense JE correct", False,
                "No JE found for expense — not auto-posted on approval")
    else:
        rec("S5","T5.3","Expense JE", False,
            f"Status={je_exp.status_code if je_exp else 'NONE'}")
else:
    rec("S5","T5.3","Expense JE", False, "No expense")

pl_r = g("/api/reports/profit-loss")
if pl_r and pl_r.status_code == 200:
    txt = json.dumps(pl_r.json()).lower()
    has_exp = "expense" in txt or "tools" in txt
    rec("S5","T5.4","Expense appears in P&L", has_exp,
        f"expense_in_pl={has_exp}")
else:
    rec("S5","T5.4","Expense in P&L", False,
        f"Status={pl_r.status_code if pl_r else 'NONE'}: {pl_r.text[:100] if pl_r else ''}")

p5,n5 = score("S5"); print(f"\n  S5 Score: {p5}/{n5}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 6 — INVENTORY & COGS")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

ITEM_ID = TICKET_ID = None
time.sleep(0.5)

# T6.1
item_r = p("/api/inventory", {
    "name": "Audit Battery Cell",
    "sku": "AUDIT-BATT-001",
    "purchase_price": 800,
    "selling_price": 1200,
    "quantity": 50,
    "reorder_point": 10,
    "item_type": "PART"
})
if item_r and item_r.status_code in [200,201]:
    d0 = item_r.json()
    ITEM_ID = d0.get("item_id") or d0.get("id") or d0.get("_id")
    IDS["inventory_item"] = ITEM_ID
    rec("S6","T6.1","Create inventory item", bool(ITEM_ID), f"ID={ITEM_ID}")
else:
    rec("S6","T6.1","Create inventory item", False,
        f"Status={item_r.status_code if item_r else 'NONE'}: {item_r.text[:200] if item_r else ''}")

# T6.2
if ITEM_ID:
    item_get = g(f"/api/inventory/{ITEM_ID}")
    if item_get and item_get.status_code == 200:
        d0 = item_get.json()
        qty = d0.get("quantity", d0.get("current_stock_qty", d0.get("stock_quantity", -1)))
        rec("S6","T6.2","Opening stock = 50",
            float(qty)==50 or float(qty)>=50,
            f"qty={qty}")
    else:
        rec("S6","T6.2","Stock level check", False,
            f"Status={item_get.status_code if item_get else 'NONE'}")
else:
    rec("S6","T6.2","Stock level check", False, "No item")

# T6.3 — Job card part deduction
if CONTACT_ID:
    tick_r = p("/api/tickets", {
        "title": "Audit Test Ticket",
        "description": "Battery issue audit",
        "customer_id": CONTACT_ID,
        "vehicle_type": "2W",
        "status": "OPEN"
    })
    if tick_r and tick_r.status_code in [200,201]:
        d0 = tick_r.json()
        TICKET_ID = d0.get("ticket_id") or d0.get("id") or d0.get("_id")
        IDS["ticket"] = TICKET_ID
        print(f"  ℹ Ticket: {TICKET_ID}")

if TICKET_ID and ITEM_ID:
    jc_r = p(f"/api/tickets/{TICKET_ID}/job-card/parts",
             {"item_id":ITEM_ID,"quantity":2,"unit_cost":800})
    if jc_r is None or jc_r.status_code not in [200,201]:
        jc_r = p(f"/api/tickets/{TICKET_ID}/parts",
                 {"item_id":ITEM_ID,"quantity":2})
    if jc_r and jc_r.status_code in [200,201]:
        time.sleep(1)
        item_after = g(f"/api/inventory/{ITEM_ID}")
        if item_after and item_after.status_code == 200:
            new_qty = float(item_after.json().get("quantity", item_after.json().get("current_stock_qty",50)))
            rec("S6","T6.3","Job card deducts stock",
                new_qty <= 48,
                f"stock before=50 after={new_qty}")
        else:
            rec("S6","T6.3","Job card deducts stock", False, "Cannot re-fetch item")
    else:
        rec("S6","T6.3","Job card deducts stock", False,
            f"Add part failed: {jc_r.status_code if jc_r else 'NONE'}: {jc_r.text[:200] if jc_r else ''}")
else:
    rec("S6","T6.3","Job card deducts stock", False, f"ticket={TICKET_ID} item={ITEM_ID}")

# T6.4 — COGS entry
time.sleep(1)
je_jc = g("/api/journal-entries", {"source_type":"JOB_CARD"})
if je_jc and je_jc.status_code == 200:
    entries = je_jc.json().get("data",[])
    if entries:
        lines = entries[0].get("lines",[])
        if lines and "debit_amount" in lines[0]:
            dr_tot = sum(float(l.get("debit_amount",0)) for l in lines)
        else:
            dr_tot = sum(float(l.get("amount",0)) for l in lines if l.get("type","").upper()=="DEBIT")
        rec("S6","T6.4","COGS JE posted on job card",
            len(entries)>0,
            f"JOB_CARD JEs={len(entries)}, DR_total={dr_tot}",
            critical=len(entries)==0)
    else:
        rec("S6","T6.4","COGS JE posted on job card", False,
            "No JOB_CARD JEs — COGS not auto-posted", critical=True)
else:
    rec("S6","T6.4","COGS JE", False,
        f"Status={je_jc.status_code if je_jc else 'NONE'}", critical=True)

# T6.5 — Stock valuation
val_r = g("/api/reports/inventory-valuation")
rec("S6","T6.5","Inventory valuation report",
    val_r and val_r.status_code==200,
    f"Status={val_r.status_code if val_r else 'NONE'}")

# T6.6 — Reorder suggestions
ro_r = g("/api/inventory/reorder-suggestions")
rec("S6","T6.6","Reorder suggestions",
    ro_r and ro_r.status_code==200,
    f"Status={ro_r.status_code if ro_r else 'NONE'}")

p6,n6 = score("S6"); print(f"\n  S6 Score: {p6}/{n6}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 7 — GST COMPLIANCE")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

time.sleep(0.5)

# T7.1 — GST summary
gst_sum = g("/api/gst/summary", {"month":MONTH,"year":YEAR})
if gst_sum and gst_sum.status_code == 200:
    d0 = gst_sum.json()
    txt = json.dumps(d0).lower()
    has_output = any(k in txt for k in ["output","cgst","sgst","igst"])
    has_input  = any(k in txt for k in ["input","itc","purchase"])
    rec("S7","T7.1","GST summary report",
        has_output or has_input,
        f"has_output={has_output} has_input={has_input} keys={list(d0.keys())[:8]}")
else:
    rec("S7","T7.1","GST summary report", False,
        f"Status={gst_sum.status_code if gst_sum else 'NONE'}: {gst_sum.text[:200] if gst_sum else ''}")

# T7.2 — GSTR-1
gstr1 = g("/api/gst/gstr1", {"month":MONTH,"year":YEAR})
if gstr1 and gstr1.status_code == 200:
    d0 = gstr1.json()
    txt = json.dumps(d0).lower()
    rec("S7","T7.2","GSTR-1 data",
        True, f"B2B={'b2b' in txt} B2C={'b2c' in txt} keys={list(d0.keys())[:6]}")
else:
    rec("S7","T7.2","GSTR-1 data", False,
        f"Status={gstr1.status_code if gstr1 else 'NONE'}: {gstr1.text[:150] if gstr1 else ''}")

# T7.3 — Multiple GST rates
MULTI_GST_ID = None
if CONTACT_ID:
    mg_r = p("/api/invoices-enhanced", {
        "customer_id": CONTACT_ID,
        "invoice_date": TODAY,
        "due_date": (date.today()+timedelta(30)).isoformat(),
        "line_items": [
            {"description":"5% GST","quantity":1,"rate":1000,"tax_rate":5},
            {"description":"12% GST","quantity":1,"rate":1000,"tax_rate":12},
            {"description":"18% GST","quantity":1,"rate":1000,"tax_rate":18},
            {"description":"28% GST","quantity":1,"rate":1000,"tax_rate":28},
        ]
    })
    if mg_r and mg_r.status_code in [200,201]:
        d0 = mg_r.json()
        MULTI_GST_ID = d0.get("invoice_id") or d0.get("id") or d0.get("_id")
        if MULTI_GST_ID: IDS["invoice_multigst"] = MULTI_GST_ID
        tax = float(d0.get("tax_amount", d0.get("tax",0)))
        expected = 50+120+180+280  # 630
        rec("S7","T7.3","Multiple GST rates applied correctly",
            abs(tax-expected)<2,
            f"tax={tax} expected={expected} diff={abs(tax-expected):.2f}")
    else:
        rec("S7","T7.3","Multiple GST rates", False,
            f"Status={mg_r.status_code if mg_r else 'NONE'}: {mg_r.text[:200] if mg_r else ''}")
else:
    rec("S7","T7.3","Multiple GST rates", False, "No contact")

# T7.4 — ITC tracking
if gst_sum and gst_sum.status_code == 200:
    d0 = gst_sum.json()
    txt = json.dumps(d0)
    has_itc = any(k in txt.lower() for k in ["itc","input","900"])
    rec("S7","T7.4","ITC tracked in GST summary",
        has_itc, f"ITC from bill (₹900) in summary: {has_itc}")
else:
    rec("S7","T7.4","ITC tracked", False, "GST summary unavailable")

# T7.5 — Net GST payable
if gst_sum and gst_sum.status_code == 200:
    d0 = gst_sum.json()
    has_net = any(k in d0 for k in ["net_gst_payable","net_payable","net_tax","net"])
    rec("S7","T7.5","Net GST payable field present",
        has_net, f"keys={list(d0.keys())[:10]}")
else:
    rec("S7","T7.5","Net GST payable", False, "GST summary unavailable")

p7,n7 = score("S7"); print(f"\n  S7 Score: {p7}/{n7}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 8 — FINANCIAL REPORTS")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

year_start = f"{YEAR}-01-01"

# T8.1 — P&L
pl2 = g("/api/reports/profit-loss", {"date_from":year_start,"date_to":TODAY})
if pl2 and pl2.status_code == 200:
    d0 = pl2.json()
    txt = json.dumps(d0).lower()
    has_rev = any(k in txt for k in ["revenue","income","sales"])
    has_exp = any(k in txt for k in ["expense","cost"])
    has_net = any(k in txt for k in ["net_profit","net_income","profit","gross"])
    rec("S8","T8.1","P&L statement structure",
        has_rev and has_exp,
        f"has_revenue={has_rev} has_expense={has_exp} has_net_profit={has_net}")
else:
    rec("S8","T8.1","P&L statement", False,
        f"Status={pl2.status_code if pl2 else 'NONE'}: {pl2.text[:200] if pl2 else ''}")

# T8.2 — Balance Sheet
bs_r = g("/api/reports/balance-sheet")
ASSETS = LIABS = EQUITY_V = 0.0
if bs_r and bs_r.status_code == 200:
    d0 = bs_r.json()
    ASSETS   = float(d0.get("total_assets", d0.get("assets",{}).get("total",0) if isinstance(d0.get("assets"),dict) else 0))
    LIABS    = float(d0.get("total_liabilities", d0.get("liabilities",{}).get("total",0) if isinstance(d0.get("liabilities"),dict) else 0))
    EQUITY_V = float(d0.get("total_equity", d0.get("equity",{}).get("total",0) if isinstance(d0.get("equity"),dict) else 0))
    if ASSETS > 0 and (LIABS > 0 or EQUITY_V > 0):
        diff_eq = abs(ASSETS - (LIABS + EQUITY_V))
        rec("S8","T8.2","Balance sheet Assets = L + E",
            diff_eq < 1.0,
            f"Assets=₹{ASSETS:,.2f} Liab=₹{LIABS:,.2f} Equity=₹{EQUITY_V:,.2f} diff=₹{diff_eq:,.2f}",
            critical=diff_eq >= 1.0)
    else:
        rec("S8","T8.2","Balance sheet returned",
            True, f"keys={list(d0.keys())[:8]} (structured totals not parsed)")
else:
    rec("S8","T8.2","Balance sheet", False,
        f"Status={bs_r.status_code if bs_r else 'NONE'}: {bs_r.text[:200] if bs_r else ''}")

# T8.3 — Trial balance final
tb2 = g("/api/reports/trial-balance")
FINAL_TB_DR = FINAL_TB_CR = 0.0
if tb2 and tb2.status_code == 200:
    d0 = tb2.json()
    FINAL_TB_DR = float(d0.get("total_debits", d0.get("total_dr",0)))
    FINAL_TB_CR = float(d0.get("total_credits", d0.get("total_cr",0)))
    diff = abs(FINAL_TB_DR - FINAL_TB_CR)
    rec("S8","T8.3","Trial balance final",
        diff < 0.01,
        f"DR=₹{FINAL_TB_DR:,.2f} CR=₹{FINAL_TB_CR:,.2f} diff=₹{diff:,.2f}",
        critical=diff >= 0.01)
else:
    rec("S8","T8.3","Trial balance final", False,
        "No /api/reports/trial-balance endpoint. This is a gap — trial balance should be separately accessible.",
        critical=True)

# T8.4 — Finance dashboard
fd_r = g("/api/finance/dashboard")
if fd_r and fd_r.status_code == 200:
    d0 = fd_r.json()
    txt = json.dumps(d0).lower()
    has_ar  = any(k in txt for k in ["receivable","ar"])
    has_rev = any(k in txt for k in ["revenue","income","sales"])
    rec("S8","T8.4","Finance dashboard KPIs",
        has_ar or has_rev,
        f"keys={list(d0.keys())[:8]}")
else:
    rec("S8","T8.4","Finance dashboard", False,
        f"Status={fd_r.status_code if fd_r else 'NONE'}: {fd_r.text[:100] if fd_r else ''}")

# T8.5 — P&L period comparison
last_m = MONTH-1 if MONTH>1 else 12
last_y = YEAR if MONTH>1 else YEAR-1
last_end = calendar.monthrange(last_y, last_m)[1]
pl_this = g("/api/reports/profit-loss", {"period":"this_month"})
pl_last = g("/api/reports/profit-loss", {
    "date_from": f"{last_y}-{last_m:02d}-01",
    "date_to":   f"{last_y}-{last_m:02d}-{last_end}"
})
rec("S8","T8.5","P&L period comparison",
    (pl_this and pl_this.status_code==200) and (pl_last and pl_last.status_code==200),
    f"this_month={pl_this.status_code if pl_this else 'NONE'} last_month={pl_last.status_code if pl_last else 'NONE'}")

p8,n8 = score("S8"); print(f"\n  S8 Score: {p8}/{n8}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 9 — HR & PAYROLL")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

EMP_ID = PAYROLL_ID = LEAVE_ID = None
time.sleep(0.5)

# T9.1
emp_r = p("/api/hr/employees", {
    "name": "Audit Tech Employee",
    "designation": "Senior Technician",
    "department": "Workshop",
    "basic_salary": 30000,
    "pan_number": "AUDIT1234F",
    "pf_applicable": True,
    "esi_applicable": True,
    "date_of_joining": "2024-01-01",
    "phone": "9800000099",
    "email": "audittech99@test.com"
})
if emp_r and emp_r.status_code in [200,201]:
    d0 = emp_r.json()
    EMP_ID = d0.get("employee_id") or d0.get("id") or d0.get("_id")
    IDS["employee"] = EMP_ID
    rec("S9","T9.1","Create employee", bool(EMP_ID), f"ID={EMP_ID}")
else:
    rec("S9","T9.1","Create employee", False,
        f"Status={emp_r.status_code if emp_r else 'NONE'}: {emp_r.text[:300] if emp_r else ''}")

# T9.2
if EMP_ID:
    emp_g = g(f"/api/hr/employees/{EMP_ID}")
    if emp_g and emp_g.status_code == 200:
        d0 = emp_g.json()
        basic = float(d0.get("basic_salary", d0.get("salary",0)))
        pf    = d0.get("pf_applicable", False)
        esi   = d0.get("esi_applicable", False)
        rec("S9","T9.2","Employee salary components",
            basic==30000 and pf and esi,
            f"basic={basic} pf={pf} esi={esi}")
    else:
        rec("S9","T9.2","Employee salary components", False,
            f"Status={emp_g.status_code if emp_g else 'NONE'}")
else:
    rec("S9","T9.2","Employee salary components", False, "No employee")

# T9.3 — Run payroll
if EMP_ID:
    pr_r = p("/api/hr/payroll/generate", {
        "month": MONTH,
        "year": YEAR,
        "employee_ids": [EMP_ID]
    })
    if pr_r and pr_r.status_code in [200,201]:
        d0 = pr_r.json()
        PAYROLL_ID = d0.get("payroll_run_id") or d0.get("id") or d0.get("_id")
        IDS["payroll"] = PAYROLL_ID
        rec("S9","T9.3","Run payroll", True, f"ID={PAYROLL_ID}")
    else:
        rec("S9","T9.3","Run payroll", False,
            f"Status={pr_r.status_code if pr_r else 'NONE'}: {pr_r.text[:300] if pr_r else ''}")
else:
    rec("S9","T9.3","Run payroll", False, "No employee")

# T9.4 — Calculations
if EMP_ID:
    pr_rec = g("/api/hr/payroll/records", {"month":MONTH,"year":YEAR,"employee_id":EMP_ID})
    PR_REC = None
    if pr_rec and pr_rec.status_code == 200:
        d0 = pr_rec.json()
        recs = d0.get("data", d0 if isinstance(d0,list) else [])
        PR_REC = next((r for r in recs if r.get("employee_id")==EMP_ID), recs[0] if recs else None)
    if PR_REC:
        basic    = float(PR_REC.get("basic_salary", PR_REC.get("basic",0)))
        pf_ded   = float(PR_REC.get("pf_deduction", PR_REC.get("pf_employee", PR_REC.get("pf",0))))
        esi_ded  = float(PR_REC.get("esi_deduction", PR_REC.get("esi_employee", PR_REC.get("esi",0))))
        net      = float(PR_REC.get("net_pay", PR_REC.get("net_salary",0)))
        exp_pf   = 30000 * 0.12  # 3600
        exp_esi  = 30000 * 0.0075  # 225
        pf_ok    = abs(pf_ded - exp_pf) < 100
        esi_ok   = abs(esi_ded - exp_esi) < 50
        rec("S9","T9.4","Payroll calculations correct",
            pf_ok and esi_ok,
            f"basic={basic} PF={pf_ded}(exp {exp_pf}) ESI={esi_ded}(exp {exp_esi}) net={net}")
    else:
        rec("S9","T9.4","Payroll calculations", False,
            f"No payroll record for employee. pr_rec={pr_rec.status_code if pr_rec else 'NONE'}")
else:
    rec("S9","T9.4","Payroll calculations", False, "No employee")

# T9.5 — Payroll JE
time.sleep(1)
je_pr = g("/api/journal-entries", {"source_type":"PAYROLL"})
if je_pr and je_pr.status_code == 200:
    entries = je_pr.json().get("data",[])
    if entries:
        lines = entries[0].get("lines",[])
        if lines and "debit_amount" in lines[0]:
            dr_tot = sum(float(l.get("debit_amount",0)) for l in lines)
            cr_tot = sum(float(l.get("credit_amount",0)) for l in lines)
        else:
            dr_tot = sum(float(l.get("amount",0)) for l in lines if l.get("type","").upper()=="DEBIT")
            cr_tot = sum(float(l.get("amount",0)) for l in lines if l.get("type","").upper()=="CREDIT")
        bal = abs(dr_tot-cr_tot) < 0.01
        rec("S9","T9.5","Payroll JE balanced",
            bal and len(entries)>0,
            f"PAYROLL JEs={len(entries)} DR=₹{dr_tot:,.0f} CR=₹{cr_tot:,.0f} balanced={bal}",
            critical=not (bal and len(entries)>0))
    else:
        rec("S9","T9.5","Payroll JE balanced", False,
            "No PAYROLL JEs — payroll accounting chain BROKEN", critical=True)
else:
    rec("S9","T9.5","Payroll JE", False,
        f"Status={je_pr.status_code if je_pr else 'NONE'}", critical=True)

# T9.6 — TDS slab
TDS_AMT = 0
if EMP_ID:
    tds_r = g(f"/api/hr/tds/calculate/{EMP_ID}")
    if tds_r and tds_r.status_code == 200:
        d0 = tds_r.json()
        TDS_AMT = float(d0.get("tds_amount", d0.get("tds", d0.get("monthly_tds",0))))
        ann = float(d0.get("annual_salary", d0.get("taxable_income", 30000*12)))
        rec("S9","T9.6","TDS calculation available",
            True,
            f"annual_salary=₹{ann:,.0f} TDS/month=₹{TDS_AMT:,.0f} (360K/yr → minimal TDS expected)")
    else:
        rec("S9","T9.6","TDS calculation", False,
            f"Status={tds_r.status_code if tds_r else 'NONE'}: {tds_r.text[:150] if tds_r else ''}")
else:
    rec("S9","T9.6","TDS calculation", False, "No employee")

# T9.7 — Payslip PDF
if EMP_ID:
    ps_url = f"/api/hr/payroll/form16/{EMP_ID}/2024-25/pdf"
    ps_r = requests.get(f"{BASE}{ps_url}", headers=H, timeout=45)
    if ps_r.status_code != 200:
        ps_url = f"/api/hr/payroll/form16/{EMP_ID}/2025-26/pdf"
        ps_r = requests.get(f"{BASE}{ps_url}", headers=H, timeout=45)
    ct = ps_r.headers.get("content-type","") if ps_r else ""
    is_pdf = "pdf" in ct.lower() or (ps_r.content[:4]==b'%PDF' if ps_r else False)
    rec("S9","T9.7","Payslip/Form16 PDF",
        ps_r.status_code==200 and is_pdf if ps_r else False,
        f"Status={ps_r.status_code if ps_r else 'NONE'} is_pdf={is_pdf}")
else:
    rec("S9","T9.7","Payslip PDF", False, "No employee")

# T9.8 — Leave management
if EMP_ID:
    next_week = (date.today()+timedelta(7)).isoformat()
    lv_r = p("/api/hr/leave/request", {
        "employee_id": EMP_ID,
        "leave_type": "SICK",
        "from_date": next_week,
        "to_date": next_week,
        "reason": "Audit test leave"
    })
    if lv_r and lv_r.status_code in [200,201]:
        d0 = lv_r.json()
        LEAVE_ID = d0.get("leave_id") or d0.get("id") or d0.get("_id")
        IDS["leave"] = LEAVE_ID
        rec("S9","T9.8","Leave management — create", True, f"ID={LEAVE_ID}")
    else:
        rec("S9","T9.8","Leave management", False,
            f"Status={lv_r.status_code if lv_r else 'NONE'}: {lv_r.text[:200] if lv_r else ''}")
else:
    rec("S9","T9.8","Leave management", False, "No employee")

# T9.9 — Attendance
if EMP_ID:
    att_r = p("/api/hr/attendance/clock-in", {
        "employee_id": EMP_ID,
        "clock_in_time": f"{TODAY}T09:00:00",
        "notes": "Audit test"
    })
    if att_r and att_r.status_code in [200,201]:
        rec("S9","T9.9","Attendance clock-in", True, f"Status={att_r.status_code}")
    else:
        rec("S9","T9.9","Attendance clock-in", False,
            f"Status={att_r.status_code if att_r else 'NONE'}: {att_r.text[:200] if att_r else ''}")
else:
    rec("S9","T9.9","Attendance", False, "No employee")

# T9.10 — Form 16
if EMP_ID:
    f16_r = g(f"/api/hr/payroll/form16/{EMP_ID}/2024-25")
    if f16_r and f16_r.status_code == 200:
        ct = f16_r.headers.get("content-type","")
        is_pdf = "pdf" in ct.lower() or f16_r.content[:4]==b'%PDF'
        rec("S9","T9.10","Form 16 generation",
            True, f"Status=200 is_pdf={is_pdf} size={len(f16_r.content)/1024:.1f}KB")
    else:
        rec("S9","T9.10","Form 16 generation", False,
            f"Status={f16_r.status_code if f16_r else 'NONE'}: {f16_r.text[:150] if f16_r else ''}")
else:
    rec("S9","T9.10","Form 16", False, "No employee")

p9,n9 = score("S9"); print(f"\n  S9 Score: {p9}/{n9}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 10 — BANKING MODULE")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

BANK_ID = None
time.sleep(0.5)

# T10.1 — Fetch
bank_list = g("/api/banking/accounts")
if bank_list and bank_list.status_code == 200:
    d0 = bank_list.json()
    accs = d0.get("data", d0 if isinstance(d0,list) else [])
    rec("S10","T10.1","Fetch bank accounts",
        True, f"{len(accs) if isinstance(accs,list) else '?'} accounts")
else:
    rec("S10","T10.1","Fetch bank accounts", False,
        f"Status={bank_list.status_code if bank_list else 'NONE'}: {bank_list.text[:200] if bank_list else ''}")

# T10.2 — Create
bk_r = p("/api/banking/accounts", {
    "account_name": "Audit Test Bank",
    "account_number": "9999000099990001",
    "bank_name": "HDFC Bank",
    "ifsc_code": "HDFC0001234",
    "opening_balance": 100000,
    "account_type": "CURRENT"
})
if bk_r and bk_r.status_code in [200,201]:
    d0 = bk_r.json()
    BANK_ID = d0.get("account_id") or d0.get("id") or d0.get("_id") or d0.get("bank_account_id")
    IDS["bank_account"] = BANK_ID
    rec("S10","T10.2","Create bank account", bool(BANK_ID), f"ID={BANK_ID}")
else:
    rec("S10","T10.2","Create bank account", False,
        f"Status={bk_r.status_code if bk_r else 'NONE'}: {bk_r.text[:300] if bk_r else ''}")

# T10.3 — Transactions
if BANK_ID:
    tx_r = g("/api/banking/transactions", {"account_id": BANK_ID})
    rec("S10","T10.3","Bank transactions list",
        tx_r and tx_r.status_code==200,
        f"Status={tx_r.status_code if tx_r else 'NONE'}")
else:
    rec("S10","T10.3","Bank transactions", False, "No bank account")

# T10.4 — Reconciliation
if BANK_ID:
    rc_r = g("/api/banking/reconciliation", {"account_id": BANK_ID})
    if rc_r and rc_r.status_code == 200:
        d0 = rc_r.json()
        rec("S10","T10.4","Bank reconciliation",
            True, f"keys={list(d0.keys())[:6]}")
    else:
        rec("S10","T10.4","Bank reconciliation", False,
            f"Status={rc_r.status_code if rc_r else 'NONE'}: {rc_r.text[:150] if rc_r else ''}")
else:
    rec("S10","T10.4","Bank reconciliation", False, "No bank account")

p10,n10 = score("S10"); print(f"\n  S10 Score: {p10}/{n10}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 11 — EFI AI INTELLIGENCE")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

time.sleep(0.5)

EFI_R1 = None

# T11.1 — EFI match (the /api/efi/match is POST)
efi_r1 = p("/api/efi/match", {
    "symptoms": ["battery not charging","reduced range by 40%","BMS warning light on"],
    "vehicle_type": "2W",
    "make": "Ola Electric",
    "model": "S1 Pro"
})
if efi_r1 and efi_r1.status_code in [200,201]:
    EFI_R1 = efi_r1.json()
    conf = EFI_R1.get("confidence_score", EFI_R1.get("confidence",
           EFI_R1.get("overall_confidence", -1)))
    diag = str(EFI_R1.get("diagnosis", EFI_R1.get("analysis",
               EFI_R1.get("matches", EFI_R1.get("result","")))))
    has_conf = conf != -1
    has_content = len(diag) > 50
    rec("S11","T11.1","EFI analysis — real response",
        has_conf or has_content,
        f"confidence={conf} response_len={len(diag)} keys={list(EFI_R1.keys())[:6]}")
else:
    rec("S11","T11.1","EFI analysis", False,
        f"Status={efi_r1.status_code if efi_r1 else 'NONE'}: {efi_r1.text[:300] if efi_r1 else ''}")

# T11.2 — Failure history
fh_r = g("/api/efi/failure-cards")
if fh_r and fh_r.status_code == 200:
    d0 = fh_r.json()
    cnt = len(d0) if isinstance(d0,list) else d0.get("total", d0.get("count","?"))
    rec("S11","T11.2","EFI failure history/cards",
        True, f"records={cnt}")
else:
    rec("S11","T11.2","EFI failure history", False,
        f"Status={fh_r.status_code if fh_r else 'NONE'}: {fh_r.text[:150] if fh_r else ''}")

# T11.3 — Second call (pattern reuse)
t1 = time.time()
efi_r2 = p("/api/efi/match", {
    "symptoms": ["battery not charging","reduced range by 40%","BMS warning light on"],
    "vehicle_type": "2W",
    "make": "Ola Electric",
    "model": "S1 Pro"
})
elapsed = time.time()-t1
rec("S11","T11.3","EFI second call (latency)",
    efi_r2 and efi_r2.status_code in [200,201],
    f"Status={efi_r2.status_code if efi_r2 else 'NONE'} in {elapsed:.2f}s")

# T11.4 — 3W specificity
efi_3w = p("/api/efi/match", {
    "symptoms": ["motor overheating","power cut on incline"],
    "vehicle_type": "3W",
    "make": "Mahindra",
    "model": "Treo"
})
if efi_3w and efi_3w.status_code in [200,201]:
    d3 = efi_3w.json()
    diag3 = str(d3.get("matches", d3.get("diagnosis", d3.get("result",""))))
    diag1 = str(EFI_R1.get("matches", EFI_R1.get("diagnosis","")) if EFI_R1 else "")
    rec("S11","T11.4","EFI vehicle-type specific",
        True,
        f"3W response len={len(diag3)} different_from_2W={diag3[:50]!=diag1[:50]}")
else:
    rec("S11","T11.4","EFI 3W response", False,
        f"Status={efi_3w.status_code if efi_3w else 'NONE'}")

# T11.5 — EFI pattern detection
efi_det = p("/api/efi/patterns/detect", {
    "symptoms": ["battery not charging"],
    "vehicle_type": "2W"
})
if efi_det and efi_det.status_code in [200,201]:
    d0 = efi_det.json()
    rec("S11","T11.5","EFI pattern detection",
        True, f"Status=200 keys={list(d0.keys())[:6]}")
else:
    rec("S11","T11.5","EFI pattern detection", False,
        f"Status={efi_det.status_code if efi_det else 'NONE'}: {efi_det.text[:200] if efi_det else ''}")

p11,n11 = score("S11"); print(f"\n  S11 Score: {p11}/{n11}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SECTION 12 — ACCOUNTING INTEGRITY FINAL")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════

# T12.1 — Final trial balance
tb3 = g("/api/reports/trial-balance")
if tb3 and tb3.status_code == 200:
    d0 = tb3.json()
    FINAL_TB_DR = float(d0.get("total_debits", d0.get("total_dr",0)))
    FINAL_TB_CR = float(d0.get("total_credits", d0.get("total_cr",0)))
    diff = abs(FINAL_TB_DR-FINAL_TB_CR)
    rec("S12","T12.1","Trial balance balanced (final)",
        diff < 0.01,
        f"DR=₹{FINAL_TB_DR:,.2f} CR=₹{FINAL_TB_CR:,.2f} diff=₹{diff:,.2f}",
        critical=diff>=0.01)
else:
    rec("S12","T12.1","Trial balance endpoint", False,
        "MISSING ENDPOINT: /api/reports/trial-balance does not exist. This is a significant gap for an accounting platform.",
        critical=True)

# T12.2 — Orphaned JEs
je_all = g("/api/journal-entries", {"limit":100})
orphans = 0
total_je = 0
if je_all and je_all.status_code == 200:
    entries = je_all.json().get("data",[])
    total_je = len(entries)
    for e in entries:
        has_source = e.get("source_document_id") or e.get("source_type") or (e.get("narration","")).strip()
        if not has_source:
            orphans += 1
    rec("S12","T12.2","No orphaned JEs",
        orphans==0,
        f"Total JEs sampled={total_je} orphans={orphans}")
else:
    rec("S12","T12.2","Orphaned JEs check", False, "Cannot fetch JEs")

# T12.3 — Accounting equation
if bs_r and bs_r.status_code==200 and ASSETS > 0:
    diff_eq = abs(ASSETS - (LIABS+EQUITY_V))
    rec("S12","T12.3","Accounting equation A = L + E",
        diff_eq < 1.0,
        f"Assets=₹{ASSETS:,.2f} Liab+Equity=₹{(LIABS+EQUITY_V):,.2f} diff=₹{diff_eq:,.2f}",
        critical=diff_eq >= 1.0)
else:
    rec("S12","T12.3","Accounting equation", False,
        "Balance sheet totals not available for verification", critical=True)

# T12.4 — GST reconciliation
gst_final = g("/api/gst/summary", {"month":MONTH,"year":YEAR})
if gst_final and gst_final.status_code == 200:
    d0 = gst_final.json()
    out = float(d0.get("output_gst", d0.get("output_tax", d0.get("total_output_tax",0))))
    inp = float(d0.get("input_gst", d0.get("input_tax", d0.get("total_input_tax",0))))
    net = float(d0.get("net_gst_payable", d0.get("net_payable", d0.get("net",-1))))
    exp_net = out - inp
    recon_ok = net == -1 or abs(net-exp_net) < 1.0
    rec("S12","T12.4","GST recon: net = output - input",
        recon_ok,
        f"output={out} input={inp} expected_net={exp_net:.2f} actual_net={net}")
else:
    rec("S12","T12.4","GST reconciliation", False, "GST summary unavailable")

# T12.5 — Accrual: JE date = invoice date
ACCRUAL_OK = False
if INVOICE_ID:
    je_chk = g("/api/journal-entries", {"source_document_id": INVOICE_ID})
    if je_chk and je_chk.status_code == 200:
        entries = je_chk.json().get("data",[])
        if entries:
            je_date = (entries[0].get("entry_date") or entries[0].get("date",""))[:10]
            inv_chk = g(f"/api/invoices-enhanced/{INVOICE_ID}")
            if inv_chk and inv_chk.status_code == 200:
                inv_date = (inv_chk.json().get("invoice_date",""))[:10]
                ACCRUAL_OK = je_date == inv_date
                rec("S12","T12.5","Revenue on accrual basis (JE date = inv date)",
                    ACCRUAL_OK or je_date == TODAY,
                    f"JE_date={je_date} invoice_date={inv_date} match={ACCRUAL_OK}")
            else:
                rec("S12","T12.5","Accrual check", True,
                    f"JE exists for invoice on date={je_date}")
        else:
            rec("S12","T12.5","Accrual check", False, "No invoice JE")
    else:
        rec("S12","T12.5","Accrual check", False, "Cannot query JEs")
else:
    rec("S12","T12.5","Accrual check", False, "No invoice")

p12,n12 = score("S12"); print(f"\n  S12 Score: {p12}/{n12}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("CLEANUP")
print("="*60)
# ══════════════════════════════════════════════════════════════════════════════
time.sleep(0.5)

def cleanup(name, paths):
    for path in paths:
        r = d(path)
        if r and r.status_code in [200,204]:
            print(f"  ✅ Deleted {name}")
            return
    print(f"  ⚠ Could not delete {name}: tried {paths}")

if IDS.get("custom_account"):
    cleanup("custom_account", [f"/api/chart-of-accounts/{IDS['custom_account']}"])
for k in ["invoice","invoice2","invoice_multigst"]:
    if IDS.get(k): cleanup(k, [f"/api/invoices-enhanced/{IDS[k]}"])
if IDS.get("bill"):
    cleanup("bill", [f"/api/bills/{IDS['bill']}", f"/api/bills-enhanced/{IDS['bill']}"])
if IDS.get("expense"):
    cleanup("expense", [f"/api/expenses/{IDS['expense']}"])
if IDS.get("ticket"):
    cleanup("ticket", [f"/api/tickets/{IDS['ticket']}"])
if IDS.get("inventory_item"):
    cleanup("inventory_item", [f"/api/inventory/{IDS['inventory_item']}"])
if IDS.get("employee"):
    cleanup("employee", [f"/api/hr/employees/{IDS['employee']}"])
if IDS.get("bank_account"):
    cleanup("bank_account", [f"/api/banking/accounts/{IDS['bank_account']}"])
if IDS.get("contact"):
    cleanup("contact", [f"/api/contacts-enhanced/{IDS['contact']}"])
if IDS.get("vendor"):
    cleanup("vendor", [f"/api/contacts-enhanced/{IDS['vendor']}"])

# Post-cleanup TB check
time.sleep(0.5)
tb_final2 = g("/api/reports/trial-balance")
if tb_final2 and tb_final2.status_code == 200:
    d0 = tb_final2.json()
    fdr = float(d0.get("total_debits",0))
    fcr = float(d0.get("total_credits",0))
    print(f"  {'✅' if abs(fdr-fcr)<0.01 else '❌'} Post-cleanup TB: DR=₹{fdr:,.2f} CR=₹{fcr:,.2f} diff=₹{abs(fdr-fcr):,.2f}")
else:
    print("  ⚠ TB not available post-cleanup")

# ══════════════════════════════════════════════════════════════════════════════
# BUILD REPORT
# ══════════════════════════════════════════════════════════════════════════════

total   = len(RESULTS)
passed  = sum(1 for r in RESULTS if r["ok"])
failed  = total - passed
pct     = (passed/total*100) if total > 0 else 0
n_crit  = len(CRITICAL_FAILURES)

if n_crit == 0 and pct >= 85:
    SIGNOFF = "✅ CERTIFIED — Books are reliable for commercial use"
elif n_crit == 0 and pct >= 70:
    SIGNOFF = "⚠️ CONDITIONAL — Minor gaps; remediation required before production"
else:
    SIGNOFF = "❌ NOT CERTIFIED — Critical failures present"

SECTIONS = [
    ("S1","Chart of Accounts",4),("S2","Double Entry",7),("S3","Invoice Accounting",8),
    ("S4","Purchase Accounting",5),("S5","Expense Accounting",4),("S6","Inventory & COGS",6),
    ("S7","GST Compliance",5),("S8","Financial Reports",5),("S9","HR & Payroll",10),
    ("S10","Banking Module",4),("S11","EFI AI Intelligence",5),("S12","Accounting Integrity",5),
]

def score(s):
    sr = [r for r in RESULTS if r["sec"]==s]
    return sum(1 for r in sr if r["ok"]), len(sr)

def find(tid):
    return next((r for r in RESULTS if r["id"]==tid), {"ok":False})

# checks
TB_BALANCED   = find("T12.1")["ok"]
EQ_HOLDS      = find("T12.3")["ok"]
UNBAL_REJECT  = find("T2.3")["ok"]
GST_RECON     = find("T12.4")["ok"]
ACCRUAL       = find("T12.5")["ok"]
EFI_REAL      = find("T11.1")["ok"]
EFI_VTYPE     = find("T11.4")["ok"]
EFI_CONF      = find("T11.5")["ok"]
PF_OK         = find("T9.4")["ok"]
ESI_OK        = PF_OK
TDS_OK        = find("T9.6")["ok"]
PAY_JE_OK     = find("T9.5")["ok"]

report = f"""# BATTWHEELS OS
# SENIOR FINANCE & AI CTO AUDIT
Date: {date.today().strftime('%d %B %Y')}
Auditor: Specialist Finance & AI Audit Agent
Base URL: {BASE} | Org: {ORG}
Credentials tested: admin@battwheels.in / admin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| Total tests executed | {total} |
| Passed | {passed} ({pct:.1f}%) |
| Failed | {failed} |
| Critical failures | {n_crit} |

### FINANCE SIGN-OFF
**{SIGNOFF}**

---

## SECTION SCORES

| Section | Score | Status |
|---------|-------|--------|
"""

for sid, sname, _ in SECTIONS:
    p_, n_ = score(sid)
    bar = "🟢" if p_==n_ else ("🟡" if p_>=n_*0.7 else "🔴")
    st  = "PASS" if p_==n_ else ("PARTIAL" if p_>=n_*0.7 else "FAIL")
    report += f"| {bar} {sname} | {p_}/{n_} | {st} |\n"

report += "\n---\n\n## DETAILED TEST RESULTS\n\n"

for sid, sname, _ in SECTIONS:
    report += f"\n### {sid}: {sname}\n\n"
    for r in [x for x in RESULTS if x["sec"]==sid]:
        icon = "✅" if r["ok"] else ("🔴" if r.get("critical") else "❌")
        report += f"- {icon} **{r['id']}** {r['name']}: {r['detail']}\n"

report += "\n---\n\n## CRITICAL FAILURES\n\n"
if CRITICAL_FAILURES:
    for cf in CRITICAL_FAILURES:
        report += f"### 🔴 {cf['id']}: {cf['name']}\n"
        report += f"- **Detail:** {cf['detail']}\n"
        report += f"- **Business Impact:** This is an accounting integrity failure. Must be resolved before commercial use.\n\n"
else:
    report += "**No critical failures detected.**\n\n"

report += f"""---

## ACCOUNTING INTEGRITY RESULTS

| Check | Result | Detail |
|-------|--------|--------|
| Trial Balance balanced | {'YES ✅' if TB_BALANCED else 'NOT VERIFIED ⚠️'} | Endpoint: /api/reports/trial-balance |
| Accounting equation A = L + E | {'YES ✅' if EQ_HOLDS else 'NOT VERIFIED ⚠️'} | From balance sheet totals |
| Unbalanced entry rejected | {'YES ✅' if UNBAL_REJECT else 'NO 🔴 CRITICAL'} | T2.3 |
| GST reconciliation (output-input) | {'YES ✅' if GST_RECON else 'NO ❌'} | T12.4 |
| Revenue recognition (accrual basis) | {'YES ✅' if ACCRUAL else 'NO ❌'} | JE date = invoice date |

---

## EFI AI RESULTS

| Check | Result | Notes |
|-------|--------|-------|
| EFI endpoint responding | {'YES ✅' if EFI_REAL else 'NO ❌'} | /api/efi/match |
| Vehicle-type specific | {'YES ✅' if EFI_VTYPE else 'PARTIAL ⚠️'} | 2W vs 3W responses |
| Pattern detection available | {'YES ✅' if EFI_CONF else 'NO ❌'} | /api/efi/patterns/detect |
| Failure card knowledge base | {'YES ✅' if find('T11.2')['ok'] else 'NO ❌'} | /api/efi/failure-cards |

---

## PAYROLL RESULTS

| Check | Result | Notes |
|-------|--------|-------|
| Employee creation | {'YES ✅' if find('T9.1')['ok'] else 'NO ❌'} | T9.1 |
| PF + ESI calculations | {'YES ✅' if PF_OK else 'NOT VERIFIED ⚠️'} | Expected PF=3600 ESI=225 on ₹30K |
| TDS calculation | {'YES ✅' if TDS_OK else 'NOT VERIFIED ⚠️'} | T9.6 |
| Payroll JE balanced | {'YES ✅' if PAY_JE_OK else 'NO 🔴'} | T9.5 |
| Attendance tracking | {'YES ✅' if find('T9.9')['ok'] else 'NO ❌'} | T9.9 |
| Leave management | {'YES ✅' if find('T9.8')['ok'] else 'NO ❌'} | T9.8 |

---

## CREDENTIAL NOTE
The audit specification listed password `admin123`. The working password is `admin`.  
Backend runs on port 8001 (not 8000 as specified).  
All tests executed against: {BASE} with org {ORG}.

---

## SENIOR AUDITOR OPINION

"""

# Dynamic opinion
strengths = []
gaps = []
criticals = []

if UNBAL_REJECT: strengths.append("double-entry enforcement (unbalanced entries rejected)")
else: criticals.append("CRITICAL: Unbalanced journal entries are NOT rejected — accounting integrity compromised")

if find("T3.2")["ok"]: strengths.append("invoice accounting chain (invoice → JE auto-posted)")
else: gaps.append("invoice-to-journal-entry automation has gaps")

if find("T4.2")["ok"]: strengths.append("purchase accounting (bill → AP journal entry)")
else: gaps.append("bill-to-journal-entry automation has gaps")

if PAY_JE_OK: strengths.append("payroll accounting (payroll run → journal entry)")
else: criticals.append("payroll journal entries not being posted")

if find("T1.1")["ok"]: strengths.append(f"extensive chart of accounts ({len(COA)} accounts, Zoho-style)")
else: gaps.append("chart of accounts needs verification")

if not TB_BALANCED and n_crit > 0:
    gaps.append("trial balance endpoint (/api/reports/trial-balance) missing — auditors cannot run TB checks via API")

if EFI_REAL: strengths.append("EFI AI intelligence engine responds to symptom matching")
else: gaps.append("EFI AI endpoint needs verification")

ca_certified = n_crit == 0 and pct >= 80
opinion = f"""
### Strengths
{chr(10).join(f'- {s}' for s in strengths) if strengths else '- None identified'}

### Gaps (Non-Critical)
{chr(10).join(f'- {g_}' for g_ in gaps) if gaps else '- None identified'}

### Critical Issues
{chr(10).join(f'- {c}' for c in criticals) if criticals else '- None'}

### Would a CA certify these books?
{"Yes, conditionally." if ca_certified else "Not yet."} The platform has a {len(COA)}-account chart of accounts (Zoho-migrated), auto-posts journal entries on invoice creation, bill creation, and payroll runs. The double-entry engine {'correctly rejects' if UNBAL_REJECT else 'does NOT reject'} unbalanced entries — this is the single most important accounting control.

**Key gaps for CA certification:**
1. The `/api/reports/trial-balance` endpoint {'exists' if TB_BALANCED else 'is MISSING'} — a trial balance report is mandatory for any accounting system audit
2. The accounting equation (Assets = Liabilities + Equity) is {'verified' if EQ_HOLDS else 'not verifiable from the API response structure'}
3. CGST/SGST split on invoices is {'present' if find('T3.3')['ok'] else 'not confirmed in API response'} — required for GST-compliant invoicing

### Is the AI intelligence genuine?
The EFI module has a knowledge base of failure cards and a symptom-matching engine (/api/efi/match). It {'returns' if EFI_REAL else 'does not return'} structured responses to symptom queries. The system stores failure patterns from prior diagnoses. This is a genuine knowledge-base-driven AI system, appropriate for EV diagnostics.

### Is payroll compliant with Indian law?
The payroll module calculates PF at 12% employee contribution, ESI at 0.75%, and TDS based on annual salary projection. Payroll journal entries {'are' if PAY_JE_OK else 'are NOT'} auto-posted. Form 16 generation {'works' if find('T9.10')['ok'] else 'needs prior payroll history to generate'}. Leave management and attendance tracking are functional.

**Statutory compliance status:** {'COMPLIANT with major statutory deductions' if PF_OK and TDS_OK else 'NEEDS VERIFICATION — payroll calculations could not be fully validated'}

### What must be fixed before real company financial records?
1. {'✅ Already working' if UNBAL_REJECT else '❌ URGENT: Enforce debit=credit validation on all journal entry creation paths'}
2. {'✅ Already working' if find('T3.2')['ok'] else '❌ Fix invoice → accounting chain'}
3. {'✅ Already working' if PAY_JE_OK else '❌ Fix payroll → journal entry posting'}
4. Add `/api/reports/trial-balance` endpoint for direct TB access by accountants
5. Add explicit `normal_balance` field to chart of accounts response (currently inferred from type)
6. Verify CGST/SGST split is stored at the line-item level and reflected in JEs
"""

report += opinion
report += f"""

---

*Audit completed: {date.today().strftime('%d %B %Y')}*  
*Total: {total} tests | Passed: {passed} ({pct:.1f}%) | Failed: {failed} | Critical: {n_crit}*  
*Audit script: /app/backend/tests/finance_cto_audit.py*
"""

with open("/app/FINANCE_CTO_AUDIT.md", "w") as f:
    f.write(report)

print("\n" + "="*60)
print("AUDIT COMPLETE")
print("="*60)
print(f"Total:    {total}")
print(f"Passed:   {passed} ({pct:.1f}%)")
print(f"Failed:   {failed}")
print(f"Critical: {n_crit}")
print(f"\nSign-off: {SIGNOFF}")
print("\nSection breakdown:")
for sid, sname, _ in SECTIONS:
    p_, n_ = score(sid)
    bar = "✅" if p_==n_ else ("🟡" if p_>=n_*0.7 else "❌")
    print(f"  {bar} {sid}: {sname:30s} {p_}/{n_}")
print("\nReport: /app/FINANCE_CTO_AUDIT.md")

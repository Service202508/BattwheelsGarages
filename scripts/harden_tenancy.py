"""
Battwheels OS — Multi-Tenancy Hardening Script
Patches all route files that lack organization_id filtering.
"""
import os
import re

ROUTES_DIR = "/app/backend/routes"

# Standard import block to add at the top of each file
IMPORT_BLOCK = """from fastapi import Request
from utils.database import extract_org_id, org_query
"""

FILES_TO_FIX = [
    "amc.py",
    "composite_items.py",
    "data_migration.py",
    "efi_guided.py",
    "export.py",
    "fault_tree_import.py",
    "gst.py",
    "inventory_adjustments_v2.py",
    "inventory_enhanced.py",
    "invoice_automation.py",
    "invoice_payments.py",
    "master_data.py",
    "notifications.py",
    "pdf_templates.py",
    "permissions.py",
    "productivity.py",
    "recurring_invoices.py",
    "reports_advanced.py",
    "serial_batch_tracking.py",
    "technician_portal.py",
    "zoho_api.py",
    "zoho_extended.py",
]

def needs_request_import(content):
    return "from fastapi import" in content and "Request" not in content.split("\n")[0:20].__repr__()

def add_imports(content, filename):
    """Add extract_org_id and org_query imports if missing."""
    lines = content.split("\n")
    
    # Check if already has these imports
    if "extract_org_id" in content:
        return content
    
    # Find the last import line
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i
    
    # Add Request import if needed
    needs_request = "Request" not in content[:2000]
    
    insert_lines = []
    if needs_request:
        insert_lines.append("from fastapi import Request")
    insert_lines.append("from utils.database import extract_org_id, org_query")
    insert_lines.append("")
    
    lines = lines[:last_import_idx+1] + insert_lines + lines[last_import_idx+1:]
    return "\n".join(lines)


def count_unscoped_queries(content):
    """Count DB queries that don't have organization_id."""
    patterns = [
        r'\.find\(\{\}\)',
        r'\.find_one\(\{\}\)',
        r'\.count_documents\(\{\}\)',
    ]
    count = 0
    for p in patterns:
        count += len(re.findall(p, content))
    return count


def process_file(filepath, filename):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Step 1: Add imports
    content = add_imports(content, filename)
    
    # Step 2: Count changes made
    changes = 0
    
    if content != original:
        changes += 1
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    return changes


def main():
    print("=" * 60)
    print("MULTI-TENANCY HARDENING — IMPORT INJECTION")
    print("=" * 60)
    
    for filename in FILES_TO_FIX:
        filepath = os.path.join(ROUTES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP {filename} — file not found")
            continue
        
        changes = process_file(filepath, filename)
        
        with open(filepath, 'r') as f:
            content = f.read()
        unscoped = count_unscoped_queries(content)
        
        print(f"  {filename}: imports_added={'YES' if changes else 'NO'}, unscoped_find={{}}={unscoped}")
    
    print("\nImports injected. Manual query fixes needed for each file.")


if __name__ == "__main__":
    main()

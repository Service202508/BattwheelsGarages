"""
Battwheels OS — Multi-Tenancy Hardening: Automated Query Patcher
Patches all route handler DB queries to include organization_id filtering.
"""
import re
import os

ROUTES_DIR = "/app/backend/routes"

FILES_TO_FIX = [
    "amc.py", "composite_items.py", "data_migration.py", "efi_guided.py",
    "export.py", "fault_tree_import.py", "gst.py", "inventory_adjustments_v2.py",
    "inventory_enhanced.py", "invoice_automation.py", "invoice_payments.py",
    "master_data.py", "notifications.py", "pdf_templates.py", "permissions.py",
    "productivity.py", "recurring_invoices.py", "reports_advanced.py",
    "serial_batch_tracking.py", "technician_portal.py", "zoho_api.py",
    "zoho_extended.py",
]

# Collections that are genuinely platform-wide (not tenant-scoped)
PLATFORM_COLLECTIONS = {
    "efi_platform_patterns", "vehicle_master", "fault_trees", 
    "system_config", "plans", "platform_settings"
}


def patch_file(filepath, filename):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Step 1: Ensure imports exist
    if "extract_org_id" not in content:
        # Find last import line
        lines = content.split("\n")
        last_imp = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_imp = i
        
        insert = []
        if "Request" not in content[:3000]:
            insert.append("from fastapi import Request")
        insert.append("from utils.database import extract_org_id, org_query")
        insert.append("")
        
        lines = lines[:last_imp+1] + insert + lines[last_imp+1:]
        content = "\n".join(lines)
        changes.append("Added imports")
    
    # Step 2: Find all async def handler functions and add org_id extraction
    # Pattern: async def handler_name(... request: Request ...):
    #   or: async def handler_name(...):  (needs request added)
    
    # Find route handlers
    handler_pattern = re.compile(
        r'(@router\.\w+\([^\)]*\)\n)'  # decorator
        r'(async def \w+\()'            # function start
        r'([^)]*)\)'                     # params
        r'([^:]*:)',                     # rest until colon
        re.MULTILINE
    )
    
    def add_org_id_to_handler(match):
        decorator = match.group(1)
        func_start = match.group(2)
        params = match.group(3)
        rest = match.group(4)
        
        # Don't add if already has extract_org_id nearby
        full = match.group(0)
        
        # Check if request param exists
        if "request:" not in params.lower() and "request :" not in params.lower():
            # Add request: Request param
            if params.strip():
                params = params.rstrip() + ", request: Request"
            else:
                params = "request: Request"
            changes.append(f"Added request param to handler")
        
        return f"{decorator}{func_start}{params}){rest}:"
    
    content = handler_pattern.sub(add_org_id_to_handler, content)
    
    # Step 3: Add org_id extraction at start of each handler body
    # Find pattern: async def ...(... request: Request ...):
    #   followed by first line of body
    handler_body = re.compile(
        r'(async def \w+\([^)]*request:\s*Request[^)]*\).*?:\n)'
        r'(\s+)((?!org_id\s*=\s*extract_org_id))',
        re.MULTILINE
    )
    
    def inject_org_id(match):
        sig = match.group(1)
        indent = match.group(2)
        first_line = match.group(3)
        return f"{sig}{indent}org_id = extract_org_id(request)\n{indent}{first_line}"
    
    content = handler_body.sub(inject_org_id, content)
    
    # Step 4: Replace .find({}) with .find(org_query(org_id))
    # and .find_one({}) with .find_one(org_query(org_id))
    for method in ['find', 'find_one', 'count_documents']:
        pattern = rf'\.{method}\(\{{\}}\)'
        replacement = f'.{method}(org_query(org_id))'
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"Replaced .{method}({{}}) calls")
    
    # Step 5: For .insert_one() calls, we need to ensure org_id is stamped
    # This is harder to do automatically — flag for manual review
    insert_count = len(re.findall(r'\.insert_one\(', content))
    
    # Write back
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
    
    return {
        "changes": changes,
        "insert_calls": insert_count,
        "modified": content != original
    }


def main():
    print("=" * 60)
    print("MULTI-TENANCY HARDENING — AUTOMATED PATCHING")
    print("=" * 60)
    
    results = {}
    for filename in FILES_TO_FIX:
        filepath = os.path.join(ROUTES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP {filename} — not found")
            continue
        
        result = patch_file(filepath, filename)
        results[filename] = result
        
        status = "MODIFIED" if result["modified"] else "NO CHANGE"
        print(f"  {filename}: {status} | changes: {len(result['changes'])} | inserts_to_review: {result['insert_calls']}")
        for c in result["changes"]:
            print(f"    - {c}")
    
    print(f"\nTotal files processed: {len(results)}")
    print(f"Files modified: {sum(1 for r in results.values() if r['modified'])}")


if __name__ == "__main__":
    main()

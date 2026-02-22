"""
PDF Generation Service
Uses WeasyPrint to generate professional PDF documents
"""
from weasyprint import HTML, CSS
from io import BytesIO
from datetime import datetime

def generate_invoice_html(invoice: dict, org_settings: dict = None) -> str:
    """Generate HTML template for invoice"""
    org = org_settings or {}
    company_name = org.get('company_name', 'Battwheels')
    company_address = org.get('address', '')
    company_phone = org.get('phone', '')
    company_email = org.get('email', '')
    company_gstin = org.get('gstin', '')
    logo_url = org.get('logo_url', '')
    
    # Logo HTML - only include if logo_url is provided
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{company_name}" style="max-height: 60px; max-width: 200px; object-fit: contain;" />'
    
    # Build line items HTML
    items_html = ""
    for idx, item in enumerate(invoice.get("line_items", []), 1):
        items_html += f"""
            <tr>
                <td class="center">{idx}</td>
                <td>
                    <strong>{item.get('name', '')}</strong>
                    {f"<br><small>{item.get('description', '')}</small>" if item.get('description') else ''}
                </td>
                <td class="center">{item.get('hsn_or_sac', '-')}</td>
                <td class="right">{item.get('quantity', 0)}</td>
                <td class="right">₹{item.get('rate', 0):,.2f}</td>
                <td class="right">{item.get('tax_percentage', 0)}%</td>
                <td class="right">₹{item.get('item_total', 0):,.2f}</td>
            </tr>
        """
    
    # Customer details
    customer_name = invoice.get('customer_name', '')
    billing_address = invoice.get('billing_address', {})
    if isinstance(billing_address, dict):
        addr_lines = [
            billing_address.get('address', ''),
            f"{billing_address.get('city', '')}, {billing_address.get('state', '')} {billing_address.get('zip', '')}",
            billing_address.get('country', '')
        ]
        customer_address = '<br>'.join([l for l in addr_lines if l.strip()])
    else:
        customer_address = str(billing_address)
    
    customer_gstin = invoice.get('gst_no', '') or invoice.get('customer_gstin', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1cm;
            }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.4;
                color: #333;
                margin: 0;
                padding: 20px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                border-bottom: 3px solid #C8FF00;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}
            .company-info {{
                flex: 1;
            }}
            .company-logo {{
                margin-bottom: 10px;
            }}
            .company-name {{
                font-size: 24pt;
                font-weight: bold;
                color: #1a1a1a;
                margin-bottom: 5px;
            }}
            .company-details {{
                font-size: 9pt;
                color: #666;
            }}
            .invoice-title {{
                text-align: right;
            }}
            .invoice-title h1 {{
                font-size: 28pt;
                color: #C8FF00;
                margin: 0;
                letter-spacing: 2px;
                text-shadow: 0 0 1px rgba(0,0,0,0.3);
            }}
            .invoice-number {{
                font-size: 12pt;
                color: #666;
                margin-top: 5px;
            }}
            .details-section {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 25px;
            }}
            .bill-to, .invoice-details {{
                width: 48%;
            }}
            .section-title {{
                font-size: 9pt;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }}
            .customer-name {{
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .customer-address {{
                font-size: 9pt;
                color: #666;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 4px 0;
                border-bottom: 1px dotted #eee;
            }}
            .detail-label {{
                color: #888;
            }}
            .detail-value {{
                font-weight: 500;
            }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .items-table th {{
                background: #111820;
                color: #C8FF00;
                padding: 12px 8px;
                text-align: left;
                font-size: 9pt;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .items-table td {{
                padding: 10px 8px;
                border-bottom: 1px solid #eee;
                vertical-align: top;
            }}
            .items-table .center {{ text-align: center; }}
            .items-table .right {{ text-align: right; }}
            .totals-section {{
                display: flex;
                justify-content: flex-end;
                margin-top: 20px;
            }}
            .totals-table {{
                width: 300px;
            }}
            .totals-table tr td {{
                padding: 8px 10px;
            }}
            .totals-table .label {{
                text-align: right;
                color: #666;
            }}
            .totals-table .value {{
                text-align: right;
                font-weight: 500;
                width: 120px;
            }}
            .totals-table .total-row {{
                font-size: 14pt;
                font-weight: bold;
                border-top: 2px solid #333;
                background: #f8f9fa;
            }}
            .totals-table .total-row .label {{
                color: #333;
            }}
            .totals-table .balance-row {{
                background: #C8FF00;
                color: #080C0F;
            }}
            .totals-table .balance-row td {{
                font-weight: bold;
            }}
            .notes-section {{
                margin-top: 30px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .notes-title {{
                font-size: 9pt;
                color: #888;
                text-transform: uppercase;
                margin-bottom: 8px;
            }}
            .notes-content {{
                font-size: 9pt;
                color: #666;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 15px;
                border-top: 2px solid #C8FF00;
                text-align: center;
                font-size: 8pt;
                color: #666;
            }}
            .footer strong {{
                color: #C8FF00;
            }}
            .status-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 9pt;
                font-weight: bold;
                text-transform: uppercase;
            }}
            .status-paid {{ background: #d4edda; color: #155724; }}
            .status-partial {{ background: #fff3cd; color: #856404; }}
            .status-sent {{ background: #cce5ff; color: #004085; }}
            .status-draft {{ background: #e2e3e5; color: #383d41; }}
            .status-overdue {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-info">
                {f'<div class="company-logo">{logo_html}</div>' if logo_html else ''}
                <div class="company-name">{company_name}</div>
                <div class="company-details">
                    {company_address}<br>
                    {f"Phone: {company_phone}<br>" if company_phone else ""}
                    {f"Email: {company_email}<br>" if company_email else ""}
                    {f"GSTIN: {company_gstin}" if company_gstin else ""}
                </div>
            </div>
            <div class="invoice-title">
                <h1>INVOICE</h1>
                <div class="invoice-number">#{invoice.get('invoice_number', '')}</div>
                <div style="margin-top: 10px;">
                    <span class="status-badge status-{invoice.get('status', 'draft')}">{invoice.get('status', 'Draft').upper()}</span>
                </div>
            </div>
        </div>
        
        <div class="details-section">
            <div class="bill-to">
                <div class="section-title">Bill To</div>
                <div class="customer-name">{customer_name}</div>
                <div class="customer-address">
                    {customer_address}
                    {f"<br>GSTIN: {customer_gstin}" if customer_gstin else ""}
                </div>
            </div>
            <div class="invoice-details">
                <div class="section-title">Invoice Details</div>
                <div class="detail-row">
                    <span class="detail-label">Invoice Date:</span>
                    <span class="detail-value">{invoice.get('date', '')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Due Date:</span>
                    <span class="detail-value">{invoice.get('due_date', '')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Payment Terms:</span>
                    <span class="detail-value">{invoice.get('payment_terms_label', f"Net {invoice.get('payment_terms', 15)}")}</span>
                </div>
                {f'<div class="detail-row"><span class="detail-label">Reference:</span><span class="detail-value">{invoice.get("reference_number")}</span></div>' if invoice.get('reference_number') else ''}
                {f'<div class="detail-row"><span class="detail-label">Place of Supply:</span><span class="detail-value">{invoice.get("place_of_supply")}</span></div>' if invoice.get('place_of_supply') else ''}
            </div>
        </div>
        
        <table class="items-table">
            <thead>
                <tr>
                    <th class="center" style="width: 40px;">#</th>
                    <th>Item & Description</th>
                    <th class="center" style="width: 80px;">HSN/SAC</th>
                    <th class="right" style="width: 60px;">Qty</th>
                    <th class="right" style="width: 90px;">Rate</th>
                    <th class="right" style="width: 60px;">Tax</th>
                    <th class="right" style="width: 100px;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div class="totals-section">
            <table class="totals-table">
                <tr>
                    <td class="label">Subtotal:</td>
                    <td class="value">₹{invoice.get('sub_total', 0):,.2f}</td>
                </tr>
                {f'<tr><td class="label">Discount:</td><td class="value">-₹{invoice.get("discount_total", 0):,.2f}</td></tr>' if invoice.get('discount_total', 0) > 0 else ''}
                <tr>
                    <td class="label">Tax (GST):</td>
                    <td class="value">₹{invoice.get('tax_total', 0):,.2f}</td>
                </tr>
                {f'<tr><td class="label">Shipping:</td><td class="value">₹{invoice.get("shipping_charge", 0):,.2f}</td></tr>' if invoice.get('shipping_charge', 0) > 0 else ''}
                {f'<tr><td class="label">Adjustment:</td><td class="value">₹{invoice.get("adjustment", 0):,.2f}</td></tr>' if invoice.get('adjustment', 0) != 0 else ''}
                <tr class="total-row">
                    <td class="label">Total:</td>
                    <td class="value">₹{invoice.get('total', 0):,.2f}</td>
                </tr>
                <tr class="balance-row">
                    <td class="label">Balance Due:</td>
                    <td class="value">₹{invoice.get('balance', 0):,.2f}</td>
                </tr>
            </table>
        </div>
        
        {f'''
        <div class="notes-section">
            <div class="notes-title">Notes</div>
            <div class="notes-content">{invoice.get('notes', '')}</div>
        </div>
        ''' if invoice.get('notes') else ''}
        
        {f'''
        <div class="notes-section">
            <div class="notes-title">Terms & Conditions</div>
            <div class="notes-content">{invoice.get('terms', '')}</div>
        </div>
        ''' if invoice.get('terms') else ''}
        
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | <strong>{company_name}</strong> | Powered by Battwheels OS
        </div>
    </body>
    </html>
    """
    return html


def generate_pdf_from_html(html_content: str) -> bytes:
    """Convert HTML to PDF using WeasyPrint"""
    html = HTML(string=html_content)
    pdf_buffer = BytesIO()
    html.write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def generate_estimate_html(estimate: dict, org_settings: dict = None) -> str:
    """Generate HTML template for estimate/quote"""
    org = org_settings or {}
    company_name = org.get('company_name', 'Battwheels')
    
    items_html = ""
    for idx, item in enumerate(estimate.get("line_items", []), 1):
        items_html += f"""
            <tr>
                <td class="center">{idx}</td>
                <td><strong>{item.get('name', '')}</strong></td>
                <td class="right">{item.get('quantity', 0)}</td>
                <td class="right">₹{item.get('rate', 0):,.2f}</td>
                <td class="right">₹{item.get('item_total', 0):,.2f}</td>
            </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 1cm; }}
            body {{ font-family: Arial, sans-serif; font-size: 10pt; padding: 20px; }}
            .header {{ border-bottom: 3px solid #22EDA9; padding-bottom: 15px; margin-bottom: 20px; }}
            .company-name {{ font-size: 24pt; font-weight: bold; }}
            h1 {{ color: #22EDA9; font-size: 28pt; text-align: right; margin: 0; }}
            .details {{ margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #f8f9fa; padding: 10px; text-align: left; border-bottom: 2px solid #22EDA9; }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; }}
            .center {{ text-align: center; }}
            .right {{ text-align: right; }}
            .totals {{ float: right; width: 250px; margin-top: 20px; }}
            .totals td {{ padding: 8px; }}
            .total-row {{ font-weight: bold; font-size: 14pt; border-top: 2px solid #333; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div style="display: flex; justify-content: space-between;">
                <div class="company-name">{company_name}</div>
                <div><h1>ESTIMATE</h1><p style="text-align: right;">#{estimate.get('estimate_number', '')}</p></div>
            </div>
        </div>
        <div class="details">
            <p><strong>Customer:</strong> {estimate.get('customer_name', '')}</p>
            <p><strong>Date:</strong> {estimate.get('date', '')} | <strong>Valid Until:</strong> {estimate.get('expiry_date', '')}</p>
        </div>
        <table>
            <thead><tr><th>#</th><th>Item</th><th class="right">Qty</th><th class="right">Rate</th><th class="right">Amount</th></tr></thead>
            <tbody>{items_html}</tbody>
        </table>
        <div class="totals">
            <table>
                <tr><td>Subtotal:</td><td class="right">₹{estimate.get('sub_total', 0):,.2f}</td></tr>
                <tr><td>Tax:</td><td class="right">₹{estimate.get('tax_total', 0):,.2f}</td></tr>
                <tr class="total-row"><td>Total:</td><td class="right">₹{estimate.get('total', 0):,.2f}</td></tr>
            </table>
        </div>
    </body>
    </html>
    """
    return html

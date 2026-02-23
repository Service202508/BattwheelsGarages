"""
PDF Generation Service
Uses WeasyPrint to generate professional GST-compliant PDF documents
Supports IRN/QR code for E-Invoicing
"""
from weasyprint import HTML, CSS
from io import BytesIO
from datetime import datetime
import base64
import logging

logger = logging.getLogger(__name__)

# ==================== INDIAN NUMBER SYSTEM (4D) ====================

def number_to_words_indian(amount: float) -> str:
    """
    Convert number to words using Indian number system (Lakhs, Crores)
    Examples:
        1,00,000 = "One Lakh"
        10,00,000 = "Ten Lakhs"  
        1,00,00,000 = "One Crore"
        47,560.50 = "Rupees Forty Seven Thousand Five Hundred Sixty and Paise Fifty Only"
    """
    if amount == 0:
        return "Rupees Zero Only"
    
    # Split into rupees and paise
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    
    # Words for numbers
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def two_digit_to_words(n):
        if n < 20:
            return ones[n]
        else:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 else '')
    
    def three_digit_to_words(n):
        if n == 0:
            return ''
        if n < 100:
            return two_digit_to_words(n)
        else:
            return ones[n // 100] + ' Hundred' + (' ' + two_digit_to_words(n % 100) if n % 100 else '')
    
    # Indian number system: Crores, Lakhs, Thousands, Hundreds
    result = ''
    
    if rupees >= 10000000:  # Crores
        crores = rupees // 10000000
        rupees = rupees % 10000000
        result += three_digit_to_words(crores) + ' Crore '
    
    if rupees >= 100000:  # Lakhs
        lakhs = rupees // 100000
        rupees = rupees % 100000
        result += two_digit_to_words(lakhs) + ' Lakh '
    
    if rupees >= 1000:  # Thousands
        thousands = rupees // 1000
        rupees = rupees % 1000
        result += two_digit_to_words(thousands) + ' Thousand '
    
    if rupees > 0:  # Hundreds and below
        result += three_digit_to_words(rupees)
    
    result = result.strip()
    
    if paise > 0:
        paise_words = two_digit_to_words(paise)
        if result:
            return f"Rupees {result} and Paise {paise_words} Only"
        else:
            return f"Paise {paise_words} Only"
    else:
        return f"Rupees {result} Only"


# ==================== GST STATE CODES ====================

GST_STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra",
    "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa",
    "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar Islands",
    "36": "Telangana", "37": "Andhra Pradesh (New)"
}

def get_state_name_from_code(state_code: str) -> str:
    """Get state name from GST state code"""
    return GST_STATE_CODES.get(str(state_code).zfill(2), "")

def get_state_code_from_gstin(gstin: str) -> str:
    """Extract state code from GSTIN (first 2 digits)"""
    if gstin and len(gstin) >= 2:
        return gstin[:2]
    return ""


# ==================== COMPREHENSIVE GST INVOICE PDF (4B, 4C) ====================

def generate_gst_invoice_html(
    invoice: dict, 
    line_items: list,
    org_settings: dict = None,
    irn_data: dict = None,
    bank_details: dict = None,
    payment_qr_url: str = None
) -> str:
    """
    Generate comprehensive GST-compliant invoice HTML with IRN block
    
    Args:
        invoice: Invoice document
        line_items: List of line item documents  
        org_settings: Organization settings
        irn_data: IRN details (irn, ack_no, ack_date, signed_qr_code)
        bank_details: Bank account details for payment
        payment_qr_url: Razorpay payment QR code URL
    """
    org = org_settings or {}
    
    # Supplier details
    company_name = org.get('company_name', org.get('name', 'Company Name'))
    company_legal_name = org.get('legal_name', company_name)
    company_address = org.get('address', '')
    company_city = org.get('city', '')
    company_state = org.get('state', '')
    company_pincode = org.get('pincode', org.get('zip', ''))
    company_phone = org.get('phone', '')
    company_email = org.get('email', '')
    company_gstin = org.get('gstin', '')
    company_pan = company_gstin[2:12] if company_gstin and len(company_gstin) >= 12 else ''
    company_state_code = get_state_code_from_gstin(company_gstin) or org.get('state_code', '')
    company_state_name = get_state_name_from_code(company_state_code) or company_state
    logo_url = org.get('logo_url', '')
    
    # Customer/Buyer details
    customer_name = invoice.get('customer_name', '')
    customer_gstin = invoice.get('customer_gstin', invoice.get('gst_no', ''))
    billing_address = invoice.get('billing_address', {})
    if isinstance(billing_address, dict):
        customer_address = billing_address.get('address', '')
        customer_city = billing_address.get('city', '')
        customer_state = billing_address.get('state', '')
        customer_pincode = billing_address.get('zip', billing_address.get('pincode', ''))
    else:
        customer_address = str(billing_address) if billing_address else ''
        customer_city = ''
        customer_state = ''
        customer_pincode = ''
    
    customer_state_code = get_state_code_from_gstin(customer_gstin) or invoice.get('place_of_supply', '')
    customer_state_name = get_state_name_from_code(customer_state_code) or customer_state
    customer_email = invoice.get('customer_email', '')
    customer_phone = invoice.get('customer_phone', '')
    
    # Invoice details
    invoice_number = invoice.get('invoice_number', '')
    invoice_date = invoice.get('invoice_date', invoice.get('date', ''))
    due_date = invoice.get('due_date', '')
    place_of_supply = invoice.get('place_of_supply', customer_state_code)
    place_of_supply_name = get_state_name_from_code(place_of_supply)
    reverse_charge = 'Yes' if invoice.get('reverse_charge') else 'No'
    reference_number = invoice.get('reference_number', '')
    
    # Determine document type
    doc_type = "TAX INVOICE"
    if invoice.get('doc_type') == 'CRN':
        doc_type = "CREDIT NOTE"
    elif invoice.get('is_exempt') or invoice.get('tax_total', 0) == 0:
        doc_type = "BILL OF SUPPLY"
    
    # Calculate if IGST or CGST/SGST
    is_igst = company_state_code != customer_state_code if company_state_code and customer_state_code else invoice.get('is_igst', False)
    
    # Logo HTML
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{company_name}" class="company-logo" />'
    
    # IRN Block HTML (4B)
    irn_block_html = ""
    if irn_data and irn_data.get('irn'):
        irn = irn_data.get('irn', '')
        ack_no = irn_data.get('ack_no', irn_data.get('irn_ack_no', ''))
        ack_date = irn_data.get('ack_date', irn_data.get('irn_ack_date', ''))
        signed_qr = irn_data.get('signed_qr_code', irn_data.get('irn_signed_qr', ''))
        
        # Generate QR code image
        qr_html = ""
        if signed_qr:
            try:
                from services.einvoice_service import generate_qr_code_base64
                qr_base64 = generate_qr_code_base64(signed_qr, size=100)
                qr_html = f'''
                    <div class="qr-container">
                        <img src="data:image/png;base64,{qr_base64}" alt="E-Invoice QR Code" class="irn-qr-code" />
                        <div class="qr-label">Scan to verify</div>
                    </div>
                '''
            except Exception as e:
                logger.warning(f"Failed to generate QR code for IRN: {e}")
        
        irn_block_html = f'''
        <div class="irn-block">
            <div class="irn-left">
                <div class="irn-row">
                    <span class="irn-label">IRN:</span>
                    <span class="irn-value irn-code">{irn}</span>
                </div>
                <div class="irn-row">
                    <span class="irn-label">Ack No.:</span>
                    <span class="irn-value">{ack_no}</span>
                </div>
                <div class="irn-row">
                    <span class="irn-label">Ack Date:</span>
                    <span class="irn-value">{ack_date}</span>
                </div>
            </div>
            <div class="irn-right">
                {qr_html}
            </div>
        </div>
        '''
    
    # Build line items table with GST breakdown
    items_html = ""
    for idx, item in enumerate(line_items, 1):
        hsn_sac = item.get('hsn_sac_code', item.get('hsn_or_sac', item.get('hsn_code', '-')))
        quantity = item.get('quantity', 0)
        unit = item.get('unit', 'Nos')
        rate = item.get('rate', 0)
        taxable_amount = item.get('taxable_amount', item.get('amount', 0) - item.get('discount_amount', 0))
        gst_rate = item.get('tax_rate', item.get('gst_rate', 0))
        
        if is_igst:
            igst_amt = item.get('igst_amount', item.get('tax_amount', 0))
            cgst_amt = 0
            sgst_amt = 0
        else:
            cgst_amt = item.get('cgst_amount', item.get('tax_amount', 0) / 2)
            sgst_amt = item.get('sgst_amount', item.get('tax_amount', 0) / 2)
            igst_amt = 0
        
        item_total = item.get('total', item.get('item_total', taxable_amount + igst_amt + cgst_amt + sgst_amt))
        
        items_html += f'''
            <tr>
                <td class="center">{idx}</td>
                <td>
                    <div class="item-name">{item.get('name', '')}</div>
                    {f'<div class="item-desc">{item.get("description", "")}</div>' if item.get('description') else ''}
                </td>
                <td class="center">{hsn_sac}</td>
                <td class="right">{quantity:,.2f}</td>
                <td class="center">{unit}</td>
                <td class="right">₹{rate:,.2f}</td>
                <td class="right">₹{taxable_amount:,.2f}</td>
                <td class="center">{gst_rate}%</td>
                {'<td class="right">₹' + f'{cgst_amt:,.2f}' + '</td>' if not is_igst else ''}
                {'<td class="right">₹' + f'{sgst_amt:,.2f}' + '</td>' if not is_igst else ''}
                {'<td class="right">₹' + f'{igst_amt:,.2f}' + '</td>' if is_igst else ''}
                <td class="right bold">₹{item_total:,.2f}</td>
            </tr>
        '''
    
    # Totals
    sub_total = invoice.get('sub_total', sum(item.get('taxable_amount', item.get('amount', 0)) for item in line_items))
    total_discount = invoice.get('total_discount', invoice.get('discount_total', 0))
    taxable_amount = invoice.get('taxable_amount', sub_total - total_discount)
    cgst_total = invoice.get('cgst_total', 0)
    sgst_total = invoice.get('sgst_total', 0)
    igst_total = invoice.get('igst_total', 0)
    tax_total = invoice.get('tax_total', cgst_total + sgst_total + igst_total)
    shipping_charge = invoice.get('shipping_charge', 0)
    adjustment = invoice.get('adjustment', 0)
    grand_total = invoice.get('grand_total', invoice.get('total', taxable_amount + tax_total + shipping_charge + adjustment))
    amount_in_words = number_to_words_indian(grand_total)
    
    # GST Summary table (required for B2B and invoices > ₹50,000)
    gst_summary_html = ""
    if customer_gstin or grand_total > 50000:
        # Group by HSN and tax rate
        hsn_summary = {}
        for item in line_items:
            hsn = item.get('hsn_sac_code', item.get('hsn_or_sac', '-'))
            rate = item.get('tax_rate', 0)
            key = f"{hsn}_{rate}"
            if key not in hsn_summary:
                hsn_summary[key] = {
                    'hsn': hsn,
                    'rate': rate,
                    'taxable': 0,
                    'cgst': 0,
                    'sgst': 0,
                    'igst': 0
                }
            hsn_summary[key]['taxable'] += item.get('taxable_amount', item.get('amount', 0))
            if is_igst:
                hsn_summary[key]['igst'] += item.get('igst_amount', item.get('tax_amount', 0))
            else:
                hsn_summary[key]['cgst'] += item.get('cgst_amount', item.get('tax_amount', 0) / 2)
                hsn_summary[key]['sgst'] += item.get('sgst_amount', item.get('tax_amount', 0) / 2)
        
        gst_rows = ""
        for key, data in hsn_summary.items():
            total_tax = data['cgst'] + data['sgst'] + data['igst']
            gst_rows += f'''
                <tr>
                    <td class="center">{data['hsn']}</td>
                    <td class="right">₹{data['taxable']:,.2f}</td>
                    {'<td class="right">₹' + f'{data["cgst"]:,.2f}' + '</td>' if not is_igst else ''}
                    {'<td class="right">₹' + f'{data["sgst"]:,.2f}' + '</td>' if not is_igst else ''}
                    {'<td class="right">₹' + f'{data["igst"]:,.2f}' + '</td>' if is_igst else ''}
                    <td class="right bold">₹{total_tax:,.2f}</td>
                </tr>
            '''
        
        gst_summary_html = f'''
        <div class="gst-summary-section">
            <div class="section-title">GST Summary</div>
            <table class="gst-summary-table">
                <thead>
                    <tr>
                        <th class="center">HSN/SAC</th>
                        <th class="right">Taxable Value</th>
                        {'<th class="right">CGST</th>' if not is_igst else ''}
                        {'<th class="right">SGST</th>' if not is_igst else ''}
                        {'<th class="right">IGST</th>' if is_igst else ''}
                        <th class="right">Total Tax</th>
                    </tr>
                </thead>
                <tbody>
                    {gst_rows}
                </tbody>
            </table>
        </div>
        '''
    
    # Bank Details Section
    bank_html = ""
    if bank_details:
        bank_html = f'''
        <div class="bank-section">
            <div class="section-title">Bank Details</div>
            <div class="bank-details">
                <div class="bank-row"><span class="bank-label">Bank Name:</span> <span>{bank_details.get('bank_name', '')}</span></div>
                <div class="bank-row"><span class="bank-label">Account Number:</span> <span>{bank_details.get('account_number', '')}</span></div>
                <div class="bank-row"><span class="bank-label">IFSC Code:</span> <span>{bank_details.get('ifsc_code', '')}</span></div>
                <div class="bank-row"><span class="bank-label">Account Type:</span> <span>{bank_details.get('account_type', 'Current')}</span></div>
                {f'<div class="bank-row"><span class="bank-label">UPI ID:</span> <span>{bank_details.get("upi_id", "")}</span></div>' if bank_details.get('upi_id') else ''}
            </div>
        </div>
        '''
    
    # Payment QR Section (Razorpay)
    payment_qr_html = ""
    if payment_qr_url:
        payment_qr_html = f'''
        <div class="payment-qr-section">
            <img src="{payment_qr_url}" alt="Payment QR" class="payment-qr" />
            <div class="qr-label">Scan to pay online</div>
        </div>
        '''
    
    # Terms and Conditions
    terms = invoice.get('terms_conditions', invoice.get('terms', org.get('default_terms', '')))
    default_terms = f"Goods once sold will not be taken back. Subject to {company_city or 'local'} jurisdiction."
    terms_html = f'''
    <div class="terms-section">
        <div class="section-title">Terms & Conditions</div>
        <div class="terms-content">{terms or default_terms}</div>
    </div>
    '''
    
    # Notes
    notes = invoice.get('customer_notes', invoice.get('notes', ''))
    notes_html = f'''
    <div class="notes-section">
        <div class="section-title">Notes</div>
        <div class="notes-content">{notes}</div>
    </div>
    ''' if notes else ''
    
    # Tax columns header
    if is_igst:
        tax_header = '<th class="right" style="width: 90px;">IGST Amt</th>'
    else:
        tax_header = '''
            <th class="right" style="width: 80px;">CGST Amt</th>
            <th class="right" style="width: 80px;">SGST Amt</th>
        '''
    
    # Build complete HTML
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 15mm;
            }}
            * {{
                box-sizing: border-box;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 9pt;
                line-height: 1.4;
                color: #000;
                margin: 0;
                padding: 0;
                background: #fff;
            }}
            
            /* Header Section */
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #333;
            }}
            .company-logo {{
                max-height: 60px;
                max-width: 180px;
                object-fit: contain;
                margin-bottom: 8px;
            }}
            .doc-title {{
                text-align: center;
                font-size: 14pt;
                font-weight: bold;
                margin: 10px 0;
                letter-spacing: 1px;
            }}
            
            /* Supplier & Buyer Section */
            .parties-section {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
            }}
            .party-block {{
                width: 48%;
            }}
            .party-title {{
                font-weight: bold;
                font-size: 8pt;
                color: #666;
                text-transform: uppercase;
                margin-bottom: 5px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 3px;
            }}
            .party-name {{
                font-weight: bold;
                font-size: 10pt;
                margin-bottom: 3px;
            }}
            .party-detail {{
                font-size: 8pt;
                color: #333;
                margin: 2px 0;
            }}
            .gstin-highlight {{
                font-weight: bold;
                color: #000;
            }}
            
            /* Invoice Details Row */
            .invoice-details-row {{
                display: flex;
                justify-content: space-between;
                background: #f8f8f8;
                padding: 8px 12px;
                margin-bottom: 15px;
                border: 1px solid #ddd;
            }}
            .detail-item {{
                text-align: center;
            }}
            .detail-label {{
                font-size: 7pt;
                color: #666;
                text-transform: uppercase;
            }}
            .detail-value {{
                font-weight: bold;
                font-size: 9pt;
            }}
            
            /* IRN Block (4B) */
            .irn-block {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                border: 1px solid #333;
                background: #f8f8f8;
                padding: 10px 14px;
                margin-bottom: 15px;
            }}
            .irn-left {{
                width: 70%;
            }}
            .irn-right {{
                width: 28%;
                text-align: center;
            }}
            .irn-row {{
                margin: 4px 0;
            }}
            .irn-label {{
                font-weight: bold;
                font-size: 8pt;
            }}
            .irn-value {{
                font-family: 'Courier New', Courier, monospace;
                font-size: 8pt;
            }}
            .irn-code {{
                font-size: 7.5pt;
                word-break: break-all;
                color: #000;
            }}
            .irn-qr-code {{
                width: 80px;
                height: 80px;
            }}
            .qr-container {{
                display: inline-block;
            }}
            .qr-label {{
                font-size: 7pt;
                color: #666;
                text-align: center;
                margin-top: 3px;
            }}
            
            /* Line Items Table */
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            .items-table th {{
                background: #333;
                color: #fff;
                padding: 8px 5px;
                text-align: left;
                font-size: 7.5pt;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            .items-table td {{
                padding: 6px 5px;
                border-bottom: 1px solid #ddd;
                vertical-align: top;
                font-size: 8pt;
            }}
            .items-table .center {{ text-align: center; }}
            .items-table .right {{ text-align: right; }}
            .items-table .bold {{ font-weight: bold; }}
            .item-name {{
                font-weight: 500;
            }}
            .item-desc {{
                font-size: 7pt;
                color: #666;
                margin-top: 2px;
            }}
            
            /* Totals Section */
            .totals-container {{
                display: flex;
                justify-content: flex-end;
                margin-bottom: 15px;
            }}
            .totals-table {{
                width: 280px;
            }}
            .totals-table td {{
                padding: 5px 8px;
                font-size: 8pt;
            }}
            .totals-table .label {{
                text-align: right;
                color: #666;
            }}
            .totals-table .value {{
                text-align: right;
                font-weight: 500;
                width: 100px;
            }}
            .totals-table .total-row {{
                font-size: 11pt;
                font-weight: bold;
                border-top: 2px solid #333;
                background: #f0f0f0;
            }}
            .totals-table .total-row .label,
            .totals-table .total-row .value {{
                color: #000;
                padding: 8px;
            }}
            
            /* Amount in Words */
            .amount-words {{
                background: #f8f8f8;
                padding: 8px 12px;
                margin-bottom: 15px;
                border: 1px solid #ddd;
                font-style: italic;
            }}
            .amount-words-label {{
                font-weight: bold;
                font-size: 8pt;
            }}
            
            /* GST Summary Table */
            .gst-summary-section {{
                margin-bottom: 15px;
            }}
            .section-title {{
                font-weight: bold;
                font-size: 9pt;
                color: #333;
                margin-bottom: 5px;
                text-transform: uppercase;
                border-bottom: 1px solid #ddd;
                padding-bottom: 3px;
            }}
            .gst-summary-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .gst-summary-table th {{
                background: #eee;
                padding: 6px;
                font-size: 7.5pt;
                text-transform: uppercase;
                border: 1px solid #ddd;
            }}
            .gst-summary-table td {{
                padding: 5px;
                font-size: 8pt;
                border: 1px solid #ddd;
            }}
            
            /* Bank & Payment Section */
            .bottom-section {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
            }}
            .bank-section {{
                width: 45%;
            }}
            .bank-details {{
                font-size: 8pt;
            }}
            .bank-row {{
                margin: 3px 0;
            }}
            .bank-label {{
                font-weight: bold;
                display: inline-block;
                width: 100px;
            }}
            .payment-qr-section {{
                text-align: center;
            }}
            .payment-qr {{
                width: 80px;
                height: 80px;
            }}
            
            /* Terms & Notes */
            .terms-section, .notes-section {{
                margin-bottom: 10px;
            }}
            .terms-content, .notes-content {{
                font-size: 8pt;
                color: #444;
            }}
            
            /* Signature Block */
            .signature-section {{
                margin-top: 30px;
                text-align: right;
            }}
            .signature-line {{
                border-top: 1px solid #333;
                width: 180px;
                margin-left: auto;
                padding-top: 5px;
            }}
            .signature-label {{
                font-size: 8pt;
            }}
            .for-company {{
                font-weight: bold;
                font-size: 9pt;
                margin-bottom: 40px;
            }}
            
            /* Footer */
            .footer {{
                margin-top: 20px;
                padding-top: 10px;
                border-top: 1px solid #ddd;
                text-align: center;
                font-size: 7pt;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <!-- Header with Logo & Title -->
        <div class="header">
            <div>
                {logo_html}
            </div>
            <div class="doc-title">{doc_type}</div>
            <div style="text-align: right;">
                <div style="font-weight: bold; font-size: 11pt;">{invoice_number}</div>
            </div>
        </div>
        
        <!-- Supplier & Buyer Details -->
        <div class="parties-section">
            <div class="party-block">
                <div class="party-title">Supplier</div>
                <div class="party-name">{company_legal_name}</div>
                <div class="party-detail">{company_address}</div>
                <div class="party-detail">{company_city}{', ' + company_state if company_state else ''} {company_pincode}</div>
                {f'<div class="party-detail">Phone: {company_phone}</div>' if company_phone else ''}
                {f'<div class="party-detail">Email: {company_email}</div>' if company_email else ''}
                <div class="party-detail"><span class="gstin-highlight">GSTIN: {company_gstin}</span></div>
                <div class="party-detail">State: {company_state_name} | Code: {company_state_code}</div>
                {f'<div class="party-detail">PAN: {company_pan}</div>' if company_pan else ''}
            </div>
            <div class="party-block">
                <div class="party-title">Bill To</div>
                <div class="party-name">{customer_name}</div>
                <div class="party-detail">{customer_address}</div>
                <div class="party-detail">{customer_city}{', ' + customer_state if customer_state else ''} {customer_pincode}</div>
                {f'<div class="party-detail"><span class="gstin-highlight">GSTIN: {customer_gstin}</span></div>' if customer_gstin else ''}
                <div class="party-detail">State: {customer_state_name} | Code: {customer_state_code}</div>
            </div>
        </div>
        
        <!-- Invoice Details Row -->
        <div class="invoice-details-row">
            <div class="detail-item">
                <div class="detail-label">Invoice Number</div>
                <div class="detail-value">{invoice_number}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Invoice Date</div>
                <div class="detail-value">{invoice_date}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Due Date</div>
                <div class="detail-value">{due_date}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Place of Supply</div>
                <div class="detail-value">{place_of_supply_name or place_of_supply}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Reverse Charge</div>
                <div class="detail-value">{reverse_charge}</div>
            </div>
        </div>
        
        <!-- IRN Block (if registered) -->
        {irn_block_html}
        
        <!-- Line Items Table -->
        <table class="items-table">
            <thead>
                <tr>
                    <th class="center" style="width: 25px;">#</th>
                    <th>Description</th>
                    <th class="center" style="width: 60px;">HSN/SAC</th>
                    <th class="right" style="width: 50px;">Qty</th>
                    <th class="center" style="width: 35px;">Unit</th>
                    <th class="right" style="width: 70px;">Rate</th>
                    <th class="right" style="width: 80px;">Taxable</th>
                    <th class="center" style="width: 45px;">GST%</th>
                    {tax_header}
                    <th class="right" style="width: 80px;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <!-- Totals Section -->
        <div class="totals-container">
            <table class="totals-table">
                <tr>
                    <td class="label">Subtotal:</td>
                    <td class="value">₹{sub_total:,.2f}</td>
                </tr>
                {f'<tr><td class="label">Discount:</td><td class="value">-₹{total_discount:,.2f}</td></tr>' if total_discount > 0 else ''}
                {f'<tr><td class="label">CGST:</td><td class="value">₹{cgst_total:,.2f}</td></tr>' if not is_igst and cgst_total > 0 else ''}
                {f'<tr><td class="label">SGST:</td><td class="value">₹{sgst_total:,.2f}</td></tr>' if not is_igst and sgst_total > 0 else ''}
                {f'<tr><td class="label">IGST:</td><td class="value">₹{igst_total:,.2f}</td></tr>' if is_igst and igst_total > 0 else ''}
                {f'<tr><td class="label">Shipping:</td><td class="value">₹{shipping_charge:,.2f}</td></tr>' if shipping_charge > 0 else ''}
                {f'<tr><td class="label">Round Off:</td><td class="value">₹{adjustment:,.2f}</td></tr>' if adjustment != 0 else ''}
                <tr class="total-row">
                    <td class="label">Grand Total:</td>
                    <td class="value">₹{grand_total:,.2f}</td>
                </tr>
            </table>
        </div>
        
        <!-- Amount in Words -->
        <div class="amount-words">
            <span class="amount-words-label">Amount in Words:</span> {amount_in_words}
        </div>
        
        <!-- GST Summary -->
        {gst_summary_html}
        
        <!-- Bank & Payment QR -->
        <div class="bottom-section">
            {bank_html}
            {payment_qr_html}
        </div>
        
        <!-- Terms & Notes -->
        {terms_html}
        {notes_html}
        
        <!-- Signature Block -->
        <div class="signature-section">
            <div class="for-company">For {company_name}</div>
            <div class="signature-line">
                <div class="signature-label">Authorized Signatory</div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            This is a computer generated invoice | Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </body>
    </html>
    '''
    return html


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
    company_address = org.get('address', '')
    company_phone = org.get('phone', '')
    company_email = org.get('email', '')
    company_gstin = org.get('gstin', '')
    logo_url = org.get('logo_url', '')
    
    # Logo HTML - only include if logo_url is provided
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{company_name}" style="max-height: 50px; max-width: 180px; object-fit: contain;" />'
    
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
    
    # Customer details
    customer_name = estimate.get('customer_name', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 1cm; }}
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; padding: 20px; }}
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
                margin-bottom: 8px;
            }}
            .company-name {{ font-size: 24pt; font-weight: bold; color: #1a1a1a; }}
            .company-details {{ font-size: 9pt; color: #666; margin-top: 5px; }}
            .estimate-title {{
                text-align: right;
            }}
            .estimate-title h1 {{ 
                color: #C8FF00; 
                font-size: 28pt; 
                margin: 0; 
                letter-spacing: 2px;
                text-shadow: 0 0 1px rgba(0,0,0,0.3);
            }}
            .estimate-number {{
                font-size: 12pt;
                color: #666;
                margin-top: 5px;
            }}
            .details {{ margin-bottom: 20px; }}
            .details p {{ margin: 5px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ 
                background: #111820; 
                color: #C8FF00;
                padding: 12px 10px; 
                text-align: left; 
                font-size: 9pt;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; }}
            .center {{ text-align: center; }}
            .right {{ text-align: right; }}
            .totals {{ float: right; width: 280px; margin-top: 20px; }}
            .totals td {{ padding: 8px 10px; }}
            .totals .label {{ text-align: right; color: #666; }}
            .totals .value {{ text-align: right; font-weight: 500; }}
            .total-row {{ 
                font-weight: bold; 
                font-size: 14pt; 
                border-top: 2px solid #333; 
                background: #C8FF00;
                color: #080C0F;
            }}
            .footer {{
                clear: both;
                margin-top: 60px;
                padding-top: 15px;
                border-top: 2px solid #C8FF00;
                text-align: center;
                font-size: 8pt;
                color: #666;
            }}
            .footer strong {{
                color: #080C0F;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-info">
                {f'<div class="company-logo">{logo_html}</div>' if logo_html else ''}
                <div class="company-name">{company_name}</div>
                <div class="company-details">
                    {company_address}
                    {f"<br>Phone: {company_phone}" if company_phone else ""}
                    {f"<br>Email: {company_email}" if company_email else ""}
                    {f"<br>GSTIN: {company_gstin}" if company_gstin else ""}
                </div>
            </div>
            <div class="estimate-title">
                <h1>ESTIMATE</h1>
                <div class="estimate-number">#{estimate.get('estimate_number', '')}</div>
            </div>
        </div>
        <div class="details">
            <p><strong>Customer:</strong> {customer_name}</p>
            <p><strong>Date:</strong> {estimate.get('date', '')} | <strong>Valid Until:</strong> {estimate.get('expiry_date', '')}</p>
        </div>
        <table>
            <thead><tr><th class="center" style="width: 40px;">#</th><th>Item</th><th class="right" style="width: 60px;">Qty</th><th class="right" style="width: 90px;">Rate</th><th class="right" style="width: 100px;">Amount</th></tr></thead>
            <tbody>{items_html}</tbody>
        </table>
        <div class="totals">
            <table>
                <tr><td class="label">Subtotal:</td><td class="value">₹{estimate.get('sub_total', 0):,.2f}</td></tr>
                <tr><td class="label">Tax:</td><td class="value">₹{estimate.get('tax_total', 0):,.2f}</td></tr>
                <tr class="total-row"><td class="label">Total:</td><td class="value">₹{estimate.get('total', 0):,.2f}</td></tr>
            </table>
        </div>
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y')} | <strong>{company_name}</strong> | Powered by Battwheels OS
        </div>
    </body>
    </html>
    """
    return html

# Test file for Zoho-style enhanced features: Edit, Share, Attachments, Comments, History
# Tests Invoice and Estimate enhanced functionality

import pytest
import requests
import os
import time

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestInvoiceEnhancedFeatures:
    """Test Invoice enhanced features: Edit, Share, Attachments, Comments, History"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.headers = {"Content-Type": "application/json"}
        # Get a draft invoice for edit tests
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/?status=draft&per_page=1", headers=self.headers)
        if response.status_code == 200:
            invoices = response.json().get('invoices', [])
            self.draft_invoice_id = invoices[0].get('invoice_id') if invoices else None
        else:
            self.draft_invoice_id = None
            
        # Get a non-draft invoice for share/attachments/comments tests
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/?status=sent&per_page=1", headers=self.headers)
        if response.status_code == 200:
            invoices = response.json().get('invoices', [])
            self.sent_invoice_id = invoices[0].get('invoice_id') if invoices else None
        else:
            self.sent_invoice_id = None
    
    # ==================== INVOICE EDIT TESTS ====================
    
    def test_get_invoice_detail(self):
        """Test getting invoice detail with line items"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'invoice' in data
        invoice = data['invoice']
        assert 'invoice_id' in invoice
        assert 'invoice_number' in invoice
        assert 'line_items' in invoice
        assert 'history' in invoice
    
    def test_update_draft_invoice_notes(self):
        """Test updating draft invoice customer notes"""
        if not self.draft_invoice_id:
            pytest.skip("No draft invoice available")
        
        update_data = {"customer_notes": f"Updated notes at {time.time()}"}
        response = requests.put(
            f"{BASE_URL}/api/invoices-enhanced/{self.draft_invoice_id}",
            headers=self.headers,
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert data.get('message') == 'Invoice updated'
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{self.draft_invoice_id}", headers=self.headers)
        assert get_response.status_code == 200
        invoice = get_response.json().get('invoice', {})
        assert invoice.get('customer_notes') == update_data['customer_notes']
    
    def test_update_non_draft_invoice_limited(self):
        """Test that non-draft invoices have limited update fields"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        # Try to update notes (allowed)
        update_data = {"customer_notes": f"Updated notes at {time.time()}"}
        response = requests.put(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}",
            headers=self.headers,
            json=update_data
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
    
    # ==================== INVOICE SHARE TESTS ====================
    
    def test_create_share_link(self):
        """Test creating a share link for invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        share_config = {
            "expiry_days": 30,
            "allow_payment": True,
            "password_protected": False
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/share",
            headers=self.headers,
            json=share_config
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'share_link' in data
        share_link = data['share_link']
        assert 'share_link_id' in share_link
        assert 'public_url' in share_link
        assert 'share_token' in share_link
        assert 'expiry_date' in share_link
    
    def test_share_link_for_draft_fails(self):
        """Test that creating share link for draft invoice fails"""
        if not self.draft_invoice_id:
            pytest.skip("No draft invoice available")
        
        share_config = {"expiry_days": 30}
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.draft_invoice_id}/share",
            headers=self.headers,
            json=share_config
        )
        # Should fail for draft invoices
        assert response.status_code == 400
    
    # ==================== INVOICE ATTACHMENTS TESTS ====================
    
    def test_list_attachments_empty(self):
        """Test listing attachments for invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/attachments", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'attachments' in data
        assert isinstance(data['attachments'], list)
    
    def test_upload_attachment(self):
        """Test uploading attachment to invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        # Create a test file
        files = {'file': ('test_doc.txt', b'Test attachment content', 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/attachments",
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'attachment' in data
        attachment = data['attachment']
        assert 'attachment_id' in attachment
        assert attachment.get('filename') == 'test_doc.txt'
        
        # Store for cleanup
        self.test_attachment_id = attachment['attachment_id']
    
    def test_delete_attachment(self):
        """Test deleting attachment from invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        # First upload an attachment
        files = {'file': ('delete_test.txt', b'Delete test content', 'text/plain')}
        upload_response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/attachments",
            files=files
        )
        assert upload_response.status_code == 200
        attachment_id = upload_response.json().get('attachment', {}).get('attachment_id')
        
        # Delete the attachment
        delete_response = requests.delete(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/attachments/{attachment_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        assert delete_response.json().get('code') == 0
        assert delete_response.json().get('message') == 'Attachment deleted'
    
    # ==================== INVOICE COMMENTS TESTS ====================
    
    def test_list_comments_empty(self):
        """Test listing comments for invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/comments", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'comments' in data
        assert isinstance(data['comments'], list)
    
    def test_add_comment(self):
        """Test adding comment to invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        comment_data = {
            "comment": f"Test comment at {time.time()}",
            "is_internal": True
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/comments",
            headers=self.headers,
            json=comment_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'comment' in data
        comment = data['comment']
        assert 'comment_id' in comment
        assert comment.get('comment') == comment_data['comment']
        assert comment.get('is_internal') == True
        
        # Store for cleanup
        self.test_comment_id = comment['comment_id']
    
    def test_delete_comment(self):
        """Test deleting comment from invoice"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        # First add a comment
        comment_data = {"comment": "Comment to delete", "is_internal": True}
        add_response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/comments",
            headers=self.headers,
            json=comment_data
        )
        assert add_response.status_code == 200
        comment_id = add_response.json().get('comment', {}).get('comment_id')
        
        # Delete the comment
        delete_response = requests.delete(
            f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/comments/{comment_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        assert delete_response.json().get('code') == 0
        assert delete_response.json().get('message') == 'Comment deleted'
    
    # ==================== INVOICE HISTORY TESTS ====================
    
    def test_get_invoice_history(self):
        """Test getting invoice history"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/history", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'history' in data
        assert isinstance(data['history'], list)
        
        # History should have at least created entry
        if data['history']:
            history_entry = data['history'][0]
            assert 'history_id' in history_entry
            assert 'action' in history_entry
            assert 'timestamp' in history_entry
    
    # ==================== INVOICE PDF TESTS ====================
    
    def test_pdf_endpoint_exists(self):
        """Test that PDF endpoint exists (may fail due to dependencies)"""
        if not self.sent_invoice_id:
            pytest.skip("No sent invoice available")
        
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{self.sent_invoice_id}/pdf", headers=self.headers)
        # PDF may fail due to missing system dependencies, but endpoint should exist
        assert response.status_code in [200, 500]  # 500 if weasyprint deps missing


class TestEstimateEnhancedFeatures:
    """Test Estimate enhanced features: Edit"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.headers = {"Content-Type": "application/json"}
        # Get a draft estimate for edit tests
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?status=draft&per_page=1", headers=self.headers)
        if response.status_code == 200:
            estimates = response.json().get('estimates', [])
            self.draft_estimate_id = estimates[0].get('estimate_id') if estimates else None
        else:
            self.draft_estimate_id = None
    
    def test_get_estimate_detail(self):
        """Test getting estimate detail with line items"""
        if not self.draft_estimate_id:
            pytest.skip("No draft estimate available")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{self.draft_estimate_id}", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'estimate' in data
        estimate = data['estimate']
        assert 'estimate_id' in estimate
        assert 'estimate_number' in estimate
        assert 'line_items' in estimate
    
    def test_update_draft_estimate_notes(self):
        """Test updating draft estimate notes"""
        if not self.draft_estimate_id:
            pytest.skip("No draft estimate available")
        
        update_data = {"notes": f"Updated notes at {time.time()}"}
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{self.draft_estimate_id}",
            headers=self.headers,
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert data.get('message') == 'Estimate updated'
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{self.draft_estimate_id}", headers=self.headers)
        assert get_response.status_code == 200
        estimate = get_response.json().get('estimate', {})
        assert estimate.get('notes') == update_data['notes']
    
    def test_list_estimates(self):
        """Test listing estimates"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'estimates' in data
        assert 'page_context' in data
    
    def test_estimates_summary(self):
        """Test estimates summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/summary", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'summary' in data
        summary = data['summary']
        assert 'total' in summary
        assert 'by_status' in summary


class TestInvoiceDetailActions:
    """Test Invoice detail dialog action buttons"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.headers = {"Content-Type": "application/json"}
        # Get any invoice
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/?per_page=1", headers=self.headers)
        if response.status_code == 200:
            invoices = response.json().get('invoices', [])
            self.invoice_id = invoices[0].get('invoice_id') if invoices else None
        else:
            self.invoice_id = None
    
    def test_clone_invoice(self):
        """Test cloning an invoice"""
        if not self.invoice_id:
            pytest.skip("No invoice available")
        
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.invoice_id}/clone",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('code') == 0
        assert 'invoice' in data
        cloned = data['invoice']
        assert cloned.get('invoice_id') != self.invoice_id
        assert cloned.get('status') == 'draft'
    
    def test_void_invoice(self):
        """Test voiding an invoice (using cloned draft)"""
        if not self.invoice_id:
            pytest.skip("No invoice available")
        
        # First clone to get a draft we can void
        clone_response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{self.invoice_id}/clone",
            headers=self.headers
        )
        if clone_response.status_code != 200:
            pytest.skip("Could not clone invoice")
        
        cloned_id = clone_response.json().get('invoice', {}).get('invoice_id')
        
        # Void the cloned invoice
        void_response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{cloned_id}/void?reason=Test%20void",
            headers=self.headers
        )
        assert void_response.status_code == 200
        assert void_response.json().get('code') == 0
        
        # Verify status changed
        get_response = requests.get(f"{BASE_URL}/api/invoices-enhanced/{cloned_id}", headers=self.headers)
        assert get_response.status_code == 200
        assert get_response.json().get('invoice', {}).get('status') == 'void'

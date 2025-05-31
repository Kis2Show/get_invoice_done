#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example tests for invoice OCR system
"""

import pytest
import os
import sqlite3
from unittest.mock import Mock, patch

class TestInvoiceProcessing:
    """Test invoice processing functionality"""
    
    @pytest.mark.unit
    def test_database_connection(self, test_db):
        """Test database connection"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        assert len(tables) > 0
        assert ('invoices',) in tables
    
    @pytest.mark.unit
    def test_sample_invoice_data(self, sample_invoice_data):
        """Test sample invoice data structure"""
        required_fields = [
            'file_name', 'file_path', 'file_type', 'invoice_number',
            'seller_name', 'buyer_name', 'total_amount'
        ]
        
        for field in required_fields:
            assert field in sample_invoice_data
            assert sample_invoice_data[field] is not None
    
    @pytest.mark.unit
    def test_invoice_directories(self, test_invoice_dirs):
        """Test invoice directories creation"""
        required_dirs = ['pdf', 'imge', 'unrecognized']
        
        for dir_name in required_dirs:
            assert dir_name in test_invoice_dirs
            assert os.path.exists(test_invoice_dirs[dir_name])
            assert os.path.isdir(test_invoice_dirs[dir_name])
    
    @pytest.mark.ocr
    def test_mock_ocr_service(self, mock_ocr_service):
        """Test mock OCR service"""
        # Test text extraction
        text = mock_ocr_service.extract_text("dummy_path")
        assert text == "测试OCR提取的文本"
        
        # Test invoice processing
        result = mock_ocr_service.process_invoice("dummy_path")
        assert 'invoice_number' in result
        assert 'confidence' in result
        assert result['confidence'] > 0.9

class TestConfiguration:
    """Test configuration and setup"""
    
    @pytest.mark.unit
    def test_config_values(self, test_config):
        """Test configuration values"""
        assert 'DATABASE_URL' in test_config
        assert 'INVOICE_DIR' in test_config
        assert 'OCR_CONFIDENCE_THRESHOLD' in test_config
        
        # Test threshold value
        assert 0 < test_config['OCR_CONFIDENCE_THRESHOLD'] < 1
        
        # Test file size limit
        assert test_config['MAX_FILE_SIZE'] > 0
    
    @pytest.mark.unit
    def test_allowed_extensions(self, test_config):
        """Test allowed file extensions"""
        extensions = test_config['ALLOWED_EXTENSIONS']
        assert isinstance(extensions, list)
        assert 'pdf' in extensions
        assert 'jpg' in extensions

class TestAPI:
    """Test API endpoints"""
    
    @pytest.mark.api
    @pytest.mark.skipif(True, reason="Requires FastAPI app")
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    @pytest.mark.api
    @pytest.mark.skipif(True, reason="Requires FastAPI app")
    def test_invoices_list_endpoint(self, test_client):
        """Test invoices list endpoint"""
        response = test_client.get("/api/invoices/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestDatabase:
    """Test database operations"""
    
    @pytest.mark.database
    def test_insert_invoice(self, test_db, sample_invoice_data):
        """Test inserting invoice data"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Insert sample data
        cursor.execute('''
            INSERT INTO invoices (
                file_name, file_path, file_type, invoice_number,
                seller_name, buyer_name, total_amount, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sample_invoice_data['file_name'],
            sample_invoice_data['file_path'],
            sample_invoice_data['file_type'],
            sample_invoice_data['invoice_number'],
            sample_invoice_data['seller_name'],
            sample_invoice_data['buyer_name'],
            sample_invoice_data['total_amount'],
            sample_invoice_data['confidence']
        ))
        
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM invoices")
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Verify data
        cursor.execute("SELECT * FROM invoices WHERE file_name = ?", 
                      (sample_invoice_data['file_name'],))
        result = cursor.fetchone()
        assert result is not None
        
        conn.close()
    
    @pytest.mark.database
    def test_query_invoices(self, test_db, sample_invoice_data):
        """Test querying invoice data"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Insert test data
        cursor.execute('''
            INSERT INTO invoices (file_name, file_path, file_type, seller_name, buyer_name, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            sample_invoice_data['file_name'],
            sample_invoice_data['file_path'],
            sample_invoice_data['file_type'],
            sample_invoice_data['seller_name'],
            sample_invoice_data['buyer_name'],
            sample_invoice_data['total_amount']
        ))
        conn.commit()
        
        # Query by seller
        cursor.execute("SELECT * FROM invoices WHERE seller_name = ?",
                      (sample_invoice_data['seller_name'],))
        results = cursor.fetchall()
        assert len(results) == 1
        
        # Query by buyer
        cursor.execute("SELECT * FROM invoices WHERE buyer_name LIKE ?",
                      ('%宁波牧柏%',))
        results = cursor.fetchall()
        assert len(results) == 1
        
        conn.close()

class TestFileHandling:
    """Test file handling operations"""
    
    @pytest.mark.unit
    def test_pdf_content(self, sample_pdf_content):
        """Test PDF content handling"""
        assert sample_pdf_content.startswith(b'%PDF')
        assert len(sample_pdf_content) > 0
    
    @pytest.mark.unit
    def test_file_extension_validation(self):
        """Test file extension validation"""
        valid_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp']
        
        test_files = [
            'invoice.pdf',
            'scan.jpg',
            'document.PNG',
            'receipt.jpeg'
        ]
        
        for file_name in test_files:
            extension = file_name.split('.')[-1].lower()
            assert extension in valid_extensions

@pytest.mark.slow
class TestPerformance:
    """Performance tests"""
    
    @pytest.mark.performance
    def test_database_performance(self, test_db):
        """Test database performance with multiple records"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Insert multiple records
        import time
        start_time = time.time()
        
        for i in range(100):
            cursor.execute('''
                INSERT INTO invoices (file_name, total_amount)
                VALUES (?, ?)
            ''', (f'test_invoice_{i}.pdf', 100.0 + i))
        
        conn.commit()
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # Less than 1 second
        
        # Verify count
        cursor.execute("SELECT COUNT(*) FROM invoices")
        count = cursor.fetchone()[0]
        assert count == 100
        
        conn.close()

# Integration tests
@pytest.mark.integration
class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_workflow(self, test_db, test_invoice_dirs, sample_invoice_data):
        """Test complete workflow"""
        # This would test the complete flow from file upload to database storage
        # For now, just verify the components are available
        assert os.path.exists(test_db)
        assert all(os.path.exists(path) for path in test_invoice_dirs.values())
        assert sample_invoice_data is not None

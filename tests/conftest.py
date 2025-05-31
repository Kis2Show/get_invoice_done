#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pytest configuration and fixtures for invoice OCR system tests
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import sqlite3
from unittest.mock import Mock

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp(prefix="invoice_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def test_db_path(test_data_dir):
    """Create a test database path"""
    return os.path.join(test_data_dir, "test_invoices.db")

@pytest.fixture(scope="function")
def test_db(test_db_path):
    """Create a test database for each test"""
    # Create test database
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            invoice_number TEXT,
            invoice_date TEXT,
            seller_name TEXT,
            seller_tax_number TEXT,
            buyer_name TEXT,
            buyer_tax_number TEXT,
            total_amount REAL,
            tax_amount REAL,
            pre_tax_amount REAL,
            items TEXT,
            raw_text TEXT,
            confidence REAL,
            processed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield test_db_path

    # Cleanup
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError:
            # File might be in use, skip cleanup
            pass

@pytest.fixture(scope="function")
def test_invoice_dirs(test_data_dir):
    """Create test invoice directories"""
    dirs = {
        'pdf': os.path.join(test_data_dir, 'invoices', 'pdf'),
        'imge': os.path.join(test_data_dir, 'invoices', 'imge'),
        'unrecognized': os.path.join(test_data_dir, 'invoices', 'unrecognized')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    yield dirs
    
    # Cleanup is handled by test_data_dir fixture

@pytest.fixture(scope="function")
def sample_pdf_content():
    """Sample PDF content for testing"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

@pytest.fixture(scope="function")
def sample_invoice_data():
    """Sample invoice data for testing"""
    return {
        'file_name': 'test_invoice.pdf',
        'file_path': '/test/path/test_invoice.pdf',
        'file_type': 'pdf',
        'invoice_number': '12345678',
        'invoice_date': '2024-01-15 00:00:00',
        'seller_name': '测试销售方公司',
        'seller_tax_number': '123456789012345678',
        'buyer_name': '宁波牧柏科技咨询有限公司',
        'buyer_tax_number': '91330225MA2J4X2M2B',
        'total_amount': 1000.00,
        'tax_amount': 130.00,
        'pre_tax_amount': 870.00,
        'items': '测试商品',
        'raw_text': '测试原始文本内容'
    }

@pytest.fixture(scope="function")
def mock_ocr_service():
    """Mock OCR service for testing"""
    mock_service = Mock()
    mock_service.extract_text.return_value = "测试OCR提取的文本"
    mock_service.process_invoice.return_value = {
        'invoice_number': '12345678',
        'invoice_date': '2024-01-15',
        'seller_name': '测试销售方',
        'buyer_name': '测试购买方',
        'total_amount': 1000.00,
        'confidence': 0.95
    }
    return mock_service

@pytest.fixture(scope="function")
def test_config():
    """Test configuration"""
    return {
        'DATABASE_URL': 'sqlite:///test_invoices.db',
        'INVOICE_DIR': './test_invoices',
        'LOG_LEVEL': 'DEBUG',
        'OCR_CONFIDENCE_THRESHOLD': 0.6,
        'MAX_FILE_SIZE': 10485760,
        'ALLOWED_EXTENSIONS': ['pdf', 'jpg', 'jpeg', 'png']
    }

@pytest.fixture(scope="function")
def test_app(test_db, test_config):
    """Create test FastAPI app"""
    try:
        from app.main import app
        from app.database import get_db
        
        # Override database dependency
        def override_get_db():
            conn = sqlite3.connect(test_db)
            try:
                yield conn
            finally:
                conn.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        yield app
        
        # Cleanup
        app.dependency_overrides.clear()
    except ImportError:
        # If app is not available, return a mock
        yield Mock()

@pytest.fixture(scope="function")
def test_client(test_app):
    """Create test client"""
    try:
        from fastapi.testclient import TestClient
        return TestClient(test_app)
    except ImportError:
        return Mock()

# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "ocr: OCR functionality tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "docker: Docker related tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add slow marker to tests that take more than 5 seconds
    for item in items:
        if "slow" not in item.keywords:
            if any(keyword in item.name.lower() for keyword in ["performance", "load", "stress"]):
                item.add_marker(pytest.mark.slow)

# Test reporting hooks (commented out - requires pytest-html plugin)
# def pytest_html_report_title(report):
#     """Customize HTML report title"""
#     report.title = "Invoice OCR System Test Report"

# def pytest_html_results_summary(prefix, summary, postfix):
#     """Customize HTML report summary"""
#     prefix.extend([
#         "<h2>Invoice OCR System Test Results</h2>",
#         f"<p>Test Environment: {os.environ.get('TEST_ENV', 'local')}</p>"
#     ])

# Cleanup hooks
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """Cleanup test files after session"""
    yield
    
    # Remove any test files that might have been created
    test_patterns = [
        "test_*.db",
        "test_*.log",
        "test_*.pdf",
        "test_*.jpg",
        "test_*.png"
    ]
    
    import glob
    for pattern in test_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except OSError:
                pass

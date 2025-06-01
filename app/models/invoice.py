from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True)
    file_name = Column(String, index=True)
    file_type = Column(String)  # 'image' or 'pdf'
    
    # 发票基本信息
    invoice_number = Column(String, index=True)
    invoice_date = Column(DateTime)
    
    # 金额信息
    total_amount = Column(Float)
    tax_amount = Column(Float)
    amount_without_tax = Column(Float)
    
    # 公司信息
    seller_name = Column(String)
    seller_tax_number = Column(String)
    buyer_name = Column(String)
    buyer_tax_number = Column(String)
    
    # OCR原始文本
    raw_text = Column(Text)
    
    # 处理状态
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class InvoiceResponse(BaseModel):
    id: int
    file_path: str
    file_name: str
    file_type: str
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    amount_without_tax: Optional[float] = None
    seller_name: Optional[str] = None
    seller_tax_number: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_tax_number: Optional[str] = None
    processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InvoiceFilter(BaseModel):
    invoice_number: Optional[str] = None
    seller_name: Optional[str] = None
    buyer_name: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    limit: Optional[int] = 100
    offset: Optional[int] = 0

class ProcessingStatus(BaseModel):
    total_files: int
    processed_files: int
    failed_files: int
    status: str


class InvoiceUpload(BaseModel):
    """发票上传响应模型"""
    file_name: str
    file_size: int
    file_type: str
    upload_status: str
    message: str


class InvoiceUploadResponse(BaseModel):
    """批量上传响应模型"""
    uploaded_files: List[InvoiceUpload]
    total_files: int
    successful_uploads: int
    failed_uploads: int
    message: str

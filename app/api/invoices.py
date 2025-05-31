from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
import os

from app.database import get_db
from app.models.invoice import Invoice, InvoiceResponse, InvoiceFilter, ProcessingStatus
from app.services.invoice_service import InvoiceService
from app.services.error_handling_service import ErrorHandlingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

@router.post("/process", response_model=ProcessingStatus)
async def process_invoices(db: Session = Depends(get_db)):
    """处理所有发票文件"""
    try:
        service = InvoiceService(db)
        stats = service.process_all_invoices()
        
        return ProcessingStatus(
            total_files=stats['total'],
            processed_files=stats['processed'],
            failed_files=stats['failed'],
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[InvoiceResponse])
async def get_invoices(
    invoice_number: Optional[str] = Query(None),
    seller_name: Optional[str] = Query(None),
    buyer_name: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    limit: Optional[int] = Query(100),
    offset: Optional[int] = Query(0),
    db: Session = Depends(get_db)
):
    """获取发票列表"""
    try:
        filter_params = InvoiceFilter(
            invoice_number=invoice_number,
            seller_name=seller_name,
            buyer_name=buyer_name,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        service = InvoiceService(db)
        invoices = service.get_invoices(filter_params)
        
        return [InvoiceResponse.model_validate(invoice) for invoice in invoices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """获取单个发票详情"""
    try:
        service = InvoiceService(db)
        invoice = service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return InvoiceResponse.model_validate(invoice)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear/all")
async def clear_all_invoices(db: Session = Depends(get_db)):
    """清空所有发票数据"""
    try:
        service = InvoiceService(db)
        count = service.clear_all_invoices()
        return {"message": f"Successfully cleared {count} invoices"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """删除发票"""
    try:
        service = InvoiceService(db)
        success = service.delete_invoice(invoice_id)

        if not success:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return {"message": "Invoice deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_statistics(db: Session = Depends(get_db)):
    """获取统计信息"""
    try:
        service = InvoiceService(db)
        stats = service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deduplicate")
async def remove_duplicates(db: Session = Depends(get_db)):
    """移除重复发票"""
    try:
        service = InvoiceService(db)
        removed_count = service.remove_duplicates()
        return {"message": f"Removed {removed_count} duplicate invoices"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{invoice_id}/raw_text")
async def get_invoice_raw_text(invoice_id: int, db: Session = Depends(get_db)):
    """获取发票的原始OCR文本"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return {
            "id": invoice.id,
            "file_name": invoice.file_name,
            "raw_text": invoice.raw_text or "No raw text available"
        }
    except Exception as e:
        logger.error(f"Error getting invoice raw text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/statistics")
async def get_error_statistics():
    """获取错误统计信息"""
    try:
        error_handler = ErrorHandlingService()
        stats = error_handler.get_error_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/errors/generate_report")
async def generate_error_report():
    """生成错误处理报告"""
    try:
        error_handler = ErrorHandlingService()
        report_path = error_handler.create_manual_review_report()
        return {
            "message": "错误报告生成成功",
            "report_path": report_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/unrecognized")
async def list_unrecognized_files():
    """列出未识别的发票文件"""
    try:
        error_handler = ErrorHandlingService()
        unrecognized_files = []

        # 遍历未识别目录
        for root, dirs, files in os.walk(error_handler.unrecognized_dir):
            for file in files:
                if not file.endswith(('.txt', '.json')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, error_handler.unrecognized_dir)
                    category = os.path.dirname(relative_path) if os.path.dirname(relative_path) else "root"

                    unrecognized_files.append({
                        "file_name": file,
                        "category": category,
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path),
                        "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })

        return {
            "total_count": len(unrecognized_files),
            "files": unrecognized_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/errors/delete_unrecognized")
async def delete_unrecognized_file(request: dict):
    """删除未识别的发票文件"""
    try:
        file_path = request.get("file_path")
        if not file_path:
            raise HTTPException(status_code=400, detail="文件路径不能为空")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        # 检查文件是否在未识别目录中
        error_handler = ErrorHandlingService()
        if not file_path.startswith(error_handler.unrecognized_dir):
            raise HTTPException(status_code=403, detail="只能删除未识别目录中的文件")

        # 删除文件
        os.remove(file_path)

        return {
            "message": "文件删除成功",
            "file_path": file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/errors/clear_all_unrecognized")
async def clear_all_unrecognized_files():
    """清空所有未识别的发票文件"""
    try:
        error_handler = ErrorHandlingService()
        deleted_count = 0

        # 遍历未识别目录，删除所有文件
        for root, dirs, files in os.walk(error_handler.unrecognized_dir):
            for file in files:
                if not file.endswith(('.txt', '.json')):  # 保留日志文件
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"删除文件失败: {file_path}, 错误: {e}")

        return {
            "message": f"成功清空 {deleted_count} 个未识别文件",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

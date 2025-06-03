#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime
import logging
import os

from app.services.invoice_service_minimal import InvoiceServiceMinimal
from app.services.file_service import file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

@router.post("/process")
async def process_invoices():
    """处理所有发票文件"""
    try:
        service = InvoiceServiceMinimal()
        stats = service.process_all_invoices()
        
        return {
            "total_files": stats['total'],
            "processed_files": stats['processed'],
            "failed_files": stats['failed'],
            "skipped_files": stats['skipped'],
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"处理发票失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理发票失败: {str(e)}")

@router.get("/")
async def get_invoices(
    limit: Optional[int] = Query(100, description="返回数量限制"),
    offset: Optional[int] = Query(0, description="偏移量")
):
    """获取发票列表"""
    try:
        service = InvoiceServiceMinimal()
        invoices = service.get_invoices(limit=limit, offset=offset)
        
        return {
            "invoices": invoices,
            "total": len(invoices),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"获取发票列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取发票列表失败: {str(e)}")

@router.get("/stats/summary")
async def get_statistics():
    """获取统计信息"""
    try:
        service = InvoiceServiceMinimal()
        stats = service.get_invoice_stats()
        return stats
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/export/csv")
async def export_to_csv(export_path: Optional[str] = Query(None)):
    """导出数据到CSV文件"""
    try:
        service = InvoiceServiceMinimal()
        file_path = service.export_to_csv(export_path)
        
        return {
            "message": "导出成功",
            "file_path": file_path,
            "download_url": f"/api/invoices/download/{os.path.basename(file_path)}"
        }
    except Exception as e:
        logger.error(f"导出CSV失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出CSV失败: {str(e)}")

@router.get("/csv/path")
async def get_csv_file_path():
    """获取CSV文件路径"""
    try:
        service = InvoiceServiceMinimal()
        file_path = service.get_csv_file_path()
        
        return {
            "csv_file_path": file_path,
            "exists": os.path.exists(file_path),
            "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
    except Exception as e:
        logger.error(f"获取CSV文件路径失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取CSV文件路径失败: {str(e)}")

@router.post("/upload")
async def upload_invoices(files: List[UploadFile] = File(...)):
    """上传发票文件"""
    try:
        service = InvoiceServiceMinimal()
        uploaded_files = []
        successful_uploads = 0
        failed_uploads = 0

        for upload_file in files:
            # 保存文件
            result = file_service.save_uploaded_file(upload_file)

            upload_info = {
                "file_name": upload_file.filename,
                "file_size": result['file_size'],
                "file_type": result['file_type'] or 'unknown',
                "upload_status": 'success' if result['success'] else 'failed',
                "message": result['message']
            }

            # 如果文件保存成功，尝试处理
            if result['success']:
                try:
                    process_result = service.upload_invoice_file(
                        result['file_path'], 
                        result['file_type']
                    )
                    upload_info.update(process_result)
                    successful_uploads += 1
                except Exception as e:
                    upload_info['message'] += f" (处理失败: {str(e)})"
                    failed_uploads += 1
            else:
                failed_uploads += 1

            uploaded_files.append(upload_info)

        return {
            "uploaded_files": uploaded_files,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "message": f"上传完成: 成功 {successful_uploads} 个，失败 {failed_uploads} 个"
        }

    except Exception as e:
        logger.error(f"上传发票文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.delete("/files/{file_name}")
async def delete_invoice_file(file_name: str):
    """删除发票文件（同时删除文件和CSV记录）"""
    try:
        # 尝试在PDF目录中查找
        pdf_path = file_service.pdf_dir / file_name
        image_path = file_service.image_dir / file_name

        file_path = None
        if pdf_path.exists():
            file_path = str(pdf_path)
        elif image_path.exists():
            file_path = str(image_path)
        else:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 删除文件
        result = file_service.delete_file(file_path)

        if result['success']:
            # 同时删除CSV中对应的记录
            service = InvoiceServiceMinimal()
            deleted = service.delete_invoice_by_file_path(file_path)

            message = f"文件删除成功"
            if deleted:
                message += f"，同时删除了CSV记录"

            return {
                "message": message,
                "file_name": file_name,
                "csv_record_deleted": deleted
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.get("/files/list")
async def list_invoice_files():
    """列出所有发票文件"""
    try:
        files = file_service.list_files()

        # 按类型分组
        pdf_files = [f for f in files if f['file_type'] == 'pdf']
        image_files = [f for f in files if f['file_type'] == 'image']

        return {
            "total_files": len(files),
            "pdf_files": len(pdf_files),
            "image_files": len(image_files),
            "files": {
                "pdf": pdf_files,
                "images": image_files
            }
        }

    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")

@router.get("/processing/status")
async def get_processing_status():
    """获取处理状态"""
    try:
        service = InvoiceServiceMinimal()
        status = service.get_processing_status()
        return status
    except Exception as e:
        logger.error(f"获取处理状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        service = InvoiceServiceMinimal()
        csv_path = service.get_csv_file_path()
        
        return {
            "status": "healthy",
            "storage_type": "csv",
            "csv_file_exists": os.path.exists(csv_path),
            "dependencies": {
                "pandas": False,  # 不使用pandas
                "numpy": False,   # 不使用numpy
                "easyocr": True,
                "pdfplumber": True
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

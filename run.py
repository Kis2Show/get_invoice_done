#!/usr/bin/env python3
"""
发票识别管理系统启动脚本
"""
import os
import sys
import subprocess
import logging

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import easyocr
        import PIL
        print("✓ 核心依赖已安装")

        # 检查存储类型
        storage_type = os.getenv('STORAGE_TYPE', 'excel')
        if storage_type == 'csv':
            print("✓ 使用CSV存储模式（无pandas依赖）")
        else:
            try:
                import pandas
                import openpyxl
                print("✓ Excel存储依赖可用")
            except ImportError:
                print("⚠ Excel存储依赖不可用，将使用CSV模式")
                os.environ['STORAGE_TYPE'] = 'csv'

        # 检查PDF处理能力
        pdf_available = False
        try:
            import fitz
            pdf_available = True
            print("✓ PyMuPDF可用")
        except ImportError:
            try:
                import pdfplumber
                pdf_available = True
                print("✓ pdfplumber可用")
            except ImportError:
                print("⚠ PDF处理库不可用，将无法处理PDF文件")

        # 检查OpenCV（可选）
        try:
            import cv2
            print("✓ OpenCV可用")
        except ImportError:
            print("ℹ OpenCV不可用，使用EasyOCR内置图像处理")

        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements-micro.txt")
        return False

def check_directories():
    """检查目录结构"""
    required_dirs = [
        "invoices",
        "invoices/imge", 
        "invoices/pdf",
        "app",
        "app/static"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"✗ 目录不存在: {dir_path}")
            return False
        print(f"✓ 目录存在: {dir_path}")
    
    return True

def count_invoice_files():
    """统计发票文件数量"""
    image_count = 0
    pdf_count = 0
    
    if os.path.exists("invoices/imge"):
        for file in os.listdir("invoices/imge"):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')):
                image_count += 1
    
    if os.path.exists("invoices/pdf"):
        for file in os.listdir("invoices/pdf"):
            if file.lower().endswith('.pdf'):
                pdf_count += 1
    
    print(f"📄 发现发票文件: 图片 {image_count} 个, PDF {pdf_count} 个")
    return image_count + pdf_count

def main():
    print("🚀 启动发票识别管理系统")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查目录
    if not check_directories():
        sys.exit(1)
    
    # 统计文件
    total_files = count_invoice_files()
    if total_files == 0:
        print("⚠️  警告: 未发现发票文件，请将发票文件放入 invoices/imge 或 invoices/pdf 目录")
    
    print("\n🌐 启动Web服务器...")
    print("访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 启动服务器
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 服务已停止")

if __name__ == "__main__":
    main()

@echo off
echo 🚀 上传发票OCR系统到GitHub
echo ================================

REM 检查Git是否已安装
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git未安装，请先安装Git
    pause
    exit /b 1
)

echo ✅ Git已安装

REM 检查是否已初始化Git仓库
if not exist .git (
    echo 🔧 初始化Git仓库...
    git init
    echo ✅ Git仓库已初始化
) else (
    echo ✅ Git仓库已存在
)

REM 添加远程仓库
echo 🔗 添加远程仓库...
git remote add origin https://github.com/Kis2Show/get_invoice_done.git 2>nul
if errorlevel 1 (
    echo ℹ️ 远程仓库已存在，更新URL...
    git remote set-url origin https://github.com/Kis2Show/get_invoice_done.git
)
echo ✅ 远程仓库配置完成

REM 添加所有文件
echo 📁 添加所有文件...
git add .
echo ✅ 文件添加完成

REM 创建提交
echo 💬 创建提交...
git commit -m "🎉 Initial commit: Complete Invoice OCR System with CI/CD

✨ Features:
- FastAPI-based invoice OCR system with web interface
- Support for PDF and image invoice processing
- SQLite database with comprehensive data management
- Docker containerization with multi-stage build
- Complete GitHub Actions CI/CD pipeline
- Automatic Docker Hub image publishing (kis2show/invoice-ocr-system)
- Production-ready configuration and deployment scripts
- Comprehensive testing framework with coverage reporting
- Security scanning integration (Trivy, Bandit)
- Automated dependency updates and release management

🐳 Docker Features:
- Multi-architecture support (linux/amd64, linux/arm64)
- Optimized production Dockerfile with non-root user
- Docker Compose orchestration with health checks
- Automated image building and publishing

🔄 CI/CD Pipeline:
- Automated testing and code coverage (pytest, codecov)
- Security vulnerability scanning
- Multi-environment deployment support
- Automated releases with changelog generation
- Docker image auto-build and push to Docker Hub

🔒 Security & Production:
- Non-root container execution
- Comprehensive security scanning
- Production environment configuration
- Secrets management and environment variables
- Complete ignore files for development artifacts

📦 Ready for immediate production deployment!"

if errorlevel 1 (
    echo ⚠️ 提交失败，可能没有变更或存在问题
) else (
    echo ✅ 提交创建成功
)

REM 推送到GitHub
echo 🚀 推送到GitHub...
git push -u origin main

if errorlevel 1 (
    echo ❌ 推送失败，请检查网络连接和权限
    echo 💡 如果需要认证，请配置Personal Access Token
    pause
    exit /b 1
) else (
    echo ✅ 推送成功！
)

echo.
echo 🎉 上传完成！
echo 📦 仓库地址: https://github.com/Kis2Show/get_invoice_done
echo 🐳 Docker镜像: kis2show/invoice-ocr-system
echo 🔄 GitHub Actions将自动开始构建...
echo.
echo 📋 下一步操作：
echo 1. 访问 https://github.com/Kis2Show/get_invoice_done/actions 查看构建状态
echo 2. 访问 https://hub.docker.com/r/kis2show/invoice-ocr-system 查看Docker镜像
echo 3. 创建第一个发布版本: git tag v1.0.0 && git push origin v1.0.0
echo.

pause

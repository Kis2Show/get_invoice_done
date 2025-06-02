# 🚀 发票OCR系统部署指南

## 📦 Release v1.0.1

### 🎉 主要特性
- ✅ 完整的发票OCR识别功能(PDF和图片)
- ✅ Web界面和REST API
- ✅ Docker容器化部署
- ✅ 完善的CI/CD流程
- ✅ 企业级安全扫描

## 🐳 Docker部署 (推荐)

### 快速启动
```bash
# 拉取最新镜像
docker pull kis2show/get_invoice_done:v1.0.1

# 运行容器
docker run -d \
  --name invoice-ocr \
  -p 8000:8000 \
  -v $(pwd)/invoices:/app/invoices \
  kis2show/get_invoice_done:v1.0.1

# 访问应用
curl http://localhost:8000/health
```

### 使用Docker Compose
```yaml
version: '3.8'
services:
  invoice-ocr:
    image: kis2show/get_invoice_done:v1.0.1
    ports:
      - "8000:8000"
    volumes:
      - ./invoices:/app/invoices
      - ./data:/app/data
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
```

## 📋 源码部署

### 环境要求
- Python 3.9+
- pip 21.0+

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/Kis2Show/get_invoice_done.git
cd get_invoice_done

# 切换到release版本
git checkout v1.0.1

# 安装依赖
pip install -r requirements.txt

# 启动应用
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔧 配置说明

### 环境变量
```bash
# 应用配置
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./data/invoices.db

# 文件路径配置
INVOICE_IMAGE_DIR=./invoices/imge
INVOICE_PDF_DIR=./invoices/pdf
```

### 目录结构
```
project/
├── invoices/
│   ├── imge/          # 图片发票目录
│   └── pdf/           # PDF发票目录
├── data/              # 数据库文件
└── logs/              # 日志文件
```

## 🌐 API使用

### 健康检查
```bash
curl http://localhost:8000/health
```

### 上传发票
```bash
curl -X POST \
  -F "files=@invoice.pdf" \
  http://localhost:8000/api/invoices/upload
```

### 处理发票
```bash
curl -X POST http://localhost:8000/api/invoices/process
```

### 查询发票
```bash
curl http://localhost:8000/api/invoices/
```

## 🛡️ 安全配置

### 生产环境建议
1. 使用HTTPS
2. 配置防火墙
3. 定期更新镜像
4. 监控日志文件
5. 备份数据库

### 文件权限
```bash
# 设置正确的文件权限
chmod 755 invoices/
chmod 644 invoices/imge/*
chmod 644 invoices/pdf/*
```

## 📊 监控和维护

### 日志查看
```bash
# Docker容器日志
docker logs invoice-ocr

# 应用日志文件
tail -f logs/app.log
```

### 性能监控
```bash
# 检查容器状态
docker stats invoice-ocr

# 检查磁盘使用
du -sh invoices/ data/
```

## 🔄 更新升级

### Docker更新
```bash
# 停止旧容器
docker stop invoice-ocr
docker rm invoice-ocr

# 拉取新镜像
docker pull kis2show/get_invoice_done:latest

# 启动新容器
docker run -d \
  --name invoice-ocr \
  -p 8000:8000 \
  -v $(pwd)/invoices:/app/invoices \
  kis2show/get_invoice_done:latest
```

### 源码更新
```bash
# 拉取最新代码
git pull origin master

# 更新依赖
pip install -r requirements.txt

# 重启应用
systemctl restart invoice-ocr
```

## 🆘 故障排除

### 常见问题
1. **端口占用**: 检查8000端口是否被占用
2. **权限问题**: 确保Docker有访问挂载目录的权限
3. **内存不足**: 建议至少2GB内存
4. **OCR识别失败**: 检查图片质量和格式

### 联系支持
- GitHub Issues: https://github.com/Kis2Show/get_invoice_done/issues
- 作者: Kis2show
- 邮箱: 通过GitHub联系

---
*发票OCR系统 v1.0.1 - 生产就绪版本*

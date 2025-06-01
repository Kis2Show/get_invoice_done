# 🧾 发票OCR识别管理系统

[![CI/CD](https://github.com/Kis2Show/get_invoice_done/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/Kis2Show/get_invoice_done/actions)
[![Docker](https://github.com/Kis2Show/get_invoice_done/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)](https://github.com/Kis2Show/get_invoice_done/actions)
[![Docker Hub](https://img.shields.io/docker/pulls/kis2show/get_invoice_done)](https://hub.docker.com/r/kis2show/get_invoice_done)
[![License](https://img.shields.io/github/license/Kis2Show/get_invoice_done)](LICENSE)

基于FastAPI和EasyOCR的现代化发票识别管理系统，支持PDF和图片格式的发票自动识别、信息提取、数据管理和Web界面操作。

## ✨ 功能特性

### 🔍 智能OCR识别
- **双引擎支持**:
  - **图片发票**: 使用EasyOCR引擎，支持中文发票的高精度识别
  - **PDF发票**: 使用PyMuPDF直接提取文本，速度更快、精度更高
- **多格式支持**: 支持PDF、JPG、PNG、BMP、TIFF等格式
- **智能布局分析**: 自动识别发票布局和字段位置
- **错误处理**: 智能处理识别失败的发票文件
- **文件上传**: 支持用户上传发票文件进行识别

### 📊 数据管理
- **信息提取**: 自动提取发票号码、金额、日期、公司信息等关键字段
- **数据验证**: 智能验证提取的数据准确性
- **去重功能**: 基于发票号码和代码自动去除重复记录
- **筛选排序**: 支持多维度筛选和排序功能

### 🌐 现代化界面
- **响应式设计**: 支持桌面和移动设备
- **实时反馈**: 处理进度实时显示
- **直观操作**: 简洁易用的用户界面
- **数据可视化**: 统计图表和汇总信息

### 🐳 DevOps集成
- **容器化部署**: Docker多架构支持 (amd64/arm64)
- **CI/CD流水线**: GitHub Actions自动构建和部署
- **自动化测试**: 完整的测试覆盖和质量检查
- **安全扫描**: 自动安全漏洞检测

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI (高性能异步Web框架)
- **OCR引擎**:
  - **EasyOCR**: 图片发票识别 (支持中英文混合识别)
  - **PyMuPDF**: PDF文本直接提取 (高效、准确)
- **数据库**: SQLite (轻量级关系数据库)
- **异步处理**: asyncio (异步任务处理)
- **文件处理**: 支持多种格式的发票文件上传和管理

### 前端技术
- **界面**: HTML5 + CSS3 + JavaScript
- **框架**: Bootstrap 5 (响应式UI框架)
- **图标**: Font Awesome (矢量图标库)
- **交互**: 原生JavaScript (无重型框架依赖)

### DevOps工具
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **代码质量**: pytest + coverage
- **安全扫描**: Trivy + Bandit
- **多架构**: linux/amd64, linux/arm64

## 🚀 快速开始

### 方法1: 使用Docker镜像 (最简单)

```bash
# 拉取最新镜像
docker pull kis2show/get_invoice_done:latest

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/invoices:/app/invoices \
  --name invoice-ocr \
  kis2show/get_invoice_done:latest

# 访问Web界面
open http://localhost:8000
```

### 方法2: 使用Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/Kis2Show/get_invoice_done.git
cd get_invoice_done

# 2. 配置环境变量
cp .env.production .env
# 编辑 .env 文件，更新 SECRET_KEY 和 CORS_ORIGINS

# 3. 启动服务
docker-compose up -d

# 4. 访问Web界面
open http://localhost:8000
```

### 方法3: 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/Kis2Show/get_invoice_done.git
cd get_invoice_done

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir -p data logs invoices/pdf invoices/imge invoices/unrecognized

# 5. 启动开发服务器
python run.py
```

### 📁 目录准备

确保发票文件已放置在正确位置：
```
invoices/
├── pdf/              # PDF格式发票
├── imge/             # 图片格式发票 (jpg, png, bmp, tiff)
└── unrecognized/     # 识别失败的文件 (自动创建)
```

## 使用说明

### 1. 发票处理方式

#### 方式一：本地文件扫描
- 将发票文件放入`/invoices`目录下的对应子目录：
  - PDF文件：`/invoices/pdf/`
  - 图片文件：`/invoices/imge/`
- 点击"处理发票"按钮，系统会自动扫描并识别所有发票文件

#### 方式二：在线上传
- 点击"上传发票"按钮
- 选择一个或多个发票文件（支持PDF、JPG、PNG、BMP、TIFF格式）
- 系统会自动保存文件并进行OCR识别
- 上传完成后可立即查看识别结果

### 2. 查看和筛选
- 在发票列表中查看所有已处理的发票
- 使用筛选条件进行精确搜索:
  - 发票号码
  - 销售方/购买方名称
  - 金额范围
  - 日期范围
- 支持多种排序方式

### 3. 发票详情
- 点击发票卡片查看详细信息
- 包含完整的发票信息和原始识别文本
- 支持删除操作

### 4. 数据管理
- 去重功能: 基于发票号码和发票代码自动去除重复记录
- 统计信息: 实时显示发票数量、金额汇总等统计数据

## 📚 API文档

启动服务后，访问以下地址查看完整的API文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 🔗 主要API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/invoices/process` | 处理所有发票文件 |
| `GET` | `/api/invoices/` | 获取发票列表(支持筛选) |
| `GET` | `/api/invoices/{id}` | 获取单个发票详情 |
| `DELETE` | `/api/invoices/{id}` | 删除发票 |
| `POST` | `/api/invoices/upload` | **上传发票文件** |
| `GET` | `/api/invoices/files/list` | **列出所有文件** |
| `DELETE` | `/api/invoices/files/{file_name}` | **删除指定文件** |
| `POST` | `/api/invoices/deduplicate` | 去重操作 |
| `GET` | `/api/invoices/stats/summary` | 获取统计信息 |
| `GET` | `/api/invoices/errors/statistics` | 获取错误统计 |
| `GET` | `/health` | 健康检查端点 |

### 📝 API使用示例

```bash
# 处理发票
curl -X POST "http://localhost:8000/api/invoices/process"

# 上传发票文件
curl -X POST "http://localhost:8000/api/invoices/upload" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.jpg"

# 获取发票列表
curl "http://localhost:8000/api/invoices/?limit=10&offset=0"

# 列出所有文件
curl "http://localhost:8000/api/invoices/files/list"

# 删除指定文件
curl -X DELETE "http://localhost:8000/api/invoices/files/invoice.pdf"

# 获取统计信息
curl "http://localhost:8000/api/invoices/stats/summary"

# 健康检查
curl "http://localhost:8000/health"
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/invoices.db` |
| `SECRET_KEY` | 应用密钥 | `your-secret-key-here` |
| `CORS_ORIGINS` | 允许的跨域源 | `*` |
| `MAX_FILE_SIZE` | 最大文件大小 | `10485760` (10MB) |
| `OCR_CONFIDENCE_THRESHOLD` | OCR置信度阈值 | `0.7` |
| `WORKERS` | 工作进程数 | `4` |

### 生产环境配置

```bash
# 复制生产环境配置模板
cp .env.production .env

# 编辑配置文件
nano .env
```

**重要**: 生产环境请务必修改以下配置：
- `SECRET_KEY`: 生成强密钥
- `CORS_ORIGINS`: 设置允许的域名
- `DEBUG`: 设置为 `false`

### 📁 项目目录结构

```
get_invoice_done/
├── 📁 .github/workflows/      # GitHub Actions CI/CD
│   ├── ci-cd.yml             # 完整CI/CD流水线
│   ├── docker-build.yml      # Docker构建工作流
│   ├── release.yml           # 发布管理工作流
│   └── dependency-update.yml # 依赖更新工作流
├── 📁 app/                   # FastAPI应用代码
│   ├── 📁 api/               # API路由模块
│   ├── 📁 models/            # 数据模型定义
│   ├── 📁 services/          # 业务逻辑服务
│   ├── 📁 static/            # 静态文件(HTML/CSS/JS)
│   ├── database.py           # 数据库配置
│   └── main.py              # FastAPI主应用
├── 📁 data/                  # 数据存储目录
├── 📁 invoices/              # 发票文件目录
│   ├── 📁 pdf/               # PDF格式发票
│   ├── 📁 imge/              # 图片格式发票
│   └── 📁 unrecognized/      # 识别失败文件
├── 📁 logs/                  # 应用日志目录
├── 📁 tests/                 # 测试代码
├── 🐳 Dockerfile             # Docker镜像定义
├── 🐳 docker-compose.yml     # Docker编排配置
├── ⚙️ .env.production        # 生产环境配置
├── ⚙️ .env.example           # 环境变量示例
├── 🚀 deploy.sh/.bat         # 部署脚本
├── 📦 requirements.txt       # Python依赖
├── 🐍 run.py                 # 应用启动脚本
└── 📚 README.md              # 项目说明文档
```

## ⚠️ 注意事项

### 📋 使用要求
1. **文件格式**: 确保发票文件清晰可读，避免模糊或损坏的文件
2. **中文支持**: 系统专门针对中国大陆发票格式进行优化
3. **网络连接**: 首次运行时EasyOCR会下载模型文件，请确保网络连接正常
4. **存储空间**: 数据库和日志文件存储在`./data`和`./logs`目录下，请定期备份

### 🔒 安全建议
1. **生产部署**: 务必修改默认的SECRET_KEY
2. **CORS配置**: 生产环境请设置具体的允许域名
3. **文件权限**: 确保发票文件目录有适当的读写权限
4. **定期更新**: 关注依赖包安全更新

## 🔧 故障排除

### 常见问题及解决方案

#### 1. OCR识别精度低
```bash
# 检查文件质量
- 确保发票图片清晰度足够 (建议300DPI以上)
- 检查文件是否损坏或格式不支持
- 尝试重新扫描或拍摄发票

# 调整OCR参数
- 修改 OCR_CONFIDENCE_THRESHOLD 环境变量
- 检查发票是否为标准格式
```

#### 2. Docker启动失败
```bash
# 检查端口占用
netstat -tulpn | grep :8000

# 查看容器日志
docker-compose logs -f

# 重新构建镜像
docker-compose build --no-cache
```

#### 3. 文件无法识别
```bash
# 检查文件权限
ls -la invoices/

# 查看应用日志
docker-compose logs app

# 检查支持的文件格式
curl http://localhost:8000/health
```

#### 4. 数据库问题
```bash
# 检查数据库文件
ls -la data/

# 重置数据库 (谨慎操作)
rm data/invoices.db
docker-compose restart
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. **Fork** 本仓库
2. **创建** 特性分支 (`git checkout -b feature/AmazingFeature`)
3. **提交** 更改 (`git commit -m 'Add some AmazingFeature'`)
4. **推送** 到分支 (`git push origin feature/AmazingFeature`)
5. **创建** Pull Request

### 贡献类型
- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🧪 测试用例
- 🎨 UI/UX改进
- 🔧 性能优化

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)。

## 👨‍💻 作者

**Kis2Show**
- GitHub: [@Kis2Show](https://github.com/Kis2Show)
- 项目链接: [https://github.com/Kis2Show/get_invoice_done](https://github.com/Kis2Show/get_invoice_done)

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - 易用的OCR库
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF处理库
- [Bootstrap](https://getbootstrap.com/) - 前端UI框架

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**

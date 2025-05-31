# 发票识别管理系统

基于PaddleOCR的中国大陆发票识别和管理系统，支持图片和PDF格式的发票自动识别、信息提取、排序、去重和筛选功能。

## 功能特性

- 🔍 **智能识别**: 使用PaddleOCR引擎，支持中文发票的高精度识别
- 📄 **多格式支持**: 支持图片(JPG, PNG, BMP, TIFF)和PDF格式的发票
- 🏷️ **信息提取**: 自动提取发票号码、金额、日期、公司信息等关键字段
- 🔄 **数据管理**: 支持排序、去重、筛选等数据处理功能
- 🌐 **Web界面**: 现代化的Web用户界面，支持响应式设计
- 🐳 **容器化**: 支持Docker部署，跨平台运行
- 📊 **统计分析**: 提供发票统计和汇总信息

## 技术栈

- **后端**: Python + FastAPI
- **OCR引擎**: PaddleOCR
- **PDF处理**: PyMuPDF
- **数据库**: SQLite
- **前端**: HTML + JavaScript + Bootstrap
- **容器化**: Docker + Docker Compose

## 快速开始

### 使用Docker Compose (推荐)

1. 克隆项目并进入目录:
```bash
git clone <repository-url>
cd get_invoice_done
```

2. 确保发票文件已放置在正确位置:
```
invoices/
├── imge/     # 图片格式发票
└── pdf/      # PDF格式发票
```

3. 启动服务:
```bash
docker-compose up -d
```

4. 访问Web界面:
```
http://localhost:8000
```

### 本地开发

1. 安装Python依赖:
```bash
pip install -r requirements.txt
```

2. 启动开发服务器:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 使用说明

### 1. 处理发票
- 点击"处理发票"按钮，系统会自动扫描`/invoices`目录下的所有发票文件
- 系统会使用OCR技术识别发票内容并提取关键信息
- 处理完成后会显示统计信息

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

## API文档

启动服务后，访问以下地址查看API文档:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

- `POST /api/invoices/process` - 处理所有发票文件
- `GET /api/invoices/` - 获取发票列表(支持筛选)
- `GET /api/invoices/{id}` - 获取单个发票详情
- `DELETE /api/invoices/{id}` - 删除发票
- `POST /api/invoices/deduplicate` - 去重操作
- `GET /api/invoices/stats/summary` - 获取统计信息

## 配置说明

### 环境变量

- `DATABASE_URL`: 数据库连接字符串 (默认: sqlite:///./invoices.db)
- `PYTHONPATH`: Python路径 (默认: /app)

### 目录结构

```
get_invoice_done/
├── app/                    # 应用代码
│   ├── api/               # API路由
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── static/            # 静态文件
│   ├── database.py        # 数据库配置
│   └── main.py           # 主应用
├── invoices/              # 发票文件目录
│   ├── imge/             # 图片发票
│   └── pdf/              # PDF发票
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker配置
├── docker-compose.yml    # Docker Compose配置
└── README.md             # 项目说明
```

## 注意事项

1. **文件格式**: 确保发票文件清晰可读，避免模糊或损坏的文件
2. **中文支持**: 系统专门针对中国大陆发票格式进行优化
3. **性能**: 首次运行时PaddleOCR会下载模型文件，请确保网络连接正常
4. **存储**: 数据库文件存储在`./data`目录下，请定期备份

## 故障排除

### 常见问题

1. **OCR识别精度低**:
   - 确保发票图片清晰度足够
   - 检查文件是否损坏
   - 尝试重新扫描或拍摄发票

2. **Docker启动失败**:
   - 检查端口8000是否被占用
   - 确保Docker和Docker Compose已正确安装
   - 查看容器日志: `docker-compose logs`

3. **文件无法识别**:
   - 确认文件格式是否支持
   - 检查文件权限
   - 查看应用日志获取详细错误信息

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

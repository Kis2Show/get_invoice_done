# 多阶段构建 - 构建阶段
FROM python:3.9-slim as builder

# 构建参数
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 安装构建依赖（精简版本）
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    # 基础编译工具
    cmake \
    make \
    pkg-config \
    # 图像处理库
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    # OpenCV最小依赖
    libglib2.0-0 \
    libgomp1 \
    libgcc-s1 \
    # 工具
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 复制生产环境依赖文件
COPY requirements-production.txt .

# 升级pip并安装Python依赖到用户目录
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-production.txt && \
    # 清理pip缓存
    pip cache purge

# 生产阶段 - 使用slim基础镜像
FROM python:3.9-slim as production

# 复制构建参数到生产阶段
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 设置生产环境标签
LABEL org.opencontainers.image.created=${BUILDTIME}
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.revision=${REVISION}
LABEL org.opencontainers.image.title="Invoice OCR System"
LABEL org.opencontainers.image.description="基于FastAPI和EasyOCR的发票识别管理系统"
LABEL org.opencontainers.image.source="https://github.com/Kis2Show/get_invoice_done"
LABEL org.opencontainers.image.licenses="MIT"

# 安装运行时依赖（精简版本）
RUN apt-get update && apt-get install -y \
    # 最小运行时依赖
    libgomp1 \
    libgcc-s1 \
    libjpeg62-turbo \
    libfreetype6 \
    libglib2.0-0 \
    # 健康检查工具
    curl \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码（只复制必要文件）
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser run.py ./

# 创建必要的目录并设置权限（一次性操作）
RUN mkdir -p /app/data /app/invoices/pdf /app/invoices/imge /app/invoices/unrecognized /app/logs && \
    chown -R appuser:appuser /app

# 暴露端口
EXPOSE 8000

# 切换到非root用户
USER appuser

# 设置环境变量（优化版本）
ENV PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONPATH=/app \
    DATABASE_URL=sqlite:///./data/invoices.db \
    INVOICE_DIR=/app/invoices \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # OCR优化设置
    EASYOCR_MODULE_PATH=/home/appuser/.EasyOCR \
    OMP_NUM_THREADS=1

# 健康检查（使用更轻量的检查）
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（生产模式）
CMD ["python", "run.py"]

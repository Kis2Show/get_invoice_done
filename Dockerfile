# 多阶段构建 - 构建阶段
FROM python:3.9-alpine as builder

# 构建参数
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 安装构建依赖（Alpine包管理器）
RUN apk add --no-cache \
    build-base \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    libffi-dev \
    openssl-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev

# 设置工作目录
WORKDIR /app

# 复制生产环境依赖文件
COPY requirements-production.txt .

# 升级pip并安装Python依赖到用户目录
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-production.txt && \
    # 清理pip缓存
    pip cache purge

# 生产阶段 - 使用更小的基础镜像
FROM python:3.9-alpine as production

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

# 安装运行时依赖（Alpine版本，更小）
RUN apk add --no-cache \
    libstdc++ \
    libgomp \
    libgcc \
    libjpeg-turbo \
    libpng \
    freetype \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# 创建非root用户（Alpine方式）
RUN addgroup -g 1000 appuser && \
    adduser -D -s /bin/sh -u 1000 -G appuser appuser

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
    EASYOCR_MODULE_PATH=/home/appuser/.EasyOCR

# 健康检查（使用更轻量的检查）
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（生产模式）
CMD ["python", "run.py"]

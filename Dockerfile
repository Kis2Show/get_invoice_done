# 多阶段构建 - 构建阶段
FROM python:3.9-slim as builder

# 构建参数
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 设置构建时标签
LABEL org.opencontainers.image.created=${BUILDTIME}
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.revision=${REVISION}
LABEL org.opencontainers.image.title="Invoice OCR System"
LABEL org.opencontainers.image.description="基于FastAPI和EasyOCR的发票识别管理系统"
LABEL org.opencontainers.image.source="https://github.com/Kis2Show/get_invoice_done"
LABEL org.opencontainers.image.licenses="MIT"

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到用户目录
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产阶段
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

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser run.py ./

# 创建必要的目录
RUN mkdir -p /app/data \
    && mkdir -p /app/invoices/pdf \
    && mkdir -p /app/invoices/imge \
    && mkdir -p /app/invoices/unrecognized \
    && mkdir -p /app/logs

# 复制发票目录（如果存在）
COPY --chown=appuser:appuser invoices/ ./invoices/

# 设置目录权限
RUN chown -R appuser:appuser /app

# 暴露端口
EXPOSE 8000

# 切换到非root用户
USER appuser

# 设置Python路径
ENV PATH="/home/appuser/.local/bin:$PATH"

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/invoices.db
ENV INVOICE_DIR=/app/invoices
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（生产模式，不使用reload）
CMD ["python", "run.py"]

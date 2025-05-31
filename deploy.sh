#!/bin/bash

# 🚀 发票OCR系统Docker部署脚本
# 镜像: kis2show/get_invoice_done:latest | 用户权限: 100:100
# 使用方法: ./deploy.sh [start|stop|restart|pull|logs|status]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="invoice-ocr-system"
COMPOSE_FILE="docker-compose.yml"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_info "Docker环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p data
    mkdir -p invoices/pdf
    mkdir -p invoices/imge
    mkdir -p invoices/unrecognized
    mkdir -p logs
    
    log_success "目录创建完成"
}

# 拉取最新镜像
pull_image() {
    log_info "拉取最新镜像: kis2show/get_invoice_done:latest..."

    docker pull kis2show/get_invoice_done:latest

    log_success "镜像拉取完成"
}

# 设置目录权限
setup_permissions() {
    log_info "设置目录权限 (用户ID: 100)..."

    # 检查是否为root用户或有sudo权限
    if [[ $EUID -eq 0 ]]; then
        chown -R 100:100 data invoices logs 2>/dev/null || true
        chmod -R 755 data invoices logs 2>/dev/null || true
        log_success "权限设置完成 (root用户)"
    elif sudo -n true 2>/dev/null; then
        sudo chown -R 100:100 data invoices logs 2>/dev/null || true
        sudo chmod -R 755 data invoices logs 2>/dev/null || true
        log_success "权限设置完成 (sudo)"
    else
        log_warning "无法自动设置权限，请手动执行:"
        echo "  sudo chown -R 100:100 data invoices logs"
        echo "  sudo chmod -R 755 data invoices logs"
    fi
}

# 启动服务
start_service() {
    log_info "启动发票OCR系统..."

    create_directories
    setup_permissions

    # 启动主服务
    docker-compose up -d invoice-ocr

    log_success "服务启动完成"
    log_info "🌐 Web界面地址: http://localhost:8000"
    log_info "📚 API文档: http://localhost:8000/docs"
    log_info "💚 健康检查: http://localhost:8000/health"

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    check_health
}

# 启动服务（包含管理界面）
start_with_admin() {
    log_info "启动发票OCR系统（包含管理界面）..."
    
    create_directories
    
    # 启动所有服务
    docker-compose --profile admin up -d
    
    log_success "服务启动完成"
    log_info "Web界面地址: http://localhost:8000"
    log_info "数据库管理界面: http://localhost:8080"
    log_info "健康检查: http://localhost:8000/health"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    check_health
}

# 停止服务
stop_service() {
    log_info "停止发票OCR系统..."
    
    docker-compose down
    
    log_success "服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启发票OCR系统..."
    
    stop_service
    sleep 2
    start_service
}

# 查看日志
show_logs() {
    log_info "显示服务日志..."
    
    docker-compose logs -f invoice-ocr
}

# 检查服务状态
check_status() {
    log_info "检查服务状态..."
    
    echo "=== Docker容器状态 ==="
    docker-compose ps
    
    echo -e "\n=== 服务健康状态 ==="
    check_health
    
    echo -e "\n=== 资源使用情况 ==="
    docker stats --no-stream $(docker-compose ps -q)
}

# 健康检查
check_health() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "服务健康检查通过"
            
            # 获取服务信息
            local health_info=$(curl -s http://localhost:8000/health)
            echo "健康状态: $health_info"
            return 0
        fi
        
        log_warning "健康检查失败，重试中... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "服务健康检查失败"
    return 1
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止并删除容器
    docker-compose down --volumes --remove-orphans
    
    # 删除镜像（可选）
    read -p "是否删除Docker镜像? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down --rmi all
        log_success "镜像已删除"
    fi
    
    log_success "清理完成"
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    
    local backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 备份数据库
    if [ -f "data/invoices.db" ]; then
        cp data/invoices.db "$backup_dir/"
        log_success "数据库备份完成"
    fi
    
    # 备份发票文件
    if [ -d "invoices" ]; then
        cp -r invoices "$backup_dir/"
        log_success "发票文件备份完成"
    fi
    
    log_success "备份完成: $backup_dir"
}

# 显示帮助信息
show_help() {
    echo "发票OCR系统Docker部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start       启动服务"
    echo "  start-admin 启动服务（包含管理界面）"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  pull        拉取最新镜像"
    echo "  logs        查看日志"
    echo "  status      检查状态"
    echo "  cleanup     清理资源"
    echo "  backup      备份数据"
    echo "  help        显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 start              # 启动服务"
    echo "  $0 start-admin        # 启动服务（包含管理界面）"
    echo "  $0 logs               # 查看日志"
    echo "  $0 status             # 检查状态"
}

# 主函数
main() {
    # 检查Docker环境
    check_docker
    
    # 处理命令行参数
    case "${1:-help}" in
        "start")
            start_service
            ;;
        "start-admin")
            start_with_admin
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "pull")
            pull_image
            ;;
        "logs")
            show_logs
            ;;
        "status")
            check_status
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            backup_data
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"

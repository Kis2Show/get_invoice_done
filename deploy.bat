@echo off
REM 发票OCR系统Docker部署脚本 (Windows版本)
REM 使用方法: deploy.bat [start|stop|restart|build|logs|status]

setlocal enabledelayedexpansion

REM 项目配置
set PROJECT_NAME=invoice-ocr-system
set COMPOSE_FILE=docker-compose.yml

REM 颜色定义（Windows不支持颜色，使用echo代替）
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM 检查Docker是否安装
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Docker未安装，请先安装Docker Desktop
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Docker Compose未安装，请先安装Docker Compose
    exit /b 1
)

echo %INFO% Docker环境检查通过
goto :eof

REM 创建必要的目录
:create_directories
echo %INFO% 创建必要的目录...

if not exist "data" mkdir data
if not exist "invoices" mkdir invoices
if not exist "invoices\pdf" mkdir invoices\pdf
if not exist "invoices\imge" mkdir invoices\imge
if not exist "invoices\unrecognized" mkdir invoices\unrecognized
if not exist "logs" mkdir logs

echo %SUCCESS% 目录创建完成
goto :eof

REM 构建镜像
:build_image
echo %INFO% 构建Docker镜像...

docker-compose build --no-cache
if errorlevel 1 (
    echo %ERROR% 镜像构建失败
    exit /b 1
)

echo %SUCCESS% 镜像构建完成
goto :eof

REM 启动服务
:start_service
echo %INFO% 启动发票OCR系统...

call :create_directories

REM 启动主服务
docker-compose up -d invoice-ocr
if errorlevel 1 (
    echo %ERROR% 服务启动失败
    exit /b 1
)

echo %SUCCESS% 服务启动完成
echo %INFO% Web界面地址: http://localhost:8000
echo %INFO% 健康检查: http://localhost:8000/health

REM 等待服务启动
echo %INFO% 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
call :check_health
goto :eof

REM 启动服务（包含管理界面）
:start_with_admin
echo %INFO% 启动发票OCR系统（包含管理界面）...

call :create_directories

REM 启动所有服务
docker-compose --profile admin up -d
if errorlevel 1 (
    echo %ERROR% 服务启动失败
    exit /b 1
)

echo %SUCCESS% 服务启动完成
echo %INFO% Web界面地址: http://localhost:8000
echo %INFO% 数据库管理界面: http://localhost:8080
echo %INFO% 健康检查: http://localhost:8000/health

REM 等待服务启动
echo %INFO% 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
call :check_health
goto :eof

REM 停止服务
:stop_service
echo %INFO% 停止发票OCR系统...

docker-compose down
if errorlevel 1 (
    echo %ERROR% 服务停止失败
    exit /b 1
)

echo %SUCCESS% 服务已停止
goto :eof

REM 重启服务
:restart_service
echo %INFO% 重启发票OCR系统...

call :stop_service
timeout /t 2 /nobreak >nul
call :start_service
goto :eof

REM 查看日志
:show_logs
echo %INFO% 显示服务日志...

docker-compose logs -f invoice-ocr
goto :eof

REM 检查服务状态
:check_status
echo %INFO% 检查服务状态...

echo === Docker容器状态 ===
docker-compose ps

echo.
echo === 服务健康状态 ===
call :check_health

echo.
echo === 资源使用情况 ===
for /f "tokens=*" %%i in ('docker-compose ps -q') do (
    docker stats --no-stream %%i
)
goto :eof

REM 健康检查
:check_health
set max_attempts=30
set attempt=1

:health_loop
if !attempt! gtr !max_attempts! (
    echo %ERROR% 服务健康检查失败
    exit /b 1
)

REM 使用curl检查健康状态（如果可用）
curl -f -s http://localhost:8000/health >nul 2>&1
if not errorlevel 1 (
    echo %SUCCESS% 服务健康检查通过
    
    REM 获取服务信息
    for /f "delims=" %%i in ('curl -s http://localhost:8000/health') do set health_info=%%i
    echo 健康状态: !health_info!
    goto :eof
)

echo %WARNING% 健康检查失败，重试中... (!attempt!/!max_attempts!)
timeout /t 2 /nobreak >nul
set /a attempt+=1
goto health_loop

REM 清理资源
:cleanup
echo %INFO% 清理Docker资源...

REM 停止并删除容器
docker-compose down --volumes --remove-orphans
if errorlevel 1 (
    echo %ERROR% 清理失败
    exit /b 1
)

REM 询问是否删除镜像
set /p delete_images="是否删除Docker镜像? (y/N): "
if /i "!delete_images!"=="y" (
    docker-compose down --rmi all
    echo %SUCCESS% 镜像已删除
)

echo %SUCCESS% 清理完成
goto :eof

REM 备份数据
:backup_data
echo %INFO% 备份数据...

REM 创建备份目录
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "backup_dir=backup_%dt:~0,8%_%dt:~8,6%"
mkdir "!backup_dir!"

REM 备份数据库
if exist "data\invoices.db" (
    copy "data\invoices.db" "!backup_dir!\" >nul
    echo %SUCCESS% 数据库备份完成
)

REM 备份发票文件
if exist "invoices" (
    xcopy "invoices" "!backup_dir!\invoices\" /E /I /Q >nul
    echo %SUCCESS% 发票文件备份完成
)

echo %SUCCESS% 备份完成: !backup_dir!
goto :eof

REM 显示帮助信息
:show_help
echo 发票OCR系统Docker部署脚本 (Windows版本)
echo.
echo 使用方法:
echo   %~nx0 [命令]
echo.
echo 可用命令:
echo   start       启动服务
echo   start-admin 启动服务（包含管理界面）
echo   stop        停止服务
echo   restart     重启服务
echo   build       构建镜像
echo   logs        查看日志
echo   status      检查状态
echo   cleanup     清理资源
echo   backup      备份数据
echo   help        显示帮助
echo.
echo 示例:
echo   %~nx0 start              # 启动服务
echo   %~nx0 start-admin        # 启动服务（包含管理界面）
echo   %~nx0 logs               # 查看日志
echo   %~nx0 status             # 检查状态
goto :eof

REM 主函数
:main
call :check_docker

REM 处理命令行参数
set command=%1
if "%command%"=="" set command=help

if "%command%"=="start" (
    call :start_service
) else if "%command%"=="start-admin" (
    call :start_with_admin
) else if "%command%"=="stop" (
    call :stop_service
) else if "%command%"=="restart" (
    call :restart_service
) else if "%command%"=="build" (
    call :build_image
) else if "%command%"=="logs" (
    call :show_logs
) else if "%command%"=="status" (
    call :check_status
) else if "%command%"=="cleanup" (
    call :cleanup
) else if "%command%"=="backup" (
    call :backup_data
) else (
    call :show_help
)

goto :eof

REM 执行主函数
call :main %*

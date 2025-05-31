# 🔧 GitHub Actions 问题修复指南

## 📋 问题概述

在GitHub Actions运行过程中遇到了两个主要问题：
1. **actions/upload-artifact@v3** 下载信息缺失
2. **Docker Hub登录失败** - 用户名或密码错误

## ✅ 已修复的问题

### 1. 🔄 Actions版本更新

#### 问题描述
- `actions/upload-artifact@v3` 下载信息缺失
- `codecov/codecov-action@v3` 版本过旧

#### 解决方案
更新所有Actions到最新稳定版本：

```yaml
# 修复前
- uses: actions/upload-artifact@v3
- uses: codecov/codecov-action@v3

# 修复后  
- uses: actions/upload-artifact@v4
- uses: codecov/codecov-action@v4
```

#### 修复的文件
- `.github/workflows/ci-cd.yml`
- `.github/workflows/dependency-update.yml`

### 2. 🐳 Docker Hub认证修复

#### 问题描述
```
Error: Error response from daemon: Get "https://registry-1.docker.io/v2/": unauthorized: incorrect username or password
```

#### 根本原因
Docker登录配置中包含了不必要的`registry`参数，导致认证失败。

#### 解决方案
简化Docker登录配置：

```yaml
# 修复前
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    registry: ${{ env.REGISTRY }}  # 这行导致问题
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

# 修复后
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

#### 修复的文件
- `.github/workflows/docker-build.yml`
- `.github/workflows/ci-cd.yml`
- `.github/workflows/release.yml`

## 🔍 Secrets配置验证

### 必需的GitHub Secrets

确保在GitHub仓库设置中配置了以下Secrets：

| Secret名称 | 描述 | 状态 |
|-----------|------|------|
| `DOCKERHUB_USERNAME` | Docker Hub用户名 | ✅ 已配置 |
| `DOCKERHUB_TOKEN` | Docker Hub访问令牌 | ✅ 已配置 |
| `CODECOV_TOKEN` | Codecov上传令牌 | ⚠️ 可选 |

### Docker Hub用户名验证

请确认Docker Hub用户名为：**kis2show**

如果用户名不正确，请在GitHub仓库设置中更新：
1. 访问：`https://github.com/Kis2Show/get_invoice_done/settings/secrets/actions`
2. 编辑 `DOCKERHUB_USERNAME`
3. 确保值为：`kis2show`

### Docker Hub Token验证

如果Docker Hub Token有问题，请重新生成：

1. **登录Docker Hub**: https://hub.docker.com/
2. **访问Account Settings** → **Security**
3. **创建新的Access Token**:
   - Token名称: `github-actions-kis2show`
   - 权限: `Read, Write, Delete`
4. **复制Token**并更新GitHub Secret

## 🚀 修复验证

### 1. 推送修复
```bash
git add .
git commit -m "🔧 Fix GitHub Actions issues

- Update actions/upload-artifact to v4
- Update codecov/codecov-action to v4  
- Fix Docker Hub login configuration
- Remove unnecessary registry parameter"
git push
```

### 2. 验证修复效果

#### 检查Actions运行
1. 访问：https://github.com/Kis2Show/get_invoice_done/actions
2. 查看最新的工作流运行
3. 确认以下步骤成功：
   - ✅ Docker Hub登录
   - ✅ 文件上传
   - ✅ 镜像构建和推送

#### 检查Docker Hub
1. 访问：https://hub.docker.com/r/kis2show/get_invoice_done
2. 确认镜像已成功推送
3. 查看标签：`latest`, `master-[commit]`

## 📊 预期结果

### 成功的工作流应该显示：

#### CI/CD Pipeline
```
✅ Run Tests
✅ Security Scan  
✅ Build Docker Image
✅ Docker Security Scan
✅ Notify
```

#### Docker Build
```
✅ Checkout code
✅ Set up Docker Buildx
✅ Log in to Docker Hub
✅ Extract metadata
✅ Build and push Docker image
✅ Generate artifact attestation
```

### Docker镜像推送
- **仓库**: kis2show/get_invoice_done
- **标签**: latest, master-[commit]
- **架构**: linux/amd64, linux/arm64

## 🔧 故障排除

### 如果Docker登录仍然失败

#### 1. 验证用户名
```bash
# 确认Docker Hub用户名
echo "kis2show"
```

#### 2. 重新生成Token
- 删除旧的Access Token
- 创建新的Access Token
- 更新GitHub Secret

#### 3. 检查Token权限
确保Token具有以下权限：
- ✅ Read
- ✅ Write  
- ✅ Delete

### 如果Actions版本问题

#### 1. 检查Actions市场
访问：https://github.com/marketplace/actions/

#### 2. 使用固定版本
```yaml
# 使用特定版本而不是latest
- uses: actions/upload-artifact@v4.3.1
- uses: codecov/codecov-action@v4.1.0
```

### 如果Codecov上传失败

#### 1. 添加Codecov Token (可选)
```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    file: ./coverage.xml
```

#### 2. 或者移除Codecov步骤
如果不需要代码覆盖率报告，可以注释掉相关步骤。

## 📋 修复清单

### ✅ 已完成
- [x] 更新actions/upload-artifact到v4
- [x] 更新codecov/codecov-action到v4
- [x] 修复Docker Hub登录配置
- [x] 移除不必要的registry参数
- [x] 更新所有工作流文件

### 🔄 待验证
- [ ] 推送修复到GitHub
- [ ] 验证Actions运行成功
- [ ] 确认Docker镜像推送成功
- [ ] 检查所有工作流正常

## 🎯 下一步操作

1. **立即推送修复**:
   ```bash
   git add .
   git commit -m "🔧 Fix GitHub Actions authentication and version issues"
   git push
   ```

2. **监控Actions运行**:
   - 访问Actions页面
   - 查看工作流状态
   - 确认所有步骤成功

3. **验证Docker镜像**:
   - 检查Docker Hub仓库
   - 确认镜像标签正确
   - 测试镜像拉取

---

**🔧 修复已准备就绪，立即推送以解决GitHub Actions问题！** 🚀

# 🔒 GitHub Actions 权限问题修复指南

## 📋 问题概述

**提交**: af52412 - 权限修复完成

### 解决的权限问题

#### 1. **Build Provenance 权限错误**
```
Error: Failed to get ID token: Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable
```

#### 2. **Security Scan SARIF 上传权限错误**
```
Warning: Resource not accessible by integration
Error: Resource not accessible by integration
```

## 🔧 修复方案

### 1. Docker Build 工作流权限修复

**文件**: `.github/workflows/docker-build.yml`

**添加的权限**:
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read          # 读取仓库内容
      id-token: write         # 生成ID token用于attestations
      attestations: write     # 写入构建证明
```

**修复的功能**:
- ✅ `actions/attest-build-provenance@v1` 现在可以正常工作
- ✅ 构建证明可以正确生成和上传
- ✅ ID token 获取问题解决

### 2. CI/CD 安全扫描权限修复

**文件**: `.github/workflows/ci-cd.yml`

**添加的权限**:
```yaml
security-scan:
  permissions:
    contents: read          # 读取仓库内容
    security-events: write  # 上传SARIF到Security tab

docker-security-scan:
  permissions:
    contents: read          # 读取仓库内容
    security-events: write  # 上传SARIF到Security tab
```

**修复的功能**:
- ✅ Trivy SARIF 结果可以上传到 GitHub Security tab
- ✅ CodeQL Action v3 SARIF 上传正常工作
- ✅ "Resource not accessible by integration" 错误解决

## 📊 权限配置详解

### GitHub Actions 权限类型

| 权限类型 | 用途 | 修复的问题 |
|---------|------|-----------|
| `contents: read` | 读取仓库代码和文件 | 基础访问权限 |
| `id-token: write` | 生成OIDC ID token | Build provenance attestations |
| `attestations: write` | 写入构建证明 | Artifact attestations |
| `security-events: write` | 上传安全扫描结果 | SARIF文件上传到Security tab |

### 权限最小化原则

我们遵循最小权限原则，只授予必要的权限：

```yaml
# ✅ 正确的权限配置
permissions:
  contents: read          # 只读访问
  id-token: write         # 仅在需要attestations时
  attestations: write     # 仅在需要构建证明时
  security-events: write  # 仅在需要安全扫描时

# ❌ 避免过度权限
permissions: write-all    # 不推荐，权限过大
```

## 🎯 修复效果

### 预期正常输出

#### 1. Build Provenance 成功
```
✅ Generate artifact attestation
Successfully generated build provenance attestation
Attestation uploaded to registry
```

#### 2. Security Scan 成功
```
✅ Upload Trivy scan results to GitHub Security tab
Uploading results
Processing sarif files: ["trivy-results.sarif"]
Validating trivy-results.sarif
Successfully uploaded SARIF file
```

#### 3. Docker Security Scan 成功
```
✅ Upload Docker scan results
Successfully uploaded docker-trivy-results.sarif
Results available in Security tab
```

## 🔍 验证方法

### 1. 检查 GitHub Actions 日志
- 访问: https://github.com/Kis2Show/get_invoice_done/actions
- 查看最新的工作流运行
- 确认没有权限错误

### 2. 检查 Security Tab
- 访问: https://github.com/Kis2Show/get_invoice_done/security
- 查看 "Code scanning alerts"
- 确认 Trivy 扫描结果已上传

### 3. 检查 Attestations
- 在 Docker Hub 或 GitHub Packages 中查看构建证明
- 验证 artifact attestations 正常生成

## 🚨 常见权限问题

### 问题1: ID Token 获取失败
```
Error: Failed to get ID token
```
**解决方案**: 添加 `id-token: write` 权限

### 问题2: SARIF 上传失败
```
Resource not accessible by integration
```
**解决方案**: 添加 `security-events: write` 权限

### 问题3: Attestation 写入失败
```
Error: Insufficient permissions to write attestations
```
**解决方案**: 添加 `attestations: write` 权限

## 📚 GitHub Actions 权限参考

### 完整权限列表
- `actions: read/write` - 管理 Actions
- `checks: read/write` - 管理检查
- `contents: read/write` - 访问仓库内容
- `deployments: read/write` - 管理部署
- `id-token: write` - 生成 OIDC token
- `issues: read/write` - 管理 issues
- `packages: read/write` - 管理包
- `pages: read/write` - 管理 GitHub Pages
- `pull-requests: read/write` - 管理 PR
- `repository-projects: read/write` - 管理项目
- `security-events: write` - 上传安全事件
- `statuses: read/write` - 管理状态检查
- `attestations: write` - 写入构建证明

### 权限继承规则
1. **默认权限**: 如果没有指定，使用仓库设置的默认权限
2. **作业级权限**: 覆盖工作流级权限
3. **步骤级权限**: 某些 Actions 可能需要特定权限

## 🔮 最佳实践

### 1. 权限最小化
```yaml
# ✅ 推荐：明确指定最小权限
permissions:
  contents: read
  security-events: write

# ❌ 不推荐：使用过大权限
permissions: write-all
```

### 2. 条件性权限
```yaml
# 只在需要时授予权限
- name: Upload SARIF
  if: github.event_name != 'pull_request'
  uses: github/codeql-action/upload-sarif@v3
```

### 3. 权限文档化
```yaml
permissions:
  contents: read          # 读取源代码
  id-token: write         # 生成构建证明
  security-events: write  # 上传安全扫描结果
```

## 📞 故障排除

### 如果权限问题仍然存在：

1. **检查仓库设置**
   - Settings → Actions → General
   - 确认 "Workflow permissions" 设置正确

2. **检查组织策略**
   - 组织级别的权限策略可能覆盖仓库设置

3. **验证 Token 权限**
   - 确认使用的 `GITHUB_TOKEN` 有足够权限

4. **检查分支保护**
   - 分支保护规则可能影响权限

---

**🎉 权限问题修复完成！**

**主要成就**:
- 🔒 **Build Provenance**: ID token 和 attestations 权限配置
- 🛡️ **Security Scans**: SARIF 上传权限修复
- 📊 **最小权限**: 遵循安全最佳实践
- 📚 **文档完善**: 详细的权限配置指南

**您的 GitHub Actions 现在拥有了正确的权限配置！** 🚀✨

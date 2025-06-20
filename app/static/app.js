class InvoiceApp {
    constructor() {
        this.currentInvoiceId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadStatistics();
        this.loadInvoices();
    }

    bindEvents() {
        document.getElementById('processBtn').addEventListener('click', () => this.processInvoices());
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshData());
        document.getElementById('deduplicateBtn').addEventListener('click', () => this.deduplicateInvoices());
        document.getElementById('searchBtn').addEventListener('click', () => this.loadInvoices());
        document.getElementById('deleteInvoiceBtn').addEventListener('click', () => this.deleteInvoice());
        document.getElementById('errorManagementBtn').addEventListener('click', () => this.showErrorManagement());
        document.getElementById('uploadBtn').addEventListener('click', () => this.showUploadModal());
        document.getElementById('fileManagementBtn').addEventListener('click', () => this.showFileManagement());

        // 上传相关事件
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileSelection(e));
        document.getElementById('startUploadBtn').addEventListener('click', () => this.uploadFiles());

        // 文件管理相关事件
        document.getElementById('refreshFilesBtn').addEventListener('click', () => this.loadFileList());

        // 回车键搜索
        ['invoiceNumber', 'sellerName', 'buyerName', 'minAmount', 'maxAmount'].forEach(id => {
            document.getElementById(id).addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.loadInvoices();
            });
        });
    }

    async processInvoices() {
        this.showLoading(true);
        try {
            const response = await fetch('/api/invoices/process', {
                method: 'POST'
            });
            const result = await response.json();
            
            if (response.ok) {
                this.showAlert(`处理完成！总文件: ${result.total_files}, 成功: ${result.processed_files}, 失败: ${result.failed_files}`, 'success');
                this.refreshData();
            } else {
                this.showAlert('处理失败: ' + result.detail, 'danger');
            }
        } catch (error) {
            this.showAlert('处理失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/invoices/stats/summary');
            const stats = await response.json();
            
            document.getElementById('totalInvoices').textContent = stats.total_invoices || 0;
            document.getElementById('processedInvoices').textContent = stats.processed_invoices || 0;
            document.getElementById('totalAmount').textContent = '¥' + (stats.total_amount_sum || 0).toLocaleString();
            document.getElementById('fileTypes').textContent = `图片: ${stats.image_invoices || 0} | PDF: ${stats.pdf_invoices || 0}`;
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    async loadInvoices() {
        this.showLoading(true);
        try {
            const params = this.getFilterParams();
            const queryString = new URLSearchParams(params).toString();
            const response = await fetch(`/api/invoices/?${queryString}`);
            const invoices = await response.json();
            
            this.renderInvoices(invoices);
        } catch (error) {
            this.showAlert('加载发票失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    getFilterParams() {
        const params = {};
        
        const invoiceNumber = document.getElementById('invoiceNumber').value.trim();
        if (invoiceNumber) params.invoice_number = invoiceNumber;
        
        const sellerName = document.getElementById('sellerName').value.trim();
        if (sellerName) params.seller_name = sellerName;
        
        const buyerName = document.getElementById('buyerName').value.trim();
        if (buyerName) params.buyer_name = buyerName;
        
        const minAmount = document.getElementById('minAmount').value;
        if (minAmount) params.min_amount = minAmount;
        
        const maxAmount = document.getElementById('maxAmount').value;
        if (maxAmount) params.max_amount = maxAmount;
        
        const startDate = document.getElementById('startDate').value;
        if (startDate) params.start_date = startDate;
        
        const endDate = document.getElementById('endDate').value;
        if (endDate) params.end_date = endDate;
        
        params.sort_by = document.getElementById('sortBy').value;
        params.sort_order = document.getElementById('sortOrder').value;
        
        return params;
    }

    renderInvoices(invoices) {
        const container = document.getElementById('invoiceList');
        const noResults = document.getElementById('noResults');
        
        if (!invoices || invoices.length === 0) {
            container.innerHTML = '';
            noResults.style.display = 'block';
            return;
        }
        
        noResults.style.display = 'none';
        container.innerHTML = invoices.map(invoice => this.createInvoiceCard(invoice)).join('');
    }

    createInvoiceCard(invoice) {
        const formatDate = (dateStr) => {
            if (!dateStr) return '未知';
            return new Date(dateStr).toLocaleDateString('zh-CN');
        };

        const formatAmount = (amount) => {
            if (!amount) return '未知';
            return '¥' + amount.toLocaleString();
        };

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card invoice-card h-100" onclick="app.showInvoiceDetails(${invoice.id})">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title text-truncate">${invoice.file_name || '未知文件'}</h6>
                            <span class="badge bg-${invoice.file_type === 'image' ? 'primary' : 'success'}">${invoice.file_type}</span>
                        </div>
                        <p class="card-text">
                            <small class="text-muted">发票号码:</small><br>
                            <strong>${invoice.invoice_number || '未识别'}</strong>
                        </p>
                        <p class="card-text">
                            <small class="text-muted">销售方:</small><br>
                            ${invoice.seller_name || '未识别'}
                        </p>
                        <p class="card-text">
                            <small class="text-muted">金额:</small><br>
                            <strong class="text-primary">${formatAmount(invoice.total_amount)}</strong>
                        </p>
                        <p class="card-text">
                            <small class="text-muted">开票日期: ${formatDate(invoice.invoice_date)}</small>
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    async showInvoiceDetails(invoiceId) {
        try {
            const response = await fetch(`/api/invoices/${invoiceId}`);
            const invoice = await response.json();
            
            if (response.ok) {
                this.currentInvoiceId = invoiceId;
                this.renderInvoiceDetails(invoice);
                new bootstrap.Modal(document.getElementById('invoiceModal')).show();
            } else {
                this.showAlert('获取发票详情失败', 'danger');
            }
        } catch (error) {
            this.showAlert('获取发票详情失败: ' + error.message, 'danger');
        }
    }

    renderInvoiceDetails(invoice) {
        const formatDate = (dateStr) => {
            if (!dateStr) return '未知';
            return new Date(dateStr).toLocaleDateString('zh-CN');
        };

        const formatAmount = (amount) => {
            if (!amount) return '未知';
            return '¥' + amount.toLocaleString();
        };

        const details = `
            <div class="row">
                <div class="col-md-6">
                    <h6>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td>文件名:</td><td>${invoice.file_name || '未知'}</td></tr>
                        <tr><td>文件类型:</td><td>${invoice.file_type}</td></tr>
                        <tr><td>发票号码:</td><td>${invoice.invoice_number || '未识别'}</td></tr>

                        <tr><td>开票日期:</td><td>${formatDate(invoice.invoice_date)}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>金额信息</h6>
                    <table class="table table-sm">
                        <tr><td>价税合计:</td><td><strong>${formatAmount(invoice.total_amount)}</strong></td></tr>
                        <tr><td>税额:</td><td>${formatAmount(invoice.tax_amount)}</td></tr>
                        <tr><td>不含税金额:</td><td>${formatAmount(invoice.amount_without_tax)}</td></tr>
                    </table>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <h6>销售方信息</h6>
                    <table class="table table-sm">
                        <tr><td>名称:</td><td>${invoice.seller_name || '未识别'}</td></tr>
                        <tr><td>税号:</td><td>${invoice.seller_tax_number || '未识别'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>购买方信息</h6>
                    <table class="table table-sm">
                        <tr><td>名称:</td><td>${invoice.buyer_name || '未识别'}</td></tr>
                        <tr><td>税号:</td><td>${invoice.buyer_tax_number || '未识别'}</td></tr>
                    </table>
                </div>
            </div>
            ${invoice.raw_text ? `
                <div class="row">
                    <div class="col-12">
                        <h6>原始识别文本</h6>
                        <textarea class="form-control" rows="5" readonly>${invoice.raw_text}</textarea>
                    </div>
                </div>
            ` : ''}
        `;
        
        document.getElementById('invoiceDetails').innerHTML = details;
    }

    async deleteInvoice() {
        if (!this.currentInvoiceId) return;
        
        if (!confirm('确定要删除这张发票吗？')) return;
        
        try {
            const response = await fetch(`/api/invoices/${this.currentInvoiceId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showAlert('发票删除成功', 'success');
                bootstrap.Modal.getInstance(document.getElementById('invoiceModal')).hide();
                this.refreshData();
            } else {
                this.showAlert('删除失败', 'danger');
            }
        } catch (error) {
            this.showAlert('删除失败: ' + error.message, 'danger');
        }
    }

    async deduplicateInvoices() {
        if (!confirm('确定要执行去重操作吗？重复的发票记录将被删除。')) return;
        
        this.showLoading(true);
        try {
            const response = await fetch('/api/invoices/deduplicate', {
                method: 'POST'
            });
            const result = await response.json();
            
            if (response.ok) {
                this.showAlert(result.message, 'success');
                this.refreshData();
            } else {
                this.showAlert('去重失败: ' + result.detail, 'danger');
            }
        } catch (error) {
            this.showAlert('去重失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    refreshData() {
        this.loadStatistics();
        this.loadInvoices();
    }

    showLoading(show) {
        const loading = document.querySelector('.loading');
        loading.style.display = show ? 'inline-block' : 'none';
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    async showErrorManagement() {
        try {
            // 加载错误统计和未识别文件
            await this.loadErrorStatistics();
            await this.loadUnrecognizedFiles();

            // 绑定错误管理模态框内的事件
            this.bindErrorManagementEvents();

            // 显示模态框
            new bootstrap.Modal(document.getElementById('errorManagementModal')).show();
        } catch (error) {
            this.showAlert('加载错误管理信息失败: ' + error.message, 'danger');
        }
    }

    async loadErrorStatistics() {
        try {
            const response = await fetch('/api/invoices/errors/statistics');
            const stats = await response.json();

            // 更新错误统计显示
            document.getElementById('totalErrors').textContent = stats.total_errors || 0;
            document.getElementById('avgConfidence').textContent =
                ((stats.avg_confidence || 0) * 100).toFixed(1) + '%';

            // 显示错误类型分布
            this.renderErrorTypeChart(stats.error_types || {});

        } catch (error) {
            console.error('Failed to load error statistics:', error);
        }
    }

    async loadUnrecognizedFiles() {
        try {
            const response = await fetch('/api/invoices/errors/unrecognized');
            const data = await response.json();

            // 更新未识别文件统计
            document.getElementById('unrecognizedFiles').textContent = data.total_count || 0;

            // 计算需要审核的文件数量
            const needsReview = (data.files || []).filter(file =>
                file.category === 'manual_review' || file.category === 'low_confidence'
            ).length;
            document.getElementById('needsReview').textContent = needsReview;

            // 渲染未识别文件列表
            this.renderUnrecognizedFilesList(data.files || []);

        } catch (error) {
            console.error('Failed to load unrecognized files:', error);
        }
    }

    renderErrorTypeChart(errorTypes) {
        const chartContainer = document.getElementById('errorTypeChart');

        if (Object.keys(errorTypes).length === 0) {
            chartContainer.innerHTML = '<p class="text-muted">暂无错误数据</p>';
            return;
        }

        // 创建简单的条形图
        const total = Object.values(errorTypes).reduce((sum, count) => sum + count, 0);

        const chartHTML = Object.entries(errorTypes).map(([type, count]) => {
            const percentage = (count / total * 100).toFixed(1);
            const typeNames = {
                'missing_critical_fields': '缺少关键字段',
                'low_confidence': '置信度低',
                'parsing_errors': '解析错误',
                'validation_failed': '验证失败',
                'manual_review': '需要人工审核'
            };

            return `
                <div class="mb-2">
                    <div class="d-flex justify-content-between">
                        <span>${typeNames[type] || type}</span>
                        <span>${count} (${percentage}%)</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        }).join('');

        chartContainer.innerHTML = chartHTML;
    }

    renderUnrecognizedFilesList(files) {
        const tbody = document.getElementById('unrecognizedFilesList');

        if (files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无未识别文件</td></tr>';
            return;
        }

        const categoryNames = {
            'missing_critical_fields': '缺少关键字段',
            'low_confidence': '置信度低',
            'parsing_errors': '解析错误',
            'validation_failed': '验证失败',
            'manual_review': '需要人工审核'
        };

        tbody.innerHTML = files.map(file => `
            <tr>
                <td>${file.file_name}</td>
                <td>
                    <span class="badge bg-secondary">${categoryNames[file.category] || file.category}</span>
                </td>
                <td>${(file.file_size / 1024).toFixed(1)} KB</td>
                <td>${new Date(file.modified_time).toLocaleString('zh-CN')}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="app.viewUnrecognizedFile('${file.file_path}')">
                        <i class="bi bi-eye"></i> 查看
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="app.deleteUnrecognizedFile('${file.file_path}', '${file.file_name}')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `).join('');
    }

    bindErrorManagementEvents() {
        // 绑定生成报告按钮
        const generateReportBtn = document.getElementById('generateReportBtn');
        if (generateReportBtn) {
            generateReportBtn.onclick = () => this.generateErrorReport();
        }

        // 绑定刷新错误信息按钮
        const refreshErrorsBtn = document.getElementById('refreshErrorsBtn');
        if (refreshErrorsBtn) {
            refreshErrorsBtn.onclick = () => {
                this.loadErrorStatistics();
                this.loadUnrecognizedFiles();
            };
        }

        // 绑定清空所有未识别文件按钮
        const clearAllErrorsBtn = document.getElementById('clearAllErrorsBtn');
        if (clearAllErrorsBtn) {
            clearAllErrorsBtn.onclick = () => this.clearAllUnrecognizedFiles();
        }
    }

    async generateErrorReport() {
        try {
            const response = await fetch('/api/invoices/errors/generate_report', {
                method: 'POST'
            });
            const result = await response.json();

            if (response.ok) {
                this.showAlert('错误报告生成成功: ' + result.report_path, 'success');
            } else {
                this.showAlert('生成错误报告失败: ' + result.detail, 'danger');
            }
        } catch (error) {
            this.showAlert('生成错误报告失败: ' + error.message, 'danger');
        }
    }

    viewUnrecognizedFile(filePath) {
        this.showAlert(`文件路径: ${filePath}`, 'info');
        // 这里可以添加更多的文件查看逻辑
    }

    async deleteUnrecognizedFile(filePath, fileName) {
        if (!confirm(`确定要删除未识别文件 "${fileName}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            const response = await fetch('/api/invoices/errors/delete_unrecognized', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_path: filePath
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showAlert(`文件 "${fileName}" 删除成功`, 'success');
                // 刷新未识别文件列表
                this.loadUnrecognizedFiles();
                this.loadErrorStatistics();
            } else {
                this.showAlert(`删除文件失败: ${result.detail}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`删除文件失败: ${error.message}`, 'danger');
        }
    }

    async clearAllUnrecognizedFiles() {
        if (!confirm('确定要清空所有未识别文件吗？此操作将删除所有未识别目录中的文件，不可撤销！')) {
            return;
        }

        try {
            const response = await fetch('/api/invoices/errors/clear_all_unrecognized', {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                this.showAlert(`成功清空 ${result.deleted_count} 个未识别文件`, 'success');
                // 刷新未识别文件列表
                this.loadUnrecognizedFiles();
                this.loadErrorStatistics();
            } else {
                this.showAlert(`清空文件失败: ${result.detail}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`清空文件失败: ${error.message}`, 'danger');
        }
    }

    // ==================== 上传功能 ====================

    showUploadModal() {
        // 重置上传表单
        this.resetUploadForm();
        // 显示上传模态框
        new bootstrap.Modal(document.getElementById('uploadModal')).show();
    }

    resetUploadForm() {
        document.getElementById('fileInput').value = '';
        document.getElementById('filePreview').style.display = 'none';
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadResults').style.display = 'none';
        document.getElementById('startUploadBtn').disabled = true;
        document.getElementById('fileList').innerHTML = '';
        document.getElementById('uploadResultsList').innerHTML = '';
    }

    handleFileSelection(event) {
        const files = Array.from(event.target.files);

        if (files.length === 0) {
            document.getElementById('filePreview').style.display = 'none';
            document.getElementById('startUploadBtn').disabled = true;
            return;
        }

        // 验证文件类型
        const invalidFiles = this.validateFileTypes(files);
        if (invalidFiles.length > 0) {
            this.showAlert(`以下文件类型不支持：${invalidFiles.join(', ')}。只允许上传PDF或图片文件。`, 'warning');
            event.target.value = ''; // 清空文件选择
            document.getElementById('filePreview').style.display = 'none';
            document.getElementById('startUploadBtn').disabled = true;
            return;
        }

        // 显示文件预览
        this.showFilePreview(files);
        document.getElementById('startUploadBtn').disabled = false;
    }

    validateFileTypes(files) {
        const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif'];
        const invalidFiles = [];

        files.forEach(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            if (!allowedExtensions.includes(ext)) {
                invalidFiles.push(file.name);
            }
        });

        return invalidFiles;
    }

    showFilePreview(files) {
        const fileList = document.getElementById('fileList');
        const filePreview = document.getElementById('filePreview');

        fileList.innerHTML = files.map((file, index) => {
            const fileSize = (file.size / 1024).toFixed(1);
            const fileType = this.getFileTypeIcon(file.name);

            return `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <i class="bi ${fileType.icon} me-2"></i>
                        <strong>${file.name}</strong>
                        <small class="text-muted ms-2">(${fileSize} KB)</small>
                    </div>
                    <span class="badge bg-${fileType.color}">${fileType.type}</span>
                </div>
            `;
        }).join('');

        filePreview.style.display = 'block';
    }

    getFileTypeIcon(fileName) {
        const ext = fileName.toLowerCase().split('.').pop();

        if (ext === 'pdf') {
            return { icon: 'bi-file-earmark-pdf', color: 'danger', type: 'PDF' };
        } else if (['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif'].includes(ext)) {
            return { icon: 'bi-file-earmark-image', color: 'primary', type: '图片' };
        } else {
            return { icon: 'bi-file-earmark', color: 'secondary', type: '其他' };
        }
    }

    async uploadFiles() {
        const fileInput = document.getElementById('fileInput');
        const files = fileInput.files;

        if (files.length === 0) {
            this.showAlert('请选择要上传的文件', 'warning');
            return;
        }

        // 显示上传进度
        this.showUploadProgress();

        try {
            const formData = new FormData();
            Array.from(files).forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/api/invoices/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.showUploadResults(result);
                this.showAlert(`上传完成！成功: ${result.successful_uploads}, 失败: ${result.failed_uploads}`, 'success');

                // 刷新数据
                setTimeout(() => {
                    this.refreshData();
                }, 1000);
            } else {
                this.showAlert('上传失败: ' + result.detail, 'danger');
            }
        } catch (error) {
            this.showAlert('上传失败: ' + error.message, 'danger');
        } finally {
            this.hideUploadProgress();
        }
    }

    showUploadProgress() {
        document.getElementById('uploadProgress').style.display = 'block';
        document.getElementById('uploadStatus').textContent = '正在上传文件...';
        document.getElementById('startUploadBtn').disabled = true;

        // 模拟进度条动画
        const progressBar = document.querySelector('#uploadProgress .progress-bar');
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
        }, 200);

        // 保存interval ID以便后续清除
        this.uploadProgressInterval = interval;
    }

    hideUploadProgress() {
        if (this.uploadProgressInterval) {
            clearInterval(this.uploadProgressInterval);
        }

        const progressBar = document.querySelector('#uploadProgress .progress-bar');
        progressBar.style.width = '100%';

        setTimeout(() => {
            document.getElementById('uploadProgress').style.display = 'none';
            document.getElementById('startUploadBtn').disabled = false;
        }, 500);
    }

    showUploadResults(result) {
        const resultsList = document.getElementById('uploadResultsList');
        const uploadResults = document.getElementById('uploadResults');

        resultsList.innerHTML = result.uploaded_files.map(file => {
            const statusClass = file.upload_status === 'success' ? 'success' : 'danger';
            const statusIcon = file.upload_status === 'success' ? 'bi-check-circle' : 'bi-x-circle';

            return `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <i class="bi ${statusIcon} me-2 text-${statusClass}"></i>
                        <strong>${file.file_name}</strong>
                        <small class="text-muted ms-2">(${(file.file_size / 1024).toFixed(1)} KB)</small>
                    </div>
                    <div>
                        <span class="badge bg-${statusClass}">${file.upload_status}</span>
                        ${file.message ? `<small class="text-muted d-block">${file.message}</small>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        uploadResults.style.display = 'block';
    }

    // ==================== 文件管理功能 ====================

    async showFileManagement() {
        try {
            await this.loadFileList();
            new bootstrap.Modal(document.getElementById('fileManagementModal')).show();
        } catch (error) {
            this.showAlert('加载文件管理失败: ' + error.message, 'danger');
        }
    }

    async loadFileList() {
        try {
            const response = await fetch('/api/invoices/files/list');
            const data = await response.json();

            if (response.ok) {
                this.updateFileStatistics(data);
                this.renderFileList(data.files);
            } else {
                this.showAlert('加载文件列表失败', 'danger');
            }
        } catch (error) {
            this.showAlert('加载文件列表失败: ' + error.message, 'danger');
        }
    }

    updateFileStatistics(data) {
        document.getElementById('totalFiles').textContent = data.total_files || 0;
        document.getElementById('pdfFiles').textContent = data.pdf_files || 0;
        document.getElementById('imageFiles').textContent = data.image_files || 0;
    }

    renderFileList(files) {
        const tbody = document.getElementById('fileManagementList');

        if (!files || (files.pdf && files.pdf.length === 0 && files.images && files.images.length === 0)) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无文件</td></tr>';
            return;
        }

        const allFiles = [...(files.pdf || []), ...(files.images || [])];

        tbody.innerHTML = allFiles.map(file => {
            const fileSize = (file.file_size / 1024).toFixed(1);
            const modifiedTime = new Date(file.modified_time * 1000).toLocaleString('zh-CN');
            const fileTypeIcon = this.getFileTypeIcon(file.file_name);

            return `
                <tr>
                    <td>
                        <i class="bi ${fileTypeIcon.icon} me-2"></i>
                        ${file.file_name}
                    </td>
                    <td>
                        <span class="badge bg-${fileTypeIcon.color}">${fileTypeIcon.type}</span>
                    </td>
                    <td>${fileSize} KB</td>
                    <td>${modifiedTime}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger"
                                onclick="app.deleteFile('${file.file_name}')"
                                title="删除文件">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    async deleteFile(fileName) {
        if (!confirm(`确定要删除文件 "${fileName}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            const response = await fetch(`/api/invoices/files/${encodeURIComponent(fileName)}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                this.showAlert(`文件 "${fileName}" 删除成功`, 'success');
                // 刷新文件列表
                this.loadFileList();
                // 刷新主页数据
                this.refreshData();
            } else {
                this.showAlert(`删除文件失败: ${result.detail}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`删除文件失败: ${error.message}`, 'danger');
        }
    }
}

// 初始化应用
const app = new InvoiceApp();

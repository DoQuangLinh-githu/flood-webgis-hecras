// frontend/js/simulation.js

class SimulationManager {
    constructor() {
        this.currentJobId = null;
        this.pollInterval = null;
        this.isPolling = false;
        this.statusOrder = ['QUEUED', 'RUNNING', 'PROCESSING', 'COMPLETED'];
        this.pollEveryMs = 5000; // 5s
    }

    async createSimulation(formData) {
        const submitBtn = document.getElementById('submitBtn');
        const btnIcon = submitBtn.querySelector('i');

        try {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            btnIcon.className = 'fas fa-spinner fa-spin';

            const data = {
                scenario_name: formData.scenarioName,
                rainfall: parseFloat(formData.rainfall),
                rainfall_unit: formData.rainfallUnit,
                duration: parseFloat(formData.duration),
                duration_unit: formData.durationUnit,
            };

            console.log('[simulation] POST /api/simulations/run', data);

            const response = await SimulationAPI.runSimulation(data);
            console.log('[simulation] response:', response);

            window.showToast(
                `Đã tạo job ${response.job_id}`,
                'success'
            );

            this.currentJobId = response.job_id;
            this.updateJobStatus(response);
            this.addToHistory(response);
            this.startPolling(response.job_id);

            return response;
        } catch (error) {
            window.showToast(
                error.message || 'Không thể chạy mô phỏng',
                'error'
            );
            throw error;
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
            btnIcon.className = 'fas fa-play';
        }
    }

    updateJobStatus(job) {
        const panel = document.getElementById('jobStatusPanel');
        if (!panel) return;
        panel.style.display = 'block';

        document.getElementById('jobIdDisplay').textContent = job.job_id || '-';
        document.getElementById('jobScenarioDisplay').textContent =
            job.scenario_name || '-';

        // Job.parameters có thể là object lồng nhau
        let params = job.parameters || {};
        if (params.parameters) {
            // Backend trả về { parameters: { rainfall, duration, ... } }
            params = params.parameters;
        }
        const rainfall = params.rainfall ?? 0;
        const rainfallUnit = params.rainfall_unit || 'mm';
        const duration = params.duration ?? 0;
        const durationUnit = params.duration_unit || 'hour';
        const paramsText = `${rainfall} ${rainfallUnit} / ${duration} ${durationUnit}`;
        document.getElementById('jobParamsDisplay').textContent = paramsText;

        if (job.created_at) {
            const created = new Date(job.created_at);
            document.getElementById('jobCreatedDisplay').textContent =
                created.toLocaleString('vi-VN');
        }

        this.updateStatusDisplay(job.status);
        this.updateProgress(job.status);
    }

    updateStatusDisplay(status) {
        const statusEl = document.getElementById('jobStatusDisplay');
        if (!statusEl) return;
        const s = (status || 'UNKNOWN').toUpperCase();
        statusEl.innerHTML = `<span class="status-badge status-${s.toLowerCase()}">${s}</span>`;
    }

    updateProgress(status) {
        const fill = document.getElementById('progressFill');
        if (!fill) return;
        const progress = SimulationAPI.getStatusProgress(status);
        fill.style.width = `${Math.min(progress, 100)}%`;

        const steps = document.querySelectorAll('.progress-steps .step');
        const statusIndex = this.statusOrder.indexOf(status);

        steps.forEach((step, index) => {
            step.classList.remove('active', 'done');
            if (index < statusIndex) step.classList.add('done');
            else if (index === statusIndex) step.classList.add('active');
        });

        if (status === 'COMPLETED') {
            fill.style.background = 'linear-gradient(90deg,#4caf50,#66bb6a)';
            steps.forEach((s) => s.classList.add('done'));
        } else if (status === 'FAILED' || status === 'CANCELLED') {
            fill.style.background = '#dc3545';
        } else {
            fill.style.background = 'linear-gradient(90deg,#1976d2,#4fc3f7)';
        }
    }

    async startPolling(jobId) {
        this.stopPolling();
        this.isPolling = true;
        this.currentJobId = jobId;

        // Poll ngay lập tức 1 lần
        await this._pollOnce(jobId);

        this.pollInterval = setInterval(async () => {
            await this._pollOnce(jobId);
        }, this.pollEveryMs);
    }

    async _pollOnce(jobId) {
        try {
            const status = await SimulationAPI.getSimulationStatus(jobId);
            if (!status) {
                this.stopPolling();
                window.showToast('Job không tồn tại', 'error');
                return;
            }

            this.updateJobStatus(status);

            if (SimulationAPI.isTerminalStatus(status.status)) {
                this.stopPolling();

                if (status.status === 'COMPLETED') {
                    window.showToast('✅ Mô phỏng hoàn thành!', 'success');

                    // Load GeoJSON + hiển thị lên bản đồ
                    if (window.floodMap) {
                        const geojson = await SimulationAPI.getGeojson(jobId);
                        if (geojson) {
                            window.floodMap.addFloodLayerFromGeojson(geojson);
                        } else {
                            window.showToast('Không tải được kết quả', 'warning');
                        }
                    }
                } else if (status.status === 'FAILED') {
                    window.showToast(
                        `❌ Mô phỏng thất bại: ${status.error_message || 'Unknown'}`,
                        'error'
                    );
                }
            }
        } catch (error) {
            console.error('Poll error:', error);
        }
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.isPolling = false;
    }

    addToHistory(job) {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;

        const emptyMsg = historyList.querySelector('.empty-history');
        if (emptyMsg) emptyMsg.remove();

        // Tránh thêm trùng
        const existing = historyList.querySelector(`[data-job-id="${job.job_id}"]`);
        if (existing) return;

        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.jobId = job.job_id;

        const created = job.created_at ? new Date(job.created_at) : new Date();
        const timeStr = created.toLocaleString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        const status = (job.status || 'QUEUED').toUpperCase();

        item.innerHTML = `
            <div class="h-left">
                <span class="h-job-id">${job.job_id}</span>
                <span class="h-scenario">${job.scenario_name || ''}</span>
            </div>
            <div class="h-right">
                <span class="h-status status-badge status-${status.toLowerCase()}">${status}</span>
                <span class="h-time">${timeStr}</span>
            </div>
        `;

        item.addEventListener('click', () => this.loadJob(job.job_id));
        historyList.prepend(item);
    }

        async loadJob(jobId) {
        const status = await SimulationAPI.getSimulationStatus(jobId);
        if (!status) {
            window.showToast(`Không tìm thấy job ${jobId}`, 'error');
            return;
        }
        this.currentJobId = jobId;
        this.updateJobStatus(status);

        if (status.status === 'COMPLETED') {
            await this._loadGeojson(jobId);
            window.showToast(`Đã tải kết quả job ${jobId}`, 'success');
        } else if (SimulationAPI.isTerminalStatus(status.status)) {
            window.showToast(`Job ${jobId}: ${status.status}`, 'warning');
        } else {
            this.startPolling(jobId);
            window.showToast(`Đang theo dõi job ${jobId}`, 'info');
        }
    }

    async _loadGeojson(jobId) {
        if (!window.floodMap) {
            console.warn('[simulation] floodMap not available');
            return;
        }

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/simulations/${jobId}/geojson`
            );

            if (!response.ok) {
                let msg = `HTTP ${response.status}`;
                try {
                    const err = await response.json();
                    msg = err.detail || msg;
                } catch (_) {}
                window.showToast(`Không tải được GeoJSON: ${msg}`, 'error');
                return;
            }

            const geojson = await response.json();
            window.floodMap.addFloodLayerFromGeojson(geojson);
        } catch (e) {
            console.error('_loadGeojson error:', e);
            window.showToast(`Lỗi tải kết quả: ${e.message}`, 'error');
        }
    }

    async refreshHistory() {
        const btn = document.getElementById('refreshHistoryBtn');
        if (btn) btn.classList.add('spinning');

        try {
            const jobs = await SimulationAPI.getSimulations();
            const historyList = document.getElementById('historyList');
            if (!historyList) return;
            historyList.innerHTML = '';

            if (!jobs || jobs.length === 0) {
                historyList.innerHTML = `
                    <div class="empty-history">
                        <i class="fas fa-inbox"></i>
                        <p>Chưa có mô phỏng nào</p>
                    </div>
                `;
                return;
            }

            jobs.forEach((job) => this.addToHistory(job));
            window.showToast(`Đã tải ${jobs.length} jobs`, 'success');
        } catch (error) {
            window.showToast('Không thể tải lịch sử', 'error');
        } finally {
            if (btn) btn.classList.remove('spinning');
        }
    }
}


// ============================================================
// INIT
// ============================================================

let simManager = null;

document.addEventListener('DOMContentLoaded', () => {
    simManager = new SimulationManager();
    window.simManager = simManager;

    const form = document.getElementById('simulationForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                scenarioName: document.getElementById('scenarioName').value.trim(),
                rainfall: document.getElementById('rainfall').value,
                rainfallUnit: document.getElementById('rainfallUnit').value,
                duration: document.getElementById('duration').value,
                durationUnit: document.getElementById('durationUnit').value,
            };

            if (!formData.scenarioName) {
                window.showToast('Vui lòng nhập tên kịch bản', 'warning');
                return;
            }
            if (!formData.rainfall || parseFloat(formData.rainfall) <= 0) {
                window.showToast('Vui lòng nhập lượng mưa hợp lệ', 'warning');
                return;
            }
            if (!formData.duration || parseFloat(formData.duration) <= 0) {
                window.showToast('Vui lòng nhập thời gian hợp lệ', 'warning');
                return;
            }

            await simManager.createSimulation(formData);
        });
    }

    const refreshBtn = document.getElementById('refreshHistoryBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => simManager.refreshHistory());
    }

    setTimeout(() => simManager.refreshHistory(), 500);
});
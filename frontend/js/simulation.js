// frontend/js/simulation.js

class SimulationManager {
    constructor() {
        this.currentJobId = null;
        this.pollInterval = null;
        this.isPolling = false;
        this.statusOrder = ['QUEUED', 'RUNNING', 'PROCESSING', 'COMPLETED'];
    }

    async createSimulation(formData) {
        const submitBtn = document.getElementById('submitBtn');
        const btnIcon = submitBtn.querySelector('i');

        try {
            // Disable button
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            btnIcon.className = 'fas fa-spinner';

            // Prepare data
            const data = {
                scenario_name: formData.scenarioName,
                rainfall: parseFloat(formData.rainfall),
                rainfall_unit: formData.rainfallUnit,
                duration: parseFloat(formData.duration),
                duration_unit: formData.durationUnit,
            };

            // Call API
            const response = await SimulationAPI.createSimulation(data);

            // Show success
            window.showToast(`Job ${response.job_id} created successfully!`, 'success');

            // Save job ID
            this.currentJobId = response.job_id;

            // Update UI
            this.updateJobStatus(response);

            // Add to history
            this.addToHistory(response);

            // Start polling
            this.startPolling(response.job_id);

            return response;
        } catch (error) {
            window.showToast(error.message || 'Failed to create simulation', 'error');
            throw error;
        } finally {
            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
            btnIcon.className = 'fas fa-play';
        }
    }

    updateJobStatus(job) {
        const panel = document.getElementById('jobStatusPanel');
        panel.style.display = 'block';

        document.getElementById('jobIdDisplay').textContent = job.job_id;
        document.getElementById('jobScenarioDisplay').textContent = job.scenario_name;

        // Parameters display
        const params = job.parameters || {};
        const paramsText = `${params.rainfall || 0} ${params.rainfall_unit || 'mm'} / ${params.duration || 0} ${params.duration_unit || 'hour'}`;
        document.getElementById('jobParamsDisplay').textContent = paramsText;

        // Created time
        const created = new Date(job.created_at);
        document.getElementById('jobCreatedDisplay').textContent = created.toLocaleString('vi-VN');

        // Status
        this.updateStatusDisplay(job.status);

        // Progress
        this.updateProgress(job.status);
    }

    updateStatusDisplay(status) {
        const statusEl = document.getElementById('jobStatusDisplay');
        const badge = statusEl.querySelector('.status-badge') || document.createElement('span');

        badge.className = `status-badge status-${status.toLowerCase()}`;
        badge.textContent = status;

        if (!statusEl.querySelector('.status-badge')) {
            statusEl.innerHTML = '';
            statusEl.appendChild(badge);
        } else {
            statusEl.innerHTML = '';
            statusEl.appendChild(badge);
        }
    }

    updateProgress(status) {
        const progress = SimulationAPI.getStatusProgress(status);
        const fill = document.getElementById('progressFill');
        fill.style.width = `${Math.min(progress, 100)}%`;

        // Update steps
        const steps = document.querySelectorAll('.progress-steps .step');
        const statusIndex = this.statusOrder.indexOf(status);

        steps.forEach((step, index) => {
            step.classList.remove('active', 'done');
            if (index < statusIndex) {
                step.classList.add('done');
            } else if (index === statusIndex) {
                step.classList.add('active');
            }
        });

        // Special case for COMPLETED
        if (status === 'COMPLETED') {
            fill.style.background = 'linear-gradient(90deg, #4caf50, #66bb6a)';
            steps.forEach((step) => {
                step.classList.add('done');
                step.classList.remove('active');
            });
        } else if (status === 'FAILED' || status === 'CANCELLED') {
            fill.style.background = '#dc3545';
        } else {
            fill.style.background = 'linear-gradient(90deg, #1976d2, #4fc3f7)';
        }
    }

    async startPolling(jobId) {
        // Stop existing polling
        this.stopPolling();

        this.isPolling = true;
        this.currentJobId = jobId;

        // Poll every 3 seconds
        this.pollInterval = setInterval(async () => {
            try {
                const status = await SimulationAPI.getSimulationStatus(jobId);
                if (status) {
                    this.updateJobStatus(status);

                    // Stop polling if terminal status
                    if (SimulationAPI.isTerminalStatus(status.status)) {
                        this.stopPolling();
                        if (status.status === 'COMPLETED') {
                            window.showToast('✅ Simulation completed successfully!', 'success');
                            // Show flood data (placeholder)
                            if (window.floodMap) {
                                window.floodMap.addFloodLayer({
                                    job_id: jobId,
                                    status: 'COMPLETED',
                                });
                            }
                        } else if (status.status === 'FAILED') {
                            window.showToast(
                                `❌ Simulation failed: ${status.error_message || 'Unknown error'}`,
                                'error'
                            );
                        }
                    }
                } else {
                    // Job not found
                    this.stopPolling();
                    window.showToast('Job not found', 'error');
                }
            } catch (error) {
                console.error('Polling error:', error);
                // Don't stop polling on network errors
            }
        }, 3000);
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
        const emptyMsg = historyList.querySelector('.empty-history');

        if (emptyMsg) {
            emptyMsg.remove();
        }

        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.jobId = job.job_id;

        const created = new Date(job.created_at);
        const timeStr = created.toLocaleString('vi-VN');

        item.innerHTML = `
            <div class="h-left">
                <span class="h-job-id">${job.job_id}</span>
                <span class="h-scenario">${job.scenario_name}</span>
            </div>
            <div class="h-right">
                <span class="h-status status-badge status-${job.status.toLowerCase()}">${job.status}</span>
                <span class="h-time">${timeStr}</span>
            </div>
        `;

        item.addEventListener('click', () => {
            // Load job status
            this.loadJob(job.job_id);
        });

        historyList.prepend(item);
    }

    async loadJob(jobId) {
        const status = await SimulationAPI.getSimulationStatus(jobId);
        if (status) {
            this.currentJobId = jobId;
            this.updateJobStatus(status);
            this.startPolling(jobId);
            window.showToast(`Đang tải job ${jobId}`, 'info');
        } else {
            window.showToast(`Không tìm thấy job ${jobId}`, 'error');
        }
    }

    async refreshHistory() {
        const btn = document.getElementById('refreshHistoryBtn');
        btn.classList.add('spinning');

        try {
            const jobs = await SimulationAPI.getSimulations();
            const historyList = document.getElementById('historyList');
            historyList.innerHTML = '';

            if (jobs.length === 0) {
                historyList.innerHTML = `
                    <div class="empty-history">
                        <i class="fas fa-inbox"></i>
                        <p>Chưa có mô phỏng nào</p>
                    </div>
                `;
                return;
            }

            jobs.forEach((job) => {
                this.addToHistory(job);
            });

            window.showToast(`Đã tải ${jobs.length} jobs`, 'success');
        } catch (error) {
            window.showToast('Không thể tải lịch sử', 'error');
        } finally {
            btn.classList.remove('spinning');
        }
    }
}

// Initialize on DOM ready
let simManager = null;

document.addEventListener('DOMContentLoaded', () => {
    simManager = new SimulationManager();

    // Form submit
    document.getElementById('simulationForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = {
            scenarioName: document.getElementById('scenarioName').value.trim(),
            rainfall: document.getElementById('rainfall').value,
            rainfallUnit: document.getElementById('rainfallUnit').value,
            duration: document.getElementById('duration').value,
            durationUnit: document.getElementById('durationUnit').value,
        };

        // Validate
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

    // Refresh history
    document.getElementById('refreshHistoryBtn').addEventListener('click', () => {
        simManager.refreshHistory();
    });

    // Load history on start
    setTimeout(() => {
        simManager.refreshHistory();
    }, 500);
});
// frontend/js/app.js

// ===== TOAST SYSTEM =====
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

// Make toast globally available
window.showToast = showToast;

// ===== API STATUS CHECK =====
async function checkApiStatus() {
    const statusEl = document.getElementById('apiStatus');
    const dot = document.querySelector('.status-dot');

    try {
        const response = await SimulationAPI.healthCheck();
        if (response && response.status === 'healthy') {
            dot.className = 'status-dot online';
            statusEl.textContent = 'API: Connected';
            statusEl.style.color = '#4caf50';
        } else {
            dot.className = 'status-dot offline';
            statusEl.textContent = 'API: Degraded';
            statusEl.style.color = '#ff9800';
        }
    } catch (error) {
        dot.className = 'status-dot offline';
        statusEl.textContent = 'API: Disconnected';
        statusEl.style.color = '#f44336';
        showToast('Không thể kết nối đến API Server', 'error', 5000);
    }
}

// ===== RESPONSIVE SIDEBAR TOGGLE =====
function setupResponsive() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebarBtn');

    // Auto-collapse on small screens
    if (window.innerWidth <= 768) {
        sidebar.classList.add('collapsed');
        const icon = toggleBtn.querySelector('i');
        icon.className = 'fas fa-chevron-right';
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
        }
    });
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
    // Ctrl + Enter: Submit form
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('simulationForm').dispatchEvent(new Event('submit'));
    }

    // Escape: Close sidebar on mobile
    if (e.key === 'Escape' && window.innerWidth <= 768) {
        document.getElementById('sidebar').classList.add('collapsed');
    }
});

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    // Check API status
    checkApiStatus();
    setInterval(checkApiStatus, 30000); // Check every 30 seconds

    // Setup responsive
    setupResponsive();

    // Console info
    console.log('🌊 Flood WebGIS HEC-RAS v1.0.0');
    console.log('📡 API:', API_BASE_URL);
    console.log('🗺️ Map initialized');

    // Auto-fill demo data
    if (!document.getElementById('scenarioName').value) {
        document.getElementById('scenarioName').value = 'Mưa 5mm 5h';
        document.getElementById('rainfall').value = 5;
        document.getElementById('duration').value = 5;
    }
});
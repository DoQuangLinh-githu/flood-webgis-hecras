// frontend/js/api.js

// ============================================================
// API BASE URL
// Tự động phát hiện:
//   - Nếu window.API_BASE_URL được set (từ index.html) -> dùng
//   - Nếu chạy trên cùng origin -> dùng origin hiện tại
//   - Fallback: http://localhost:8000
// ============================================================

function detectApiBaseUrl() {
    if (window.API_BASE_URL) {
        return window.API_BASE_URL;
    }
    // Nếu frontend được serve từ cùng backend (cùng port)
    // dùng origin hiện tại
    if (
        window.location.protocol === 'http:' ||
        window.location.protocol === 'https:'
    ) {
        // Nếu frontend đang chạy ở port khác (dev với Vite),
        // phải dùng URL cụ thể. Ở production, frontend và backend
        // cùng origin (Render serve cả 2), nên dùng origin.
        return window.location.origin;
    }
    return 'http://localhost:8000';
}

const API_BASE_URL = detectApiBaseUrl();

console.log('[api.js] API_BASE_URL =', API_BASE_URL);


class SimulationAPI {
    // --------------------------------------------------------
    // HEALTH
    // --------------------------------------------------------
    static async healthCheck() {
        try {
            const r = await fetch(`${API_BASE_URL}/api/health`);
            if (!r.ok) return null;
            return await r.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return null;
        }
    }

    // --------------------------------------------------------
    // RUN SIMULATION (async)
    // --------------------------------------------------------
    static async runSimulation(data) {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/simulations/run`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    body: JSON.stringify(data),
                }
            );

            if (!response.ok) {
                let msg = 'Failed to run simulation';
                try {
                    const err = await response.json();
                    msg = err.detail || msg;
                } catch (_) {}
                throw new Error(msg);
            }

            return await response.json();
        } catch (error) {
            console.error('Run simulation failed:', error);
            throw error;
        }
    }

    // --------------------------------------------------------
    // GET SIMULATION STATUS
    // --------------------------------------------------------
    static async getSimulationStatus(jobId) {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/simulations/${jobId}`
            );
            if (!response.ok) {
                if (response.status === 404) return null;
                throw new Error('Failed to fetch status');
            }
            return await response.json();
        } catch (error) {
            console.error('Get status failed:', error);
            return null;
        }
    }

    // --------------------------------------------------------
    // LIST ALL
    // --------------------------------------------------------
    static async getSimulations() {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/simulations`
            );
            if (!response.ok) throw new Error('Failed to list');
            return await response.json();
        } catch (error) {
            console.error('List simulations failed:', error);
            return [];
        }
    }

    // --------------------------------------------------------
    // GET HEC-RAS GEOJSON
    // --------------------------------------------------------
    static async getGeojson(jobId) {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/simulations/${jobId}/geojson`
            );
            if (!response.ok) {
                if (response.status === 404) return null;
                throw new Error('Failed to fetch geojson');
            }
            return await response.json();
        } catch (error) {
            console.error('Get geojson failed:', error);
            return null;
        }
    }

    // --------------------------------------------------------
    // HEC-RAS STATUS
    // --------------------------------------------------------
    static async getHecrasStatus() {
        try {
            const r = await fetch(
                `${API_BASE_URL}/api/simulations/hecras/status`
            );
            if (!r.ok) return null;
            return await r.json();
        } catch (e) {
            return null;
        }
    }

    // --------------------------------------------------------
    // HELPERS
    // --------------------------------------------------------
    static getStatusProgress(status) {
        const order = ['QUEUED', 'RUNNING', 'PROCESSING', 'COMPLETED'];
        const idx = order.indexOf(status);
        if (idx === -1) return 0;
        return ((idx + 1) / order.length) * 100;
    }

    static isTerminalStatus(status) {
        return ['COMPLETED', 'FAILED', 'CANCELLED'].includes(status);
    }
}
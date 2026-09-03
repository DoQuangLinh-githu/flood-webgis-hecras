// frontend/js/api.js

// Lấy API_URL từ biến môi trường hoặc dùng mặc định
const API_BASE_URL = window.API_BASE_URL || 
                     process.env.API_BASE_URL || 
                     'http://localhost:8000';

class SimulationAPI {
    static async healthCheck() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return null;
        }
    }

    static async createSimulation(data) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/simulations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create simulation');
            }

            return await response.json();
        } catch (error) {
            console.error('Create simulation failed:', error);
            throw error;
        }
    }

    static async runHECRASSimulation(data) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/simulations/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to run HEC-RAS simulation');
            }

            return await response.json();
        } catch (error) {
            console.error('Run HEC-RAS simulation failed:', error);
            throw error;
        }
    }

    static async getSimulations() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/simulations`);
            if (!response.ok) {
                throw new Error('Failed to fetch simulations');
            }
            return await response.json();
        } catch (error) {
            console.error('Get simulations failed:', error);
            return [];
        }
    }

    static async getSimulationStatus(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/simulations/${jobId}`);
            if (!response.ok) {
                if (response.status === 404) {
                    return null;
                }
                throw new Error('Failed to fetch job status');
            }
            return await response.json();
        } catch (error) {
            console.error('Get job status failed:', error);
            return null;
        }
    }

    static async cancelSimulation(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/simulations/${jobId}`, {
                method: 'DELETE',
            });
            return response.ok;
        } catch (error) {
            console.error('Cancel simulation failed:', error);
            return false;
        }
    }

    static getStatusOrder() {
        return ['QUEUED', 'RUNNING', 'PROCESSING', 'COMPLETED'];
    }

    static getStatusProgress(status) {
        const order = this.getStatusOrder();
        const index = order.indexOf(status);
        if (index === -1) return 0;
        return ((index + 1) / order.length) * 100;
    }

    static isTerminalStatus(status) {
        return ['COMPLETED', 'FAILED', 'CANCELLED'].includes(status);
    }
}
// frontend/js/map.js

class FloodMap {
    constructor(mapId) {
        this.map = L.map(mapId, {
            center: [10.8231, 106.6297], // TP.HCM
            zoom: 12,
            zoomControl: false,
        });

        // Base Layer
        this.baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors',
        }).addTo(this.map);

        // Layer Groups
        this.layers = {
            rivers: L.layerGroup().addTo(this.map),
            boundaries: L.layerGroup().addTo(this.map),
            flood: L.layerGroup().addTo(this.map),
        };

        // Sample data
        this.addSampleData();

        // Map events
        this.map.on('moveend', () => this.updateBounds());
    }

    addSampleData() {
        // Sample rivers (using VN-2000 approximate coordinates for Saigon River)
        const saigonRiver = L.polyline(
            [
                [10.95, 106.65],
                [10.85, 106.70],
                [10.75, 106.75],
                [10.65, 106.75],
                [10.55, 106.72],
            ],
            {
                color: '#2196f3',
                weight: 3,
                opacity: 0.8,
                smoothFactor: 1,
            }
        ).addTo(this.layers.rivers);

        const saigonRiver2 = L.polyline(
            [
                [10.82, 106.60],
                [10.78, 106.65],
                [10.72, 106.68],
                [10.65, 106.70],
            ],
            {
                color: '#2196f3',
                weight: 2,
                opacity: 0.6,
                smoothFactor: 1,
            }
        ).addTo(this.layers.rivers);

        // Sample boundaries (simplified districts)
        const districts = [
            [
                [10.90, 106.60],
                [10.90, 106.75],
                [10.80, 106.75],
                [10.80, 106.60],
                [10.90, 106.60],
            ],
            [
                [10.80, 106.60],
                [10.80, 106.75],
                [10.70, 106.75],
                [10.70, 106.60],
                [10.80, 106.60],
            ],
            [
                [10.70, 106.65],
                [10.70, 106.78],
                [10.60, 106.78],
                [10.60, 106.65],
                [10.70, 106.65],
            ],
        ];

        districts.forEach((coords, index) => {
            const color = ['#ff9800', '#4caf50', '#9c27b0'][index % 3];
            L.polygon(coords, {
                color: color,
                weight: 2,
                opacity: 0.6,
                fillOpacity: 0.1,
                fillColor: color,
            })
                .addTo(this.layers.boundaries)
                .bindPopup(`<b>Khu vực ${index + 1}</b>`);
        });
    }

    addFloodLayer(data) {
        // Clear existing flood layer
        this.layers.flood.clearLayers();

        if (!data) {
            this.showToast('Không có dữ liệu ngập lụt', 'warning');
            return;
        }

        // Sample flood data (simulated)
        const floodData = [
            { lat: 10.82, lng: 106.68, depth: 1.2 },
            { lat: 10.80, lng: 106.70, depth: 0.8 },
            { lat: 10.78, lng: 106.72, depth: 0.5 },
            { lat: 10.76, lng: 106.70, depth: 0.3 },
            { lat: 10.74, lng: 106.68, depth: 0.7 },
            { lat: 10.72, lng: 106.70, depth: 1.5 },
            { lat: 10.70, lng: 106.72, depth: 0.4 },
            { lat: 10.68, lng: 106.70, depth: 0.6 },
        ];

        const getColor = (depth) => {
            if (depth <= 0.3) return '#ffffb2';
            if (depth <= 0.5) return '#fecc5c';
            if (depth <= 1.0) return '#fd8d3c';
            if (depth <= 2.0) return '#f03b20';
            return '#bd0026';
        };

        const getRadius = (depth) => {
            return 50 + depth * 100;
        };

        floodData.forEach((point) => {
            const circle = L.circle([point.lat, point.lng], {
                radius: getRadius(point.depth),
                color: getColor(point.depth),
                weight: 1,
                opacity: 0.8,
                fillColor: getColor(point.depth),
                fillOpacity: 0.6,
            })
                .addTo(this.layers.flood)
                .bindPopup(`
                    <b>Độ sâu ngập:</b> ${point.depth.toFixed(1)} m<br>
                    <b>Vị trí:</b> ${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}
                `);
        });

        // Fit map to flood data
        const bounds = floodData.map((p) => [p.lat, p.lng]);
        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }

        this.showToast('Đã hiển thị dữ liệu ngập lụt', 'success');
    }

    clearFloodLayer() {
        this.layers.flood.clearLayers();
        this.showToast('Đã xóa lớp ngập lụt', 'info');
    }

    zoomIn() {
        this.map.zoomIn();
    }

    zoomOut() {
        this.map.zoomOut();
    }

    locateUser() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    this.map.setView([latitude, longitude], 15);
                    L.marker([latitude, longitude], {
                        icon: L.divIcon({
                            html: '<i class="fas fa-user" style="font-size:20px;color:#1976d2;"></i>',
                            className: 'location-marker',
                            iconSize: [30, 30],
                            iconAnchor: [15, 15],
                        }),
                    })
                        .addTo(this.map)
                        .bindPopup('Vị trí của bạn');
                },
                () => {
                    this.showToast('Không thể xác định vị trí', 'error');
                }
            );
        } else {
            this.showToast('Trình duyệt không hỗ trợ định vị', 'warning');
        }
    }

    updateBounds() {
        const bounds = this.map.getBounds();
        // Can be used to load data for visible area
    }

    showToast(message, type = 'info') {
        // Delegate to global toast function
        if (window.showToast) {
            window.showToast(message, type);
        }
    }
}

// Initialize map when DOM is ready
let floodMap = null;

document.addEventListener('DOMContentLoaded', () => {
    floodMap = new FloodMap('map');

    // Map control buttons
    document.getElementById('zoomInBtn')?.addEventListener('click', () => {
        floodMap.zoomIn();
    });

    document.getElementById('zoomOutBtn')?.addEventListener('click', () => {
        floodMap.zoomOut();
    });

    document.getElementById('locateBtn')?.addEventListener('click', () => {
        floodMap.locateUser();
    });

    document.getElementById('toggleSidebarBtn')?.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('collapsed');
        const btn = document.getElementById('toggleSidebarBtn');
        btn.querySelector('i').classList.toggle('fa-chevron-left');
        btn.querySelector('i').classList.toggle('fa-chevron-right');
    });
});
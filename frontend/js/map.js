// frontend/js/map.js

class FloodMap {
    constructor(mapId) {
        this.map = L.map(mapId, {
            center: [10.78, 106.70], // TP.HCM
            zoom: 11,
            zoomControl: false,
        });

        // Base layer — Esri World Imagery (vệ tinh, không API key)
        this.baseLayer = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            {
                maxZoom: 19,
                attribution: '© Esri, Maxar, Earthstar Geographics',
            }
        ).addTo(this.map);

        // Labels overlay (tên đường, địa danh)
        this.labelsLayer = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            {
                maxZoom: 19,
                opacity: 0.8,
            }
        ).addTo(this.map);

        // Layer groups
        this.layers = {
            flood: L.layerGroup().addTo(this.map),
        };

        this.legend = document.getElementById('mapLegend');
        this.floodBounds = null;
    }

    // ============================================================
    // FLOOD LAYER
    // ============================================================

    addFloodLayerFromGeojson(geojson) {
        this.layers.flood.clearLayers();

        if (!geojson || !geojson.features || geojson.features.length === 0) {
            window.showToast('Không có dữ liệu ngập', 'warning');
            return;
        }

        const features = geojson.features;

        // Màu theo độ sâu (m)
        const getColor = (d) => {
            if (d === null || d === undefined) return '#bdbdbd';
            if (d < 0.01) return null;            // khô -> bỏ
            if (d < 0.25) return '#ffffb2';
            if (d < 0.5)  return '#fecc5c';
            if (d < 1.0)  return '#fd8d3c';
            if (d < 1.5)  return '#f03b20';
            return '#bd0026';
        };

        const bounds = L.latLngBounds();
        let nWet = 0;
        let maxDepth = 0;

        features.forEach((feat) => {
            const coords = feat.geometry?.coordinates;
            if (!coords || coords.length < 2) return;

            const [lon, lat] = coords;
            const p = feat.properties || {};
            const depth = p.max_depth_m;

            if (depth !== null && depth !== undefined && depth > maxDepth) {
                maxDepth = depth;
            }

            const color = getColor(depth);
            if (!color) return;

            nWet++;

            const marker = L.circleMarker([lat, lon], {
                radius: 5,
                fillColor: color,
                color: '#333',
                weight: 0.5,
                fillOpacity: 0.8,
            });

            marker.bindPopup(`
                <b>Cell #${p.cell_id}</b><br>
                Độ sâu: <b>${depth !== null ? depth.toFixed(3) : '—'} m</b><br>
                Cao độ đáy: ${p.bottom_elev_m !== null ? p.bottom_elev_m.toFixed(2) : '—'} m<br>
                Mực nước max: ${p.max_wse_m !== null ? p.max_wse_m.toFixed(2) : '—'} m<br>
                Thời điểm max: ${p.t_peak_days !== null ? p.t_peak_days.toFixed(1) : '—'} ngày
            `);

            marker.addTo(this.layers.flood);
            bounds.extend([lat, lon]);
        });

        if (nWet > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }

        // Cập nhật legend info (nếu có)
        console.log(`[map] ${nWet} cells ngập, max depth = ${maxDepth.toFixed(2)} m`);

        window.showToast(
            `Hiển thị ${nWet} cells ngập (max ${maxDepth.toFixed(2)} m)`,
            'success'
        );
    }

    // ============================================================
    // CLEAR
    // ============================================================

    clearFloodLayer() {
        this.layers.flood.clearLayers();
        window.showToast('Đã xóa lớp ngập lụt', 'info');
    }

    // ============================================================
    // CONTROLS
    // ============================================================

    zoomIn() { this.map.zoomIn(); }
    zoomOut() { this.map.zoomOut(); }

    locateUser() {
        if (!navigator.geolocation) {
            window.showToast('Trình duyệt không hỗ trợ định vị', 'warning');
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                this.map.setView([latitude, longitude], 15);
                L.marker([latitude, longitude]).addTo(this.map).bindPopup('Vị trí của bạn');
            },
            () => window.showToast('Không thể xác định vị trí', 'error')
        );
    }

    setBaseMap(type) {
        // type: 'satellite' | 'street' | 'topo'
        this.map.removeLayer(this.baseLayer);

        const urls = {
            satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            street: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            topo: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        };

        this.baseLayer = L.tileLayer(urls[type] || urls.satellite, {
            maxZoom: 19,
            attribution: '© Esri',
        }).addTo(this.map);
    }
}


// ============================================================
// INIT
// ============================================================

let floodMap = null;

document.addEventListener('DOMContentLoaded', () => {
    floodMap = new FloodMap('map');
    window.floodMap = floodMap;

    document.getElementById('zoomInBtn')?.addEventListener('click', () => floodMap.zoomIn());
    document.getElementById('zoomOutBtn')?.addEventListener('click', () => floodMap.zoomOut());
    document.getElementById('locateBtn')?.addEventListener('click', () => floodMap.locateUser());

    document.getElementById('toggleSidebarBtn')?.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('collapsed');
        const btn = document.getElementById('toggleSidebarBtn');
        btn.querySelector('i').classList.toggle('fa-chevron-left');
        btn.querySelector('i').classList.toggle('fa-chevron-right');
    });
});
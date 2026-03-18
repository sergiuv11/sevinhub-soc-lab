// frontend/map.js

document.addEventListener('DOMContentLoaded', () => {
    const threatMapDiv = document.getElementById('threat-map');

    if (!threatMapDiv) {
        console.error("Threat map div not found.");
        return;
    }

    // Initialize the Leaflet map
    const map = L.map('threat-map').setView([20, 0], 2); // Centered a bit north

    // Add a tile layer (Dark mode tiles)
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenStreetMap</a> contributors',
        maxZoom: 20,
        id: 'mapbox/dark-v10',
        tileSize: 512,
        zoomOffset: -1
    }).addTo(map);

    let attackMarkers = [];

    function generateMockThreatData() {
        const attacks = [];
        const attackTypes = ['DDoS', 'Phishing', 'Malware', 'Ransomware'];
        const severities = ['Low', 'Medium', 'High', 'Critical'];

        // Example coordinates for major regions to simulate attacks between them
        const locations = [
            { name: "North America", lat: 40, lon: -100 },
            { name: "Europe", lat: 50, lon: 10 },
            { name: "Asia", lat: 30, lon: 100 },
            { name: "South America", lat: -20, lon: -60 },
            { name: "Africa", lat: 0, lon: 20 },
            { name: "Oceania", lat: -25, lon: 135 }
        ];

        for (let i = 0; i < 5; i++) { // Simulate 5 active attacks
            const source = locations[Math.floor(Math.random() * locations.length)];
            let target = locations[Math.floor(Math.random() * locations.length)];
            // Ensure source and target are different for visual effect
            while (target === source) {
                target = locations[Math.floor(Math.random() * locations.length)];
            }

            attacks.push({
                source_lat: source.lat + (Math.random() - 0.5) * 10, // Add some jitter
                source_lon: source.lon + (Math.random() - 0.5) * 10,
                target_lat: target.lat + (Math.random() - 0.5) * 10,
                target_lon: target.lon + (Math.random() - 0.5) * 10,
                attack_type: attackTypes[Math.floor(Math.random() * attackTypes.length)],
                severity: severities[Math.floor(Math.random() * severities.length)],
                timestamp: new Date().toISOString()
            });
        }
        return attacks;
    }

    function updateThreatMap() {
        const attacks = generateMockThreatData();

        // Clear existing markers and polylines
        attackMarkers.forEach(marker => marker.remove());
        attackMarkers = [];

        attacks.forEach(attack => {
            const markerColor = {
                'Low': 'var(--success-color)',
                'Medium': 'orange',
                'High': 'var(--alert-color)',
                'Critical': 'darkred'
            }[attack.severity] || 'gray';

            // Create a custom icon for the attack
            const attackIcon = L.divIcon({
                className: 'custom-attack-icon',
                html: `<div style="background-color: ${markerColor}; width: 10px; height: 10px; border-radius: 50%; border: 1px solid white; animation: pulse 1.5s infinite;"></div>`,
                iconSize: [12, 12],
                popupAnchor: [0, -6]
            });

            // Add a marker for the target location
            const marker = L.marker([attack.target_lat, attack.target_lon], { icon: attackIcon }).addTo(map);
            marker.bindPopup(`
                <b>Attack Type:</b> ${attack.attack_type}<br>
                <b>Severity:</b> ${attack.severity}<br>
                <b>Source:</b> Lat: ${attack.source_lat.toFixed(2)}, Lon: ${attack.source_lon.toFixed(2)}<br>
                <b>Target:</b> Lat: ${attack.target_lat.toFixed(2)}, Lon: ${attack.target_lon.toFixed(2)}<br>
                <b>Time:</b> ${new Date(attack.timestamp).toLocaleTimeString()}
            `);
            attackMarkers.push(marker);

            // Draw a polyline from source to target
            const polyline = L.polyline([[attack.source_lat, attack.source_lon], [attack.target_lat, attack.target_lon]], { color: markerColor, weight: 1, opacity: 0.7 }).addTo(map);
            attackMarkers.push(polyline); // Keep track of polylines too
        });
    }

    // Add CSS for pulse animation
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.5); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    // Initial update and periodic refresh
    updateThreatMap();
    setInterval(updateThreatMap, 5000); // Refresh every 5 seconds
});

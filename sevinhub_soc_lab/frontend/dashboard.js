// frontend/dashboard.js

let clientSideCaseHistory = [];

document.addEventListener('DOMContentLoaded', () => {
    console.log("Dashboard script loaded.");

    // Expose a function for analyst.js to add history items
    window.addClientSideCaseHistory = (item) => {
        clientSideCaseHistory.unshift(item); // Add to the beginning
        fetchCaseHistory(); // Refresh the display
    };

    // Function to fetch and update SOC status (mocked for client-side)
    async function updateSOCStatus() {
        // Simulate fetching data
        const soc_score = Math.floor(Math.random() * 50) + 50; // 50-99
        let threat_level = 'Low';
        if (soc_score < 60) threat_level = 'High';
        else if (soc_score < 75) threat_level = 'Medium';

        document.getElementById('threat-level').textContent = threat_level;
        document.getElementById('threat-level').dataset.level = threat_level; // For styling
        document.getElementById('soc-score').textContent = soc_score;
    }

    // Function to display case history (from client-side array)
    async function fetchCaseHistory() {
        const tableBody = document.querySelector('#case-history-table tbody');
        tableBody.innerHTML = ''; // Clear existing rows

        if (clientSideCaseHistory.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5">No case history yet. Analyze an indicator!</td></tr>';
            return;
        }

        clientSideCaseHistory.forEach(item => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = item.indicator;
            row.insertCell().textContent = item.threat_score;
            row.insertCell().textContent = item.classification;
            row.insertCell().textContent = new Date(item.timestamp).toLocaleString();
            row.insertCell().textContent = item.notes || '-';
        });
    }

    // Placeholder for Attack Chart (mocked data)
    let attackChartInstance;
    function createAttackChart() {
        const ctx = document.getElementById('attack-chart').getContext('2d');
        if (attackChartInstance) { attackChartInstance.destroy(); } // Destroy old chart instance

        attackChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Malware', 'Phishing', 'DDoS', 'Ransomware', 'Insider Threat'],
                datasets: [{
                    label: 'Attack Types',
                    data: [Math.floor(Math.random() * 20), Math.floor(Math.random() * 20), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 5)],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: 'var(--text-color)' }
                    },
                    x: {
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: 'var(--text-color)' }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'var(--text-color)'
                        }
                    }
                }
            }
        });
    }

    // Initial calls
    updateSOCStatus();
    fetchCaseHistory();
    createAttackChart();

    // Refresh data periodically
    setInterval(updateSOCStatus, 5000);
    setInterval(createAttackChart, 10000); // Refresh chart data
});

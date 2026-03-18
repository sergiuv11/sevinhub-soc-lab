// frontend/simulator.js

document.addEventListener('DOMContentLoaded', () => {
    const incidentListDiv = document.getElementById('incident-list');
    const incidentResponseArea = document.getElementById('incident-response-area');
    let currentIncidents = [];
    let currentSOCScore = 75; // Initial SOC score

    async function fetchAndDisplayIncidents() {
        try {
            const response = await fetch('/incidents');
            const data = await response.json();

            if (!response.ok) {
                incidentListDiv.innerHTML = `<p style="color: var(--alert-color);">Error: ${data.detail || data.message || 'Failed to load incidents.'}</p>`;
                return;
            }

            currentIncidents = data.incidents || [];
            incidentListDiv.innerHTML = ''; // Clear previous incidents

            if (currentIncidents.length === 0) {
                incidentListDiv.innerHTML = '<p>No active incidents.</p>';
                return;
            }

            currentIncidents.forEach(incident => {
                const incidentDiv = document.createElement('div');
                incidentDiv.className = 'incident-item';
                incidentDiv.innerHTML = `
                    <h3>${incident.title}</h3>
                    <p><strong>Evidence:</strong> ${incident.evidence}</p>
                    <div class="simulator-actions">
                        ${incident.actions.map(action => `<button data-incident-id="${incident.id}" data-action="${action}">${action}</button>`).join('')}
                    </div>
                    <div id="outcome-${incident.id}" class="simulator-outcome"></div>
                `;
                incidentListDiv.appendChild(incidentDiv);
            });

            // Add event listeners for response buttons
            incidentListDiv.querySelectorAll('.simulator-actions button').forEach(button => {
                button.addEventListener('click', handleResponseAction);
            });

        } catch (error) {
            console.error('Error fetching incidents:', error);
            incidentListDiv.innerHTML = '<p style="color: var(--alert-color);">Failed to connect to incident simulator service.</p>';
        }
    }

    async function handleResponseAction(event) {
        const incidentId = event.target.dataset.incidentId;
        const action = event.target.dataset.action;
        const outcomeDiv = document.getElementById(`outcome-${incidentId}`);
        outcomeDiv.innerHTML = '<p>Submitting response...</p>';

        try {
            const response = await fetch(`/incidents/${incidentId}/respond`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: action }),
            });
            const result = await response.json();

            if (response.ok) {
                let outcomeHtml = `<h3>Outcome: ${result.outcome}</h3>`;
                outcomeHtml += `<p><strong>Explanation:</strong> ${result.explanation}</p>`;
                outcomeHtml += `<p><strong>SOC Score Change:</strong> <span style="color: ${result.soc_score_change >= 0 ? 'var(--success-color)' : 'var(--alert-color)'};">${result.soc_score_change >= 0 ? '+' : ''}${result.soc_score_change}</span></p>`;
                outcomeDiv.innerHTML = outcomeHtml;

                // Update global SOC score display
                if (window.updateSOCStatus) window.updateSOCStatus();

                // Optionally, disable buttons for this incident after response
                event.target.closest('.simulator-actions').querySelectorAll('button').forEach(btn => btn.disabled = true);

            } else {
                outcomeDiv.innerHTML = `<p style="color: var(--alert-color);">Error: ${result.detail || result.message || 'Unknown error during response.'}</p>`;
            }

        } catch (error) {
            console.error('Error during incident response request:', error);
            outcomeDiv.innerHTML = '<p style="color: var(--alert-color);">Failed to connect to incident response service.</p>';
        }
    }

    // Initial fetch
    fetchAndDisplayIncidents();

    // Refresh incidents periodically if needed
    // setInterval(fetchAndDisplayIncidents, 30000);
});

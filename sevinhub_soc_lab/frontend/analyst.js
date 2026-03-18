// frontend/analyst.js

document.addEventListener('DOMContentLoaded', () => {
    const analyzeButton = document.getElementById('analyze-button');
    const analystInput = document.getElementById('analyst-input');
    const analystResults = document.getElementById('analyst-results');

    const PHISHING_KEYWORDS = ['login', 'verify', 'account update', 'security alert', 'suspicious activity', 'invoice', 'payment', 'urgent'];
    const SUSPICIOUS_TLDS = ['.xyz', '.top', '.icu', '.club', '.online', '.site', '.biz', '.info'];
    const BLACKLISTED_IPS = ['192.0.2.1', '198.51.100.1', '203.0.113.1']; // Example blacklisted IPs
    const RECENT_DOMAIN_THRESHOLD_DAYS = 30; // For simulation, assume a domain is "recent" if it contains a specific placeholder

    // Helper to simulate domain registration date check
    function isRecentDomain(domain) {
        // In a real scenario, this would query a WHOIS API or similar.
        // For this demo, we'll make it deterministic based on content.
        return domain.includes('newlyregistered') || domain.includes('recent-reg');
    }

    // Helper to simulate multiple redirects for a URL
    function hasMultipleRedirects(url) {
        // In a real scenario, this would involve making HTTP requests and following redirects.
        // For this demo, we'll make it deterministic based on content.
        return url.includes('redirect=true');
    }

    // Core analysis logic (client-side simulation)
    function analyzeIndicatorClientSide(indicator) {
        let threatScore = 0;
        const indicatorsDetected = [];
        let classification = 'Benign';
        let explanation = 'No immediate threats detected based on current rules.';
        const recommendedActions = ['Monitor activity', 'Educate user'];

        const lowerIndicator = indicator.toLowerCase();

        // Rule: Recent domain
        if (indicator.includes('.')) { // Simple check for domain/URL
            const domainMatch = indicator.match(/(?:https?:\/\/)?(?:www\.)?([^/]+)/);
            if (domainMatch && domainMatch[1]) {
                const domain = domainMatch[1].split(':')[0]; // Remove port if present
                if (isRecentDomain(domain)) {
                    threatScore += 20;
                    indicatorsDetected.push('Recent Domain Registration');
                    explanation = 'The domain appears to be recently registered, which is often associated with malicious activity.';
                    recommendedActions.push('Verify domain registration details', 'Block domain if suspicious');
                }
            }
        }

        // Rule: Phishing keywords
        const detectedKeywords = PHISHING_KEYWORDS.filter(keyword => lowerIndicator.includes(keyword));
        if (detectedKeywords.length > 0) {
            threatScore += 15 * detectedKeywords.length; // Scale score by number of keywords
            indicatorsDetected.push(`Phishing Keywords: ${detectedKeywords.join(', ')}`);
            explanation += ' Contains keywords commonly used in phishing attempts.';
            recommendedActions.push('Warn user about phishing risk', 'Report email/message as phishing');
        }

        // Rule: Suspicious TLD
        const detectedTLDs = SUSPICIOUS_TLDS.filter(tld => lowerIndicator.includes(tld));
        if (detectedTLDs.length > 0) {
            threatScore += 10 * detectedTLDs.length; // Scale score by number of TLDs
            indicatorsDetected.push(`Suspicious TLDs: ${detectedTLDs.join(', ')}`);
            explanation += ' Uses a suspicious Top-Level Domain (TLD).';
            recommendedActions.push('Block TLD if appropriate', 'Exercise caution with emails from this TLD');
        }

        // Rule: Blacklisted IP
        const detectedBlacklistedIPs = BLACKLISTED_IPS.filter(ip => indicator.includes(ip));
        if (detectedBlacklistedIPs.length > 0) {
            threatScore += 30;
            indicatorsDetected.push(`Blacklisted IP: ${detectedBlacklistedIPs.join(', ')}`);
            explanation += ' Contains an IP address known to be blacklisted.';
            recommendedActions.push('Block IP at firewall/proxy', 'Investigate source of connection');
        }

        // Rule: Multiple redirects (for URLs)
        if (indicator.startsWith('http') && hasMultipleRedirects(lowerIndicator)) {
            threatScore += 10;
            indicatorsDetected.push('Multiple Redirects Detected');
            explanation += ' The URL appears to involve multiple redirects, a common tactic for obfuscating malicious links.';
            recommendedActions.push('Do not click the link', 'Use a sandbox environment to analyze URL');
        }

        // Determine classification based on threat score
        if (threatScore >= 80) {
            classification = 'Critical Threat';
        } else if (threatScore >= 60) {
            classification = 'High Threat';
        } else if (threatScore >= 40) {
            classification = 'Medium Threat';
        } else if (threatScore >= 10) {
            classification = 'Low Threat';
        } else {
            classification = 'Benign';
        }

        // Ensure threat score is within bounds
        threatScore = Math.min(100, Math.max(0, threatScore));

        return {
            threat_score: threatScore,
            classification: classification,
            indicators_detected: indicatorsDetected.length > 0 ? indicatorsDetected : ['None'],
            recommended_actions: recommendedActions.length > 0 ? recommendedActions : ['No specific actions required'],
            explanation: explanation.trim()
        };
    }

    if (analyzeButton) {
        analyzeButton.addEventListener('click', async () => {
            const indicator = analystInput.value.trim();
            if (!indicator) {
                analystResults.innerHTML = '<p style="color: var(--alert-color);">Please enter an indicator to analyze.</p>';
                return;
            }

            analystResults.innerHTML = '<p>Analyzing... please wait.</p>';

            // Perform client-side analysis
            const result = analyzeIndicatorClientSide(indicator);

            let output = `<h3>Analysis Result for: ${indicator}</h3>`;
            output += `<p><strong>Threat Score:</strong> <span style="color: ${result.threat_score > 70 ? 'var(--alert-color)' : result.threat_score > 40 ? 'orange' : 'var(--success-color)'};">${result.threat_score}</span></p>`;
            output += `<p><strong>Classification:</strong> ${result.classification}</p>`;
            output += `<p><strong>Indicators Detected:</strong> ${result.indicators_detected.join(', ')}</p>`;
            output += `<p><strong>Recommended Actions:</strong> ${result.recommended_actions.join(', ')}</p>`;
            output += `<p><strong>Explanation:</strong> ${result.explanation}</p>`;
            analystResults.innerHTML = output;

            // Simulate saving to case history
            const newHistoryItem = {
                indicator: indicator,
                threat_score: result.threat_score,
                classification: result.classification,
                timestamp: new Date().toISOString(),
                notes: `Client-side analysis. ${result.explanation}`
            };

            // This will only update the display, not persistent storage without a backend
            if (window.addClientSideCaseHistory) {
                window.addClientSideCaseHistory(newHistoryItem);
            }
        });
    }
});

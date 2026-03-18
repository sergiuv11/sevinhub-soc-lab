from flask import Flask, render_template, request, jsonify
import socket
import dns.resolver
import re
from urllib.parse import urlparse
import ipaddress
import whois
from datetime import datetime
import ssl
import requests

app = Flask(__name__)

# Private IP ranges to prevent SSRF
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8') # Loopback
]

# Suspicious keywords for phishing detection
SUSPICIOUS_KEYWORDS = [
    "login", "verify", "secure", "account", "bank",
    "update", "password", "confirm", "signin", "webmail"
]

def is_private_ip(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for private_range in PRIVATE_IP_RANGES:
            if ip_obj in private_range:
                return True
        return False
    except ValueError:
        return False

def get_whois_info(domain):
    whois_data = {
        "creation_date": None,
        "domain_age_days": None,
        "registrar": None
    }
    try:
        w = whois.whois(domain)
        if w.creation_date:
            if isinstance(w.creation_date, list):
                creation_date = w.creation_date[0]
            else:
                creation_date = w.creation_date

            whois_data["creation_date"] = creation_date.strftime('%Y-%m-%d')
            time_difference = datetime.now() - creation_date
            whois_data["domain_age_days"] = time_difference.days

        if w.registrar:
            whois_data["registrar"] = w.registrar

    except Exception as e:
        pass
    return whois_data

def get_ssl_info(hostname):
    ssl_info = {
        "issuer": None,
        "expiration_date": None,
        "days_until_expiration": None
    }
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                issuer_list = cert.get('issuer', [])
                issuer_common_name = None
                for item in issuer_list:
                    for sub_item in item:
                        if sub_item[0] == 'commonName':
                            issuer_common_name = sub_item[1]
                            break
                    if issuer_common_name:
                        break
                ssl_info["issuer"] = issuer_common_name if issuer_common_name else 'N/A'

                not_after_str = cert.get('notAfter')
                if not_after_str:
                    expiration_date = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')
                    ssl_info["expiration_date"] = expiration_date.strftime('%Y-%m-%d')
                    
                    time_until_expiration = expiration_date - datetime.now()
                    ssl_info["days_until_expiration"] = time_until_expiration.days

    except ssl.SSLError as e:
        ssl_info["issuer"] = f"SSL Error: {e}"
    except socket.timeout:
        ssl_info["issuer"] = "SSL Error: Connection timed out"
    except Exception as e:
        ssl_info["issuer"] = f"SSL Error: {e}"

    return ssl_info

KNOWN_HOSTING_PROVIDERS = ["amazon", "google", "microsoft", "digitalocean", "linode", "vultr", "hetzner", "ovh"]

def get_ip_geolocation(ip_address):
    geo_info = {
        "country": None,
        "isp": None,
        "hosting": None
    }
    if not ip_address or is_private_ip(ip_address):
        return geo_info

    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=country,isp,hosting", timeout=3)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            geo_info["country"] = data.get('country')
            geo_info["isp"] = data.get('isp')
            geo_info["hosting"] = "Yes" if data.get('hosting') else "No"

    except requests.exceptions.RequestException as e:
        pass
    except Exception as e:
        pass
    return geo_info

def calculate_risk_score(results):
    score = 0
    max_score = 100

    if "Blocked:" in " ".join(results["security_hints"]):
        return max_score

    if not results["https_used"]:
        score += 20
    
    if results["whois_info"]["domain_age_days"] is not None:
        if results["whois_info"]["domain_age_days"] < 30:
            score += 20
        elif results["whois_info"]["domain_age_days"] < 90:
            score += 10
    else:
        score += 5

    keyword_count = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in results["url"].lower())
    if keyword_count >= 3:
        score += 25
    elif keyword_count == 2:
        score += 15
    elif keyword_count == 1:
        score += 5

    if any("Error" in str(record) for records in results["dns_records"].values() for record in records):
        score += 15
    elif any("No record found" in str(record) for records in results["dns_records"].values() for record in records):
        score += 5

    if results["https_used"] and results["ssl_info"]["days_until_expiration"] is not None:
        if results["ssl_info"]["days_until_expiration"] < 7:
            score += 10
        elif results["ssl_info"]["days_until_expiration"] < 15:
            score += 5
    elif results["https_used"] and "SSL Error" in results["ssl_info"]["issuer"]:
        score += 10

    if results["domain"] and results["domain"].count('-') > 3:
        score += 5

    if results["domain"] and len(results["domain"].split('.')[:-1]) > 2 and max(len(s) for s in results["domain"].split('.')[:-1]) > 15:
        score += 5

    if results["domain"] and re.fullmatch(r'\d+(\.\d+)+', results["domain"]):
        score += 5
    
    # Safely access ip_geolocation and its 'hosting' key
    if results.get("ip_geolocation", {}).get("hosting") == "Yes":
        # Safely access isp_lower
        isp_lower = results.get("ip_geolocation", {}).get("isp", "").lower()
        if any(provider in isp_lower for provider in KNOWN_HOSTING_PROVIDERS):
            score += 5

    return min(score, max_score)

def analyze_url(url):
    results = {
        "url": url,
        "https_used": False,
        "domain": None,
        "ip_address": None,
        "dns_records": {},
        "security_hints": [],
        "whois_info": {},
        "ssl_info": {},
        "ip_geolocation": {},
        "risk_score": 0
    }

    parsed_url = urlparse(url)
    scheme = parsed_url.scheme.lower()
    netloc = parsed_url.netloc.lower()

    if scheme not in ['http', 'https']:
        results["security_hints"].append(f"Blocked: Potentially dangerous scheme '{scheme}' detected. Only http(s) URLs are allowed.")
        results["risk_score"] = calculate_risk_score(results)
        return results

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
        results["security_hints"].append("URL did not specify http(s) protocol. Defaulting to http for initial analysis.")

    if scheme == "https":
        results["https_used"] = True
    else:
        results["security_hints"].append("Missing HTTPS: The URL does not use HTTPS, which is less secure.")

    results["domain"] = netloc
    if not results["domain"]:
        results["security_hints"].append("Could not extract domain from URL.")
        results["risk_score"] = calculate_risk_score(results)
        return results

    if len(results["domain"].split('.')[0]) > 15:
        results["security_hints"].append(f"Suspiciously long domain segment: '{results['domain'].split('.')[0]}'.")

    try:
        resolved_ip = socket.gethostbyname(results["domain"])
        results["ip_address"] = resolved_ip

        if is_private_ip(resolved_ip):
            results["security_hints"].append(f"Blocked: Resolved IP address ({resolved_ip}) is a private or loopback address. SSRF attempt prevented.")
            results["risk_score"] = calculate_risk_score(results)
            return results

        if results["domain"] == "localhost" or resolved_ip == "127.0.0.1":
            results["security_hints"].append(f"Blocked: URL resolves to localhost ({resolved_ip}). SSRF attempt prevented.")
            results["risk_score"] = calculate_risk_score(results)
            return results

    except socket.gaierror:
        results["security_hints"].append("Could not resolve IP address for the domain.")
    except Exception as e:
        results["security_hints"].append(f"Error during IP resolution: {e}")
        results["risk_score"] = calculate_risk_score(results)
        return results

    try:
        for record_type in ['A', 'AAAA', 'MX', 'NS']:
            try:
                answers = dns.resolver.resolve(results["domain"], record_type)
                results["dns_records"][record_type] = [str(r) for r in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                results["dns_records"][record_type] = ["No record found"]
            except Exception as e:
                results["dns_records"][record_type] = [f"Error: {e}"]
    except Exception as e:
        results["security_hints"].append(f"Error during general DNS lookup: {e}")

    whois_data = get_whois_info(results["domain"])
    results["whois_info"] = whois_data

    if whois_data["domain_age_days"] is not None and whois_data["domain_age_days"] < 90:
        results["security_hints"].append("Recently registered domain (< 90 days old) — possible phishing risk.")

    if results["https_used"] and results["domain"]:
        ssl_data = get_ssl_info(results["domain"])
        results["ssl_info"] = ssl_data
        if ssl_data["days_until_expiration"] is not None and ssl_data["days_until_expiration"] < 15:
            results["security_hints"].append("SSL certificate expiring soon (< 15 days).")

    keyword_count = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in url.lower())
    if keyword_count >= 2:
        results["security_hints"].append(f"Possible phishing pattern detected ({keyword_count} suspicious keywords found).")
    
    if results["domain"]:
        if results["domain"].count('-') > 3:
            results["security_hints"].append("Excessive hyphens in domain name — possible phishing indicator.")

        domain_parts = results["domain"].split('.')
        if len(domain_parts) > 2 and max(len(s) for s in domain_parts[:-1]) > 15:
            results["security_hints"].append("Long subdomain(s) detected — possible obfuscation or phishing indicator.")
        
        if re.fullmatch(r'\d+(\.\d+)+', results["domain"]):
             results["security_hints"].append("Domain name appears to be numeric (like an IP) — possible malicious intent.")
    
    if results["ip_address"] and not is_private_ip(results["ip_address"]):
        ip_geo_data = get_ip_geolocation(results["ip_address"])
        results["ip_geolocation"] = ip_geo_data
        if results.get("ip_geolocation", {}).get("hosting") == "Yes": # Safely access hosting
            isp_lower = results.get("ip_geolocation", {}).get("isp", "").lower() # Safely access isp
            if any(provider in isp_lower for provider in KNOWN_HOSTING_PROVIDERS):
                results["security_hints"].append("Hosted infrastructure (cloud/VPS) — common for phishing and malicious sites.")

    results["risk_score"] = calculate_risk_score(results)

    return results

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', results=None)

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form['url_input']
    analysis_results = analyze_url(url)
    return render_template('index.html', results=analysis_results)

# New API Endpoint
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    
    url = data['url']
    analysis_results = analyze_url(url)

    # Construct the desired API output, safely accessing nested dictionary keys
    api_output = {
        "https_used": analysis_results["https_used"],
        "domain": analysis_results["domain"],
        "ip_address": analysis_results["ip_address"],
        "domain_age_days": analysis_results.get("whois_info", {}).get("domain_age_days"),
        "ssl_issuer": analysis_results.get("ssl_info", {}).get("issuer"),
        "ssl_expiration_date": analysis_results.get("ssl_info", {}).get("expiration_date"),
        "ssl_days_until_expiration": analysis_results.get("ssl_info", {}).get("days_until_expiration"),
        "risk_score": analysis_results["risk_score"],
        "security_hints": analysis_results["security_hints"],
        "country": analysis_results.get("ip_geolocation", {}).get("country"),
        "isp": analysis_results.get("ip_geolocation", {}).get("isp"),
        "hosting": analysis_results.get("ip_geolocation", {}).get("hosting")
    }

    return jsonify(api_output), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

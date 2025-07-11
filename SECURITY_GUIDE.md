# 🔒 Security Guide - VPN Protection

The Awesome Web Scraper includes built-in security measures to protect your identity and prevent accidental exposure of your home IP address.

---

## 🛡️ **VPN Security Check**

### **Why VPN Protection?**
- **Privacy:** Prevents websites from seeing your real IP
- **Security:** Protects against IP-based tracking and blocking
- **Anonymity:** Ensures scraping activities are not linked to your identity
- **Legal Protection:** Adds layer of protection for research activities

### **How It Works**
The scraper automatically checks your public IP address before any scraping activity:

1. **🔍 IP Detection:** Queries multiple IP services for reliability
2. **🚨 Home IP Block:** Compares against your known home IP (`23.115.156.177`)
3. **🛑 Immediate Block:** Exits if home IP is detected
4. **✅ VPN Approval:** Proceeds only if different IP is detected

---

## 🚀 **Usage Examples**

### **Normal Operation (VPN Required)**
```bash
# This will be BLOCKED if running from home IP
$ python master_scraper.py example.com
🚨 BLOCKED: Running from home IP (23.115.156.177). VPN required!

🛑 SCRAPING BLOCKED FOR SECURITY
==================================================
For security reasons, scraping is not allowed from your home IP.
Please connect to VPN before running the scraper.

Home IP (BLOCKED): 23.115.156.177
Current IP: 23.115.156.177

💡 Solutions:
  1. Connect to VPN
  2. Use a proxy service
  3. Run from a different network
  4. Use --skip-vpn-check for testing (NOT RECOMMENDED)
==================================================
```

### **With VPN Active**
```bash
# This will proceed when VPN is connected
$ python master_scraper.py example.com
🔒 VPN Check: ✅ Active (IP: 185.220.101.32)
🕷️ Master Web Scraper
==================================================
Target URL: example.com
Methods: scrapy → pydoll → playwright
Output: summary
==================================================
```

### **Testing Mode (NOT RECOMMENDED)**
```bash
# For testing only - bypasses VPN check
$ python master_scraper.py example.com --skip-vpn-check
⚠️  VPN Check: SKIPPED (--skip-vpn-check used)
🕷️ Master Web Scraper
==================================================
# ... continues scraping ...
```

---

## 🔧 **VPN Checker Tool**

### **Standalone Usage**
```bash
# Check VPN status manually
$ python vpn_checker.py
🔒 VPN Status Checker
==============================
🏠 Home IP (BLOCKED): 23.115.156.177
⏱️  Timeout: 10.0s

🚨 BLOCKED: Running from home IP (23.115.156.177). VPN required!
🚫 Scraping is BLOCKED
```

### **Quiet Mode (for scripts)**
```bash
# Returns exit code 0 if VPN active, 1 if blocked
$ python vpn_checker.py --quiet
$ echo $?
1  # Blocked (home IP detected)

# With timeout
$ python vpn_checker.py --timeout 5 --quiet
```

---

## 🌐 **API Service Security**

The API service also includes VPN protection for all scraping tasks:

### **API Request**
```bash
$ curl -X POST "http://localhost:8000/scrape" \
       -H "Content-Type: application/json" \
       -d '{"url": "https://example.com"}'
```

### **VPN Check Failure Response**
```json
{
  "task_id": "task_1720728000123",
  "status": "failed",
  "message": "Task failed",
  "error": "VPN CHECK FAILED: BLOCKED: Running from home IP (23.115.156.177). VPN required!"
}
```

### **VPN Check Success Response**
```json
{
  "task_id": "task_1720728000456", 
  "status": "started",
  "message": "Scraping task started for https://example.com",
  "estimated_completion": "2025-07-11T16:15:30.123456"
}
```

---

## 🔍 **IP Detection Services**

The VPN checker uses multiple services for reliability:

1. **httpbin.org/ip** - Returns JSON format
2. **ipinfo.io/ip** - Plain text IP
3. **api.ipify.org** - Plain text IP
4. **icanhazip.com** - Plain text IP
5. **ifconfig.me/ip** - Plain text IP

**Fallback Strategy:** If one service fails, tries the next automatically.

---

## ⚙️ **Configuration**

### **Home IP Address**
```python
# In vpn_checker.py
BLOCKED_HOME_IP = "23.115.156.177"
```

**To change the blocked IP:**
1. Edit `vpn_checker.py`
2. Update the `BLOCKED_HOME_IP` constant
3. Save and restart services

### **Timeout Settings**
```bash
# Custom timeout for IP checks
$ python vpn_checker.py --timeout 15
```

### **Multiple Home IPs**
If you have multiple home IPs to block:

```python
# In vpn_checker.py - modify the check_vpn_status method
BLOCKED_HOME_IPS = ["23.115.156.177", "192.168.1.100", "another.ip.here"]

if current_ip in BLOCKED_HOME_IPS:
    return False, f"🚨 BLOCKED: Running from home IP ({current_ip}). VPN required!", current_ip
```

---

## 🛠️ **Integration Examples**

### **Custom Scripts**
```python
#!/usr/bin/env python3
from vpn_checker import require_vpn, check_vpn_quietly

# Method 1: Enforce VPN (exits on failure)
current_ip = require_vpn()
print(f"Proceeding with IP: {current_ip}")

# Method 2: Check quietly (returns None on failure)
current_ip = check_vpn_quietly()
if current_ip:
    print(f"VPN active: {current_ip}")
else:
    print("VPN check failed or home IP detected")

# Method 3: Async check
import asyncio
from vpn_checker import async_check_vpn

async def main():
    is_vpn_active, message, current_ip = await async_check_vpn()
    if is_vpn_active:
        print(f"VPN OK: {current_ip}")
    else:
        print(f"VPN Failed: {message}")

asyncio.run(main())
```

### **Shell Scripts**
```bash
#!/bin/bash
# check_and_scrape.sh

echo "Checking VPN status..."
python vpn_checker.py --quiet

if [ $? -eq 0 ]; then
    echo "✅ VPN active, proceeding with scraping"
    python master_scraper.py "$1"
else
    echo "❌ VPN check failed, aborting"
    exit 1
fi
```

### **Docker Integration**
```dockerfile
# Dockerfile
FROM python:3.11-slim

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY . .

# VPN check as health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python vpn_checker.py --quiet || exit 1

CMD ["python", "api_service.py"]
```

---

## 🚨 **Security Best Practices**

### **1. Always Use VPN**
```bash
# GOOD: VPN protection enabled
python master_scraper.py target-site.com

# BAD: VPN protection bypassed
python master_scraper.py target-site.com --skip-vpn-check
```

### **2. Monitor IP Changes**
```bash
# Check IP before and after VPN connection
python vpn_checker.py

# Connect to VPN
sudo openvpn my-vpn-config.ovpn

# Verify IP changed
python vpn_checker.py
```

### **3. Use Different VPN Servers**
```bash
# Rotate VPN servers for different scraping sessions
python master_scraper.py site1.com  # Server A
# Change VPN server
python master_scraper.py site2.com  # Server B
```

### **4. Log VPN Usage**
```bash
# Enable verbose logging to track IP usage
python master_scraper.py site.com --verbose
tail -f scraper.log | grep VPN
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. VPN Check Timeout**
```bash
# Increase timeout for slow connections
python vpn_checker.py --timeout 30
```

#### **2. IP Service Failures**
```
❌ Could not determine current IP address
```
**Solution:** Check internet connection, try again

#### **3. False Positives**
If the checker blocks when you're actually on VPN:
```bash
# Check what IP is being detected
python vpn_checker.py
```
Ensure the detected IP is not `23.115.156.177`

#### **4. Emergency Bypass**
For testing or emergency situations:
```bash
# Temporary bypass (NOT for production)
python master_scraper.py site.com --skip-vpn-check
```

### **Debug Mode**
```bash
# Enable debug logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from vpn_checker import require_vpn
require_vpn()
"
```

---

## 📊 **Security Monitoring**

### **Log Analysis**
```bash
# Check VPN usage in logs
grep "VPN Check" scraper.log

# Monitor blocked attempts
grep "BLOCKED" scraper.log

# Track IP changes
grep "Current public IP" scraper.log
```

### **Statistics**
```bash
# Get scraping statistics (includes IP info)
python data_retriever.py --stats

# Search for VPN-related entries
python data_retriever.py --search "VPN"
```

---

## 🎯 **Security Checklist**

Before scraping, ensure:

- [ ] **VPN is connected and active**
- [ ] **IP address is NOT 23.115.156.177**
- [ ] **VPN check passes:** `python vpn_checker.py`
- [ ] **Different IP confirmed:** Check detected IP
- [ ] **Logs are monitored:** Track VPN usage
- [ ] **No bypass flags used:** Avoid `--skip-vpn-check`

---

## 🔒 **Security Summary**

Your scraper includes comprehensive VPN protection:

✅ **Automatic IP Detection** - Multiple reliable services  
✅ **Home IP Blocking** - Prevents accidental exposure  
✅ **Graceful Failure** - Clear error messages and solutions  
✅ **API Protection** - VPN checks for all API requests  
✅ **Bypass Option** - For testing when needed  
✅ **Comprehensive Logging** - Track all security events  

**Your identity and privacy are protected! 🛡️**
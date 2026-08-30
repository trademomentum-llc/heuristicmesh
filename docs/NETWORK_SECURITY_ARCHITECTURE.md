# HeuristicMesh Network Security Architecture
## Complete Configuration Guide for Zyxel + TP-Link Infrastructure

**Version:** 1.0  
**Date:** 2026-08-29  
**Status:** Active  
**Hardware:** Zyxel USG Flex 100H, Zyxel XMG108, Zyxel NWA90BE, 3× TP-Link TL-SG108E, USR-TCP232-410S

---

## 🏗️ Network Topology Overview

```
INTERNET
   ↓ (WAN)
Zyxel USG Flex 100H (Firewall/Router)
   │
   ├── VLAN 10: Management (192.168.10.0/24)
   │     └── ASUS NUC (192.168.10.100)
   │     └── Zyxel XMG108 (192.168.10.2)
   │
   ├── VLAN 20: Inference (192.168.20.0/24)
   │     ├── Jetson Orin Nano A (192.168.20.10)
   │     └── Jetson Orin Nano B (192.168.20.11)
   │
   ├── VLAN 30: Sensors (192.168.30.0/24)
   │     ├── TP-Link TL-SG108E #1 (192.168.30.1)
   │     │     ├── ESP32-S3 #1 (192.168.30.11)
   │     │     ├── ESP32-S3 #2 (192.168.30.12)
   │     │     └── USR-TCP232-410S #1 (192.168.30.10)
   │     │
   │     ├── TP-Link TL-SG108E #2 (192.168.30.2)
   │     │     └── ESP32-S3 #3 (192.168.30.13)
   │     │
   │     └── TP-Link TL-SG108E #3 (192.168.30.3)
   │           └── USR-TCP232-410S #2 (192.168.30.20)
   │
   └── VLAN 40: Alert/Caregiver (192.168.40.0/24)
         ├── Zyxel NWA90BE (192.168.40.1)
         └── Caregiver Tablets (DHCP)

Modem (ISP) ←→ USG Flex 100H (WAN Port)
```

---

## 📋 Hardware Inventory & Roles

| Device | Model | Role | IP Address | VLAN | Management |
|--------|-------|------|------------|------|-------------|
| Firewall | Zyxel USG Flex 100H | Gateway, Firewall, Router | 192.168.1.1 (WAN) | All | Web (HTTPS) |
| Core Switch | Zyxel XMG108 | Management, Uplink | 192.168.10.2 | 10 (Mgmt), Trunk | Web, Nebula |
| Switch 1 | TP-Link TL-SG108E | Sensor Switch #1 | 192.168.30.1 | 30 (Access) | Web, Nebula |
| Switch 2 | TP-Link TL-SG108E | Sensor Switch #2 | 192.168.30.2 | 30 (Access) | Web, Nebula |
| Switch 3 | TP-Link TL-SG108E | Sensor Switch #3 | 192.168.30.3 | 30 (Access) | Web, Nebula |
| Access Point | Zyxel NWA90BE | WiFi for Caregivers | 192.168.40.1 | 40 | Web, Nebula |
| Serial Gateway | USR-TCP232-410S #1 | ESP32-S2 Gateway | 192.168.30.10 | 30 | Web, Serial |
| Serial Gateway | USR-TCP232-410S #2 | Backup Gateway | 192.168.30.20 | 30 | Web, Serial |
| Compute | ASUS NUC | Orchestrator | 192.168.10.100 | 10 | SSH, Web |
| Compute | Jetson Orin Nano A | Primary Inference | 192.168.20.10 | 20 | SSH |
| Compute | Jetson Orin Nano B | Standby Inference | 192.168.20.11 | 20 | SSH |

---

## 🔧 Device-Specific Configuration Guides

---

## 1️⃣ Zyxel USG Flex 100H (Firewall/Router)

### 🌐 **Access Methods**
| Method | URL | Credentials | Port |
|--------|-----|-------------|------|
| Web Interface | `https://192.168.1.1` | admin / (your password) | 443 |
| SSH | `192.168.1.1` | admin / (your password) | 22 |
| Nebula Cloud | [nebula.zyxel.com](https://nebula.zyxel.com) | Zyxel account | 443 |

---

### 📝 **Step-by-Step Configuration (Web Interface)**

#### **Step 1: Initial Setup & Firmware Update**
1. **Connect to USG Flex 100H:**
   - Plug your computer into **LAN Port 1**
   - Set computer IP to **192.168.1.2/24** (temporary)
   - Open browser to `https://192.168.1.1`

2. **Login:**
   - Default: `admin` / `1234`
   - **IMMEDIATELY CHANGE PASSWORD** to strong password

3. **Check Firmware:**
   - Navigate to **Configuration > System > Firmware**
   - **Current Version:** Should be ≥ **V5.30** (for full VLAN support)
   - **Update if needed:** Download from [Zyxel Support](https://www.zyxel.com/support)

4. **Backup Current Config:**
   - **Configuration > System > Configuration**
   - Click **Backup** and save `.cfg` file

---

#### **Step 2: WAN Configuration (Modem Connection)**

1. **Navigate to:** `Configuration > Network > Interface > Ethernet > WAN1`

2. **Connection Type:** Select based on your modem:
   | ISP Type | Selection | Notes |
   |----------|-----------|-------|
   | DHCP (Most common) | **Obtain an IP address automatically** | Cable, Fiber |
   | PPPoE | **PPPoE** | DSL, some Fiber |
   | Static IP | **Use the following IP address** | Business circuits |

3. **For DHCP (Typical):**
   ```
   IPv4 Configuration: DHCP
   Hostname: HeuristicMesh-USG
   MTU: 1500 (default)
   ```

4. **For PPPoE:**
   ```
   Username: [ISP username]
   Password: [ISP password]
   Service Name: (leave blank unless required)
   MTU: 1492 (recommended for PPPoE)
   Connection Type: Always On
   ```

5. **Advanced WAN Settings:**
   ```
   Enable Jumbo Frame: ✅ Checked (if supported)
   Enable Hardware Acceleration: ✅ Checked
   ```

---

#### **Step 3: VLAN Configuration**

**Navigate to:** `Configuration > Network > VLAN`

| VLAN ID | Name | Type | IP Address | Subnet Mask | DHCP Server |
|---------|------|------|------------|-------------|-------------|
| 10 | Management | Routing | 192.168.10.1 | 255.255.255.0 | ✅ Enabled |
| 20 | Inference | Routing | 192.168.20.1 | 255.255.255.0 | ❌ Disabled |
| 30 | Sensors | Routing | 192.168.30.1 | 255.255.255.0 | ❌ Disabled |
| 40 | Alert | Routing | 192.168.40.1 | 255.255.255.0 | ✅ Enabled |

**VLAN 10 (Management):**
```
VLAN ID: 10
VLAN Name: Management
Interface: LAN1 (Tagged)
IP Address: 192.168.10.1
Subnet Mask: 255.255.255.0
DHCP Server: Enabled
DHCP Range: 192.168.10.200 - 192.168.10.250
Lease Time: 86400 (24 hours)
DNS: 8.8.8.8, 8.8.4.4
```

**VLAN 20 (Inference):**
```
VLAN ID: 20
VLAN Name: Inference
Interface: LAN2 (Tagged)
IP Address: 192.168.20.1
Subnet Mask: 255.255.255.0
DHCP Server: Disabled (static IPs for Jetsons)
```

**VLAN 30 (Sensors):**
```
VLAN ID: 30
VLAN Name: Sensors
Interface: LAN3 (Tagged)
IP Address: 192.168.30.1
Subnet Mask: 255.255.255.0
DHCP Server: Disabled (static IPs for ESP32s)
```

**VLAN 40 (Alert/Caregiver):**
```
VLAN ID: 40
VLAN Name: Alert
Interface: LAN4 (Tagged)
IP Address: 192.168.40.1
Subnet Mask: 255.255.255.0
DHCP Server: Enabled
DHCP Range: 192.168.40.100 - 192.168.40.200
Lease Time: 43200 (12 hours)
DNS: 8.8.8.8, 8.8.4.4
```

---

#### **Step 4: Port Configuration (Trunk vs Access)**

**Navigate to:** `Configuration > Network > Interface > Ethernet`

| Port | Mode | VLAN Tagging | PVID | Allowed VLANs | Notes |
|------|------|--------------|------|----------------|-------|
| WAN1 | Access | N/A | N/A | N/A | Connects to modem |
| LAN1 | Trunk | 802.1Q | N/A | 10, 20, 30, 40 | Connects to XMG108 |
| LAN2 | Trunk | 802.1Q | N/A | 10, 20, 30, 40 | Backup uplink |
| LAN3 | Access | N/A | 30 | 30 | Direct sensor connection |
| LAN4 | Access | N/A | 40 | 40 | Connects to NWA90BE |

**LAN1 (Trunk to XMG108):**
```
Interface: LAN1
Mode: Trunk
802.1Q Tagging: Enabled
PVID: 1 (untagged)
Allowed VLANs: 10, 20, 30, 40 (all tagged)
```

---

#### **Step 5: Inter-VLAN Routing**

**Navigate to:** `Configuration > Network > Routing`

**Enable Inter-VLAN Routing:**
```
Inter-VLAN Routing: ✅ Enabled
Asymmetric Routing: ❌ Disabled
```

**Static Routes (if needed):**
```
Destination: 192.168.10.0/24
Gateway: 192.168.10.1
Interface: VLAN10

Destination: 192.168.20.0/24
Gateway: 192.168.20.1
Interface: VLAN20

Destination: 192.168.30.0/24
Gateway: 192.168.30.1
Interface: VLAN30

Destination: 192.168.40.0/24
Gateway: 192.168.40.1
Interface: VLAN40
```

---

#### **Step 6: Firewall Policies (CRITICAL)**

**Navigate to:** `Configuration > Security Policy > Policy Control`

##### **Default Policy: DENY ALL**
```
Default Policy: DENY
Log: ✅ Enabled
```

##### **Policy 1: Management VLAN (VLAN 10)**
```
Policy Name: Mgmt_Inbound
Source Zone: VLAN10
Destination Zone: ANY
Service: HTTPS, SSH, ICMP
Action: ALLOW
Log: ✅ Enabled
Schedule: Always
```

##### **Policy 2: Inference VLAN (VLAN 20)**
```
Policy Name: Inference_To_Mgmt
Source Zone: VLAN20
Destination Zone: VLAN10
Service: gRPC (TCP 50051), MQTT (TCP 1883, 8883)
Action: ALLOW
Log: ✅ Enabled

Policy Name: Inference_To_Sensors
Source Zone: VLAN20
Destination Zone: VLAN30
Service: ModBus/TCP (TCP 502), Custom (TCP 115200)
Action: ALLOW
Log: ✅ Enabled
```

##### **Policy 3: Sensors VLAN (VLAN 30)**
```
Policy Name: Sensors_To_Inference
Source Zone: VLAN30
Destination Zone: VLAN20
Service: ModBus/TCP (TCP 502), Custom (TCP 115200)
Action: ALLOW
Log: ✅ Enabled

Policy Name: Sensors_To_Mgmt
Source Zone: VLAN30
Destination Zone: VLAN10
Service: MQTT (TCP 1883, 8883), HTTPS (TCP 443)
Action: ALLOW
Log: ✅ Enabled
```

##### **Policy 4: Alert VLAN (VLAN 40)**
```
Policy Name: Alert_Outbound
Source Zone: VLAN40
Destination Zone: WAN
Service: HTTPS (TCP 443), DNS (UDP 53)
Action: ALLOW
Log: ✅ Enabled

Policy Name: Alert_To_Mgmt
Source Zone: VLAN40
Destination Zone: VLAN10
Service: MQTT (TCP 1883, 8883)
Action: ALLOW
Log: ✅ Enabled
```

##### **Policy 5: NUC Outbound (Alert Only)**
```
Policy Name: NUC_Alert_Only
Source Zone: VLAN10
Source IP: 192.168.10.100 (NUC)
Destination Zone: WAN
Service: HTTPS (TCP 443)
Action: ALLOW
Log: ✅ Enabled
```

##### **Policy 6: Block All Other Outbound from VLAN 20/30**
```
Policy Name: Block_Compute_Outbound
Source Zone: VLAN20, VLAN30
Destination Zone: WAN
Service: ANY
Action: DENY
Log: ✅ Enabled
```

---

#### **Step 7: NAT Configuration**

**Navigate to:** `Configuration > Network > NAT`

**Outbound NAT (for NUC alerts only):**
```
Rule Name: NUC_Alert_NAT
Source Interface: VLAN10
Source IP: 192.168.10.100
Destination Interface: WAN1
Translation: Interface Address
Outgoing Interface: WAN1
```

**Inbound NAT (if remote access needed):**
```
Rule Name: Remote_Mgmt
Source Interface: WAN1
Destination Interface Address: [Your Public IP]
Protocol: TCP
External Port: 4443
Internal IP: 192.168.10.1
Internal Port: 443
```

---

#### **Step 8: DNS Configuration**

**Navigate to:** `Configuration > Network > DNS`

```
Primary DNS: 8.8.8.8 (Google)
Secondary DNS: 8.8.4.4 (Google)
Tertiary DNS: 1.1.1.1 (Cloudflare)

DNS Caching: ✅ Enabled
Cache Size: 1000 entries
Cache Time: 3600 seconds
```

---

#### **Step 9: DHCP Server Configuration**

**For VLAN 10 (Management):**
```
Interface: VLAN10
Start IP: 192.168.10.200
End IP: 192.168.10.250
Subnet Mask: 255.255.255.0
Gateway: 192.168.10.1
DNS: 8.8.8.8, 8.8.4.4
Lease Time: 86400 (24 hours)
Domain Name: heuristicmesh.local
```

**For VLAN 40 (Alert/Caregiver):**
```
Interface: VLAN40
Start IP: 192.168.40.100
End IP: 192.168.40.200
Subnet Mask: 255.255.255.0
Gateway: 192.168.40.1
DNS: 8.8.8.8, 8.8.4.4
Lease Time: 43200 (12 hours)
Domain Name: heuristicmesh.local
```

---

#### **Step 10: Security Settings**

**Navigate to:** `Configuration > System > Security`

```
' ========================================================================
' ADMINISTRATIVE ACCESS
' ========================================================================

Web Admin Access: ✅ HTTPS Only
HTTP Redirect to HTTPS: ✅ Enabled
SSH Access: ✅ Enabled
SSH Port: 22 (default)
SSH Timeout: 30 minutes

Admin Session Timeout: 15 minutes
Max Login Attempts: 5
Lockout Time: 30 minutes

' ========================================================================
' PASSWORD POLICY
' ========================================================================

Minimum Length: 12 characters
Require Uppercase: ✅
Require Lowercase: ✅
Require Numbers: ✅
Require Special Chars: ✅
Password Expiration: 90 days

' ========================================================================
' FIREWALL PROTECTION
' ========================================================================

SYN Flood Protection: ✅ Enabled
Threshold: 1000 packets/sec

UDP Flood Protection: ✅ Enabled
Threshold: 1000 packets/sec

ICMP Flood Protection: ✅ Enabled
Threshold: 100 packets/sec

IP Spoofing Protection: ✅ Enabled

Land Attack Protection: ✅ Enabled

' ========================================================================
' VPN (Optional for remote access)
' ========================================================================

SSL VPN: ✅ Enabled (if needed)
Port: 4433
Certificate: Self-signed or Let's Encrypt
Authentication: Local + Google Authenticator

IPSec VPN: ❌ Disabled (unless required)
```

---

#### **Step 11: Logging & Monitoring**

**Navigate to:** `Configuration > Log & Report > Log`

```
' ========================================================================
' LOCAL LOGGING
' ========================================================================

Log Level: Informational
Log Storage: ✅ Enabled
Max Log Size: 100 MB
Log Rotation: ✅ Enabled

' ========================================================================
' SYSLOG (Recommended)
' ========================================================================

Syslog: ✅ Enabled
Server IP: 192.168.10.100 (NUC)
Port: 514
Protocol: UDP
Facility: LOCAL0

' ========================================================================
' EMAIL ALERTS
' ========================================================================

SMTP Server: smtp.gmail.com (or your provider)
Port: 587 (TLS)
Username: [your email]
Password: [app password]
From: usg-alerts@heuristicmesh.local
To: admin@heuristicmesh.local

Alert Severity: Critical, Warning
```

---

#### **Step 12: Time Configuration (NTP)**

**Navigate to:** `Configuration > System > Time`

```
Time Zone: [Your time zone, e.g., America/New_York]
NTP Server 1: pool.ntp.org
NTP Server 2: time.google.com
NTP Server 3: time.cloudflare.com

Sync Interval: 60 minutes
Daylight Saving: ✅ Auto-adjust
```

---

#### **Step 13: Save & Apply**

```bash
1. Click 
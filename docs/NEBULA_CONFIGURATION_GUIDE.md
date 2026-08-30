# Zyxel Nebula Cloud Configuration Guide
## Complete Setup for HeuristicMesh Network Infrastructure

**Version:** 1.0  
**Date:** 2026-08-29  
**Status:** Active  
**Cloud Platform:** [nebula.zyxel.com](https://nebula.zyxel.com)

---

## 🌐 Nebula Overview

**Zyxel Nebula** is a cloud-based network management platform that allows you to:
- Manage all Zyxel devices from a single dashboard
- Configure VLANs, firewall rules, and security policies centrally
- Monitor traffic and device health
- Receive alerts and notifications
- Apply configurations to multiple devices at once

**Supported Devices in HeuristicMesh:**
- ✅ Zyxel USG Flex 100H (Firewall)
- ✅ Zyxel XMG108 (Managed Switch)
- ✅ Zyxel NWA90BE (Access Point)
- ❌ TP-Link TL-SG108E (Not Nebula-compatible - use web interface)

---

## 📋 Prerequisites

### 1. Create Nebula Account
1. Go to [https://nebula.zyxel.com](https://nebula.zyxel.com)
2. Click **"Sign Up"**
3. Fill in your information
4. Verify email address
5. Log in to Nebula dashboard

### 2. Create Organization
1. After login, click **"Create Organization"**
2. Name: `HeuristicMesh`
3. Description: `Fall Detection System Network`
4. Country/Timezone: [Your location]
5. Click **"Create"**

### 3. Add License (If Required)
- Free tier supports up to **100 devices**
- For more devices, purchase a license
- Navigate to **Organization > License** to check/add

---

## 🔧 Device Registration

### **Method 1: Nebula Registration (Recommended for Zyxel Devices)**

#### **For USG Flex 100H, XMG108, NWA90BE:**

1. **Factory Reset Device (if previously configured):**
   - Press and hold reset button for 10+ seconds
   - Wait for device to reboot

2. **Connect Device to Internet:**
   - USG Flex 100H: Connect WAN port to modem
   - XMG108/NWA90BE: Connect to network with internet access

3. **In Nebula Dashboard:**
   - Navigate to **Site > Devices**
   - Click **"Add Device"**
   - Select **"Register with Nebula"**
   - Enter **Device Serial Number** (found on device label)
   - Click **"Register"**

4. **Device Will Appear in Dashboard:**
   - Status: **"Pending"** → **"Online"** (may take 5-10 minutes)
   - Once online, click device to configure

#### **Finding Serial Numbers:**
| Device | Location of Serial Number |
|--------|---------------------------|
| USG Flex 100H | Bottom of device, or System > Information in web interface |
| XMG108 | Bottom of device |
| NWA90BE | Bottom of device |

---

### **Method 2: Nebula Agent (For Non-Zyxel Devices)**

**Note:** TP-Link TL-SG108E switches are **not Nebula-compatible**. Use web interface for these.

For devices that support Nebula Agent (some third-party devices):
1. Download Nebula Agent from Nebula dashboard
2. Install on device (if supported)
3. Register device in Nebula

---

## 🏗️ Site Configuration

### **Step 1: Create Site**

1. In Nebula dashboard, navigate to **Organization > Sites**
2. Click **"Create Site"**
3. Fill in details:
   ```
   Site Name: HeuristicMesh_Primary
   Description: Main fall detection system deployment
   Address: [Your facility address]
   Time Zone: [Your time zone]
   ```
4. Click **"Create"**

### **Step 2: Add Devices to Site**

1. Navigate to **Site > Devices**
2. Select all registered devices
3. Click **"Move to Site"**
4. Select **"HeuristicMesh_Primary"**
5. Click **"Move"**

---

## 🌐 Network Configuration via Nebula

### **Step 1: VLAN Configuration**

**Navigate to:** `Site > Configure > Network > VLAN`

#### **Create VLANs:**

**VLAN 10 - Management:**
```
VLAN ID: 10
Name: Management
Description: Management network for NUC and switches
Subnet: 192.168.10.0/24
Gateway: 192.168.10.1
DHCP: Enabled
DHCP Range: 192.168.10.200 - 192.168.10.250
DNS: 8.8.8.8, 8.8.4.4
```

**VLAN 20 - Inference:**
```
VLAN ID: 20
Name: Inference
Description: Inference network for Jetson devices
Subnet: 192.168.20.0/24
Gateway: 192.168.20.1
DHCP: Disabled (static IPs for Jetsons)
```

**VLAN 30 - Sensors:**
```
VLAN ID: 30
Name: Sensors
Description: Sensor network for ESP32 devices
Subnet: 192.168.30.0/24
Gateway: 192.168.30.1
DHCP: Disabled (static IPs for ESP32s)
```

**VLAN 40 - Alert/Caregiver:**
```
VLAN ID: 40
Name: Alert
Description: Alert network for caregiver devices
Subnet: 192.168.40.0/24
Gateway: 192.168.40.1
DHCP: Enabled
DHCP Range: 192.168.40.100 - 192.168.40.200
DNS: 8.8.8.8, 8.8.4.4
```

---

### **Step 2: Port Configuration (XMG108)**

**Navigate to:** `Site > Configure > [XMG108] > Port`

**Port 1 (Uplink to USG Flex 100H):**
```
Port: 1
Mode: Trunk
PVID: 1 (untagged)
Tagged VLANs: 10, 20, 30, 40
Untagged VLAN: 1
Admin Mode: Enabled
Speed: Auto
Duplex: Auto
Flow Control: Disabled
```

**Ports 2-8 (Access Ports):**
```
Port: 2-8
Mode: Access
PVID: [VLAN ID based on device]
Tagged VLANs: None
Untagged VLAN: [VLAN ID]
Admin Mode: Enabled
Speed: Auto
Duplex: Auto
```

**Port Configuration Example:**
| Port | Device | PVID | Mode | Notes |
|------|--------|------|------|-------|
| 1 | USG Flex 100H | 1 | Trunk | All VLANs tagged |
| 2 | Jetson A | 20 | Access | VLAN 20 |
| 3 | Jetson B | 20 | Access | VLAN 20 |
| 4 | NUC | 10 | Access | VLAN 10 |
| 5 | TP-Link #1 | 30 | Trunk | VLAN 30 tagged |
| 6 | TP-Link #2 | 30 | Trunk | VLAN 30 tagged |
| 7 | TP-Link #3 | 30 | Trunk | VLAN 30 tagged |
| 8 | NWA90BE | 40 | Trunk | VLAN 40 tagged |

---

### **Step 3: Firewall Policies (USG Flex 100H)**

**Navigate to:** `Site > Configure > [USG Flex 100H] > Security Policy`

#### **Default Policy:**
```
Default Policy: DENY
Action: Drop
Log: Enabled
```

#### **Policy 1: Management Access**
```
Policy Name: Mgmt_Access
Source Zone: VLAN10
Destination Zone: ANY
Source IP: ANY
Destination IP: ANY
Service: HTTPS, SSH, ICMP
Action: ALLOW
Log: Enabled
Schedule: Always
```

#### **Policy 2: Inference to Management**
```
Policy Name: Inference_To_Mgmt
Source Zone: VLAN20
Destination Zone: VLAN10
Source IP: ANY
Destination IP: 192.168.10.100 (NUC)
Service: gRPC (TCP 50051), MQTT (TCP 1883, 8883)
Action: ALLOW
Log: Enabled
```

#### **Policy 3: Inference to Sensors**
```
Policy Name: Inference_To_Sensors
Source Zone: VLAN20
Destination Zone: VLAN30
Source IP: ANY
Destination IP: ANY
Service: ModBus/TCP (TCP 502), Custom (TCP 115200)
Action: ALLOW
Log: Enabled
```

#### **Policy 4: Sensors to Inference**
```
Policy Name: Sensors_To_Inference
Source Zone: VLAN30
Destination Zone: VLAN20
Source IP: ANY
Destination IP: ANY
Service: ModBus/TCP (TCP 502), Custom (TCP 115200)
Action: ALLOW
Log: Enabled
```

#### **Policy 5: Sensors to Management**
```
Policy Name: Sensors_To_Mgmt
Source Zone: VLAN30
Destination Zone: VLAN10
Source IP: ANY
Destination IP: 192.168.10.100 (NUC)
Service: MQTT (TCP 1883, 8883), HTTPS (TCP 443)
Action: ALLOW
Log: Enabled
```

#### **Policy 6: Alert Outbound**
```
Policy Name: Alert_Outbound
Source Zone: VLAN40
Destination Zone: WAN
Source IP: ANY
Destination IP: ANY
Service: HTTPS (TCP 443), DNS (UDP 53)
Action: ALLOW
Log: Enabled
```

#### **Policy 7: Alert to Management**
```
Policy Name: Alert_To_Mgmt
Source Zone: VLAN40
Destination Zone: VLAN10
Source IP: ANY
Destination IP: ANY
Service: MQTT (TCP 1883, 8883)
Action: ALLOW
Log: Enabled
```

#### **Policy 8: NUC Alert Only (CRITICAL)**
```
Policy Name: NUC_Alert_Only
Source Zone: VLAN10
Source IP: 192.168.10.100
Destination Zone: WAN
Destination IP: ANY
Service: HTTPS (TCP 443)
Action: ALLOW
Log: Enabled
```

#### **Policy 9: Block All Other Outbound**
```
Policy Name: Block_Compute_Outbound
Source Zone: VLAN20, VLAN30
Destination Zone: WAN
Source IP: ANY
Destination IP: ANY
Service: ANY
Action: DENY
Log: Enabled
```

---

### **Step 4: NAT Configuration**

**Navigate to:** `Site > Configure > [USG Flex 100H] > NAT`

**Outbound NAT for NUC Alerts:**
```
Rule Name: NUC_Alert_NAT
Source Interface: VLAN10
Source IP: 192.168.10.100
Destination Interface: WAN1
Translation: Interface Address
Outgoing Interface: WAN1
```

---

### **Step 5: DHCP Configuration**

**Navigate to:** `Site > Configure > [USG Flex 100H] > DHCP Server`

**VLAN 10 (Management):**
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

**VLAN 40 (Alert/Caregiver):**
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

### **Step 6: Wireless Configuration (NWA90BE)**

**Navigate to:** `Site > Configure > [NWA90BE] > Wireless`

#### **Radio Settings:**
```
Radio: 5GHz (Recommended for HeuristicMesh)
Mode: Access Point
Channel Width: 80MHz
Channel: Auto (or select least congested)
Transmit Power: 100%
Country Code: [Your country]
```

#### **SSID Configuration:**
```
SSID Name: HeuristicMesh_Alert
Hide SSID: ❌ Disabled
Security: WPA2/WPA3 Personal
Encryption: AES
Password: [Strong password, 12+ chars]
VLAN: 40
```

#### **Advanced Wireless:**
```
Max Clients: 50
Beacon Interval: 100 ms
DTIM Interval: 3
RTS Threshold: 2346
Fragmentation Threshold: 2346
Short GI: ✅ Enabled
```

#### **VLAN Assignment:**
```
SSID: HeuristicMesh_Alert
VLAN ID: 40
```

---

## 🔌 TP-Link TL-SG108E Configuration (Web Interface Only)

**Note:** TP-Link TL-SG108E is **NOT Nebula-compatible**. Must configure via web interface.

### **Access TP-Link Web Interface**

1. **Connect computer to TP-Link switch**
2. **Set computer IP:** 192.168.0.100 (temporary)
3. **Open browser:** `http://192.168.0.1`
4. **Login:** admin / admin (change immediately!)

### **Step 1: Change Admin Password**

**Navigate to:** `System > Password`

```
Old Password: admin
New Password: [Strong password]
Confirm Password: [Same]
```

---

### **Step 2: VLAN Configuration**

**Navigate to:** `VLAN > 802.1Q VLAN`

#### **VLAN Settings:**
```
VLAN ID: 30
VLAN Name: Sensors
```

#### **Port Configuration for Switch #1:**
| Port | PVID | Tagged | Untagged | Notes |
|------|------|--------|----------|-------|
| 1 | 30 | ✅ | ❌ | Uplink to XMG108 |
| 2 | 30 | ❌ | ✅ | ESP32-S3 #1 |
| 3 | 30 | ❌ | ✅ | ESP32-S3 #2 |
| 4 | 30 | ❌ | ✅ | (Future use) |
| 5 | 30 | ❌ | ✅ | (Future use) |
| 6 | 30 | ❌ | ✅ | (Future use) |
| 7 | 30 | ❌ | ✅ | (Future use) |
| 8 | 30 | ❌ | ✅ | USR-TCP232 #1 |

**Port 1 (Uplink):**
```
Port: 1
PVID: 30
Tagged: ✅ (VLAN 30)
Untagged: ❌
```

**Ports 2-8 (Access):**
```
Port: 2-8
PVID: 30
Tagged: ❌
Untagged: ✅
```

---

### **Step 3: IP Configuration**

**Navigate to:** `IP Configuration > IPv4`

```
IP Address: 192.168.30.1 (for Switch #1)
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.30.1 (USG Flex 100H)
DNS: 8.8.8.8
```

**For Switch #2:**
```
IP Address: 192.168.30.2
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.30.1
DNS: 8.8.8.8
```

**For Switch #3:**
```
IP Address: 192.168.30.3
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.30.1
DNS: 8.8.8.8
```

---

### **Step 4: Save Configuration**

```
1. Click "Apply"
2. Wait for switch to reboot (30-60 seconds)
3. Verify connectivity
```

---

## 🔄 USR-TCP232-410S Configuration

### **Access Methods**
| Method | Connection | Settings |
|--------|------------|----------|
| Web Interface | `http://192.168.30.10` | Default: admin/admin |
| Serial (AT Commands) | Direct serial | 115200 baud |
| Telnet | Port 23 | admin/admin |

### **Step 1: Initial Setup**

1. **Connect via Ethernet:**
   - Plug into TP-Link switch (VLAN 30)
   - Device should get IP from DHCP or use static

2. **Find IP Address:**
   ```bash
   # On macOS
   arp -a | grep -i usr
   # Or check your DHCP server leases
   ```

3. **Access Web Interface:**
   - Open browser to `http://[device-ip]`
   - Default credentials: `admin` / `admin`

---

### **Step 2: Network Configuration**

**Navigate to:** `Network > TCP/IP`

```
IP Address: 192.168.30.10 (for device #1)
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.30.1
DNS Server: 8.8.8.8

IP Address: 192.168.30.20 (for device #2)
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.30.1
DNS Server: 8.8.8.8
```

---

### **Step 3: Serial Configuration**

**Navigate to:** `Serial > Port 1`

```
Baud Rate: 115200
Data Bits: 8
Stop Bits: 1
Parity: None
Flow Control: None

Operation Mode: TCP Server
Local Port: 502 (for ModBus/TCP)
Remote IP: 0.0.0.0 (any)
Remote Port: 0 (any)

Connection Mode: Keep Alive
Idle Timeout: 0 (no timeout)
```

---

### **Step 4: ModBus/TCP Configuration**

**Navigate to:** `Protocol > ModBus TCP`

```
ModBus TCP: ✅ Enabled
Port: 502
Unit ID: 1 (for device #1)
Unit ID: 2 (for device #2)

Response Timeout: 1000 ms
Max Connections: 5
```

---

### **Step 5: Save & Test**

```
1. Click "Save"
2. Click "Reboot" if required
3. Test connection:
   - From Jetson: telnet 192.168.30.10 502
   - Should connect successfully
```

---

## 📊 Verification Checklist

### **After All Configurations:**

| Test | Command | Expected Result |
|------|---------|-----------------|
| Ping USG Flex 100H | `ping 192.168.1.1` | Reply from 192.168.1.1 |
| Ping XMG108 | `ping 192.168.10.2` | Reply from 192.168.10.2 |
| Ping TP-Link #1 | `ping 192.168.30.1` | Reply from 192.168.30.1 |
| Ping TP-Link #2 | `ping 192.168.30.2` | Reply from 192.168.30.2 |
| Ping TP-Link #3 | `ping 192.168.30.3` | Reply from 192.168.30.3 |
| Ping NWA90BE | `ping 192.168.40.1` | Reply from 192.168.40.1 |
| Ping USR-TCP232 #1 | `ping 192.168.30.10` | Reply from 192.168.30.10 |
| Ping USR-TCP232 #2 | `ping 192.168.30.20` | Reply from 192.168.30.20 |
| Test VLAN 10 | `ping 192.168.10.100` | Reply from NUC |
| Test VLAN 20 | `ping 192.168.20.10` | Reply from Jetson A |
| Test VLAN 30 | `ping 192.168.30.11` | Reply from ESP32 #1 |
| Test VLAN 40 | Connect to WiFi | Get IP in 192.168.40.x |
| Test ModBus/TCP | `telnet 192.168.30.10 502` | Connection successful |
| Test MQTT | `mosquitto_sub -h 192.168.10.100 -t '#' -v` | See MQTT messages |

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

| Issue | Cause | Solution |
|-------|-------|----------|
| Device not appearing in Nebula | Not registered | Check serial number, re-register |
| VLAN not working | Trunk misconfigured | Verify PVID and tagged VLANs |
| No internet on VLAN 40 | NAT missing | Add NAT rule for VLAN 40 |
| Can't ping across VLANs | Inter-VLAN routing disabled | Enable in USG Flex 100H |
| ModBus/TCP not connecting | Wrong port | Verify USR-TCP232 port 502 |
| Firewall blocking traffic | Policy misconfigured | Check policy order, add ALLOW rule |
| DHCP not working | Wrong VLAN | Verify DHCP server on correct VLAN |

### **Nebula-Specific Troubleshooting**

1. **Device Stuck in "Pending" State:**
   - Verify device has internet access
   - Check serial number is correct
   - Try factory reset and re-register
   - Check Nebula account has available licenses

2. **Configuration Not Applying:**
   - Click "Save" then "Apply" in Nebula
   - Wait 2-5 minutes for changes to propagate
   - Check device status in Nebula
   - Reboot device if needed

3. **Can't Access Nebula Dashboard:**
   - Verify internet connection
   - Try different browser
   - Clear browser cache
   - Check Zyxel Nebula status: [status.zyxel.com](https://status.zyxel.com)

---

## 📚 Manufacturer Documentation

### **Zyxel Devices**
- **USG Flex 100H:** [User Guide](https://www.zyxel.com/support/USG-Flex-100H-user-guide)
- **XMG108:** [User Guide](https://www.zyxel.com/support/XMG108-user-guide)
- **NWA90BE:** [User Guide](https://www.zyxel.com/support/NWA90BE-user-guide)
- **Nebula Cloud:** [Documentation](https://www.zyxel.com/nebula/documentation)

### **TP-Link Devices**
- **TL-SG108E:** [User Guide](https://www.tp-link.com/us/support/download/tl-sg108e/#User_Guides)
- **Web Interface Guide:** [TP-Link Support](https://www.tp-link.com/support/)

### **USR-TCP232**
- **User Manual:** [USR-TCP232 Manual](https://www.usriot.com/products/usr-tcp232-410s)
- **AT Commands:** [USR AT Commands](https://www.usriot.com/support/at-commands)

---

## 🎯 Best Practices

### **Security:**
✅ Change all default passwords immediately  
✅ Enable HTTPS-only for web interfaces  
✅ Disable unused services (Telnet, HTTP)  
✅ Use strong passwords (12+ characters)  
✅ Enable logging and syslog  
✅ Regularly backup configurations  
✅ Keep firmware up to date  

### **Performance:**
✅ Use trunk ports for inter-switch connections  
✅ Enable jumbo frames where supported  
✅ Use 5GHz WiFi for better performance  
✅ Separate VLANs for different traffic types  
✅ Enable hardware acceleration on USG Flex 100H  

### **Reliability:**
✅ Use static IPs for critical devices (NUC, Jetsons, ESP32s)  
✅ Configure redundant paths where possible  
✅ Enable link aggregation for high-traffic connections  
✅ Monitor device health in Nebula  
✅ Set up email alerts for critical events  

---

## 📞 Support Contacts

| Manufacturer | Support Website | Phone |
|--------------|-----------------|-------|
| Zyxel | [https://support.zyxel.com](https://support.zyxel.com) | 1-800-ZYXEL (US) |
| TP-Link | [https://www.tp-link.com/support](https://www.tp-link.com/support) | 1-866-225-8139 (US) |
| USR | [https://www.usriot.com/support](https://www.usriot.com/support) | +86-755-86168366 |

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.0

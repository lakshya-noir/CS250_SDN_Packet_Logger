# 📡 SDN Packet Logger using Ryu Controller

## 🧾 Overview

This project implements a Software Defined Networking (SDN) based packet logger using the Ryu controller and Mininet.  
The controller monitors all packets in real time, logs their metadata, and enforces policies such as blocking specific host pairs.

---

## 🎯 Objectives

- Understand SDN architecture (Control Plane vs Data Plane)
- Monitor network traffic at packet level
- Implement dynamic traffic control (blocking rules)
- Log packets to a CSV file for analysis
- Simulate network topology using Mininet

---

## 🏗️ Architecture

- Controller (Ryu) → Control Plane  
- Open vSwitch (Mininet) → Data Plane  
- OpenFlow Protocol → Communication between controller and switches  

---

## 🌐 Topology

- 2 Switches: s1, s2
- 4 Hosts:
  - h1 → 10.0.0.1
  - h2 → 10.0.0.2
  - h3 → 10.0.0.3
  - h4 → 10.0.0.4

### Connections

- h1, h2 → s1  
- h3, h4 → s2  
- s1 ↔ s2  

---

## ⚙️ Technologies Used

- Python 3
- Ryu SDN Controller
- Mininet
- OpenFlow 1.3

---

## 🚀 Features

- 📦 Real-time packet logging
- 📄 CSV-based persistent logs
- 🔍 Protocol detection (ICMP, TCP, UDP)
- 🚫 Traffic blocking between selected hosts
- 🔁 Learning switch behavior (flow installation)
- 🌐 Multi-switch topology support

---

## 📁 Project Structure

```
sdn-logger/ 
├── logger.py          # Ryu controller logic 
├── topology.py        # Mininet topology 
└── README.md
```

---

## ⚡ Setup Instructions

### 1. Activate virtual environment

```
source ~/ryu-env/bin/activate
```

---

### 2. Run Controller (Terminal 1)

```
cd ~/sdn-logger ryu-manager logger.py
```

---

### 3. Run Topology (Terminal 2)

```
cd ~/sdn-logger sudo mn -c sudo python3 topology.py
```

---

## 🧪 Testing

### Run connectivity test

```
pingall
```

---

### Test specific hosts

```
h1 ping -c 3 h2   # Allowed 
h2 ping -c 3 h4   # Blocked
```

---

## 📊 Sample Output

### Controller Log

```
10.0.0.1 -> 10.0.0.2 | ICMP | FORWARDED 10.0.0.1 -> 10.0.0.3 | ICMP | BLOCKED
```

---

### CSV Log File

Location:
```
~/sdn-packet-logger/packet_log.csv
```
View logs:
```
tail -n 10 ~/sdn-packet-logger/packet_log.csv
```

---

## 🧠 Key Concepts

### 🔹 SDN
Separates control plane from data plane for centralized management.

### 🔹 Packet-In
Switch sends unknown packets to controller for decision.

### 🔹 Flow Rules
Installed by controller to reduce repeated processing.

### 🔹 ARP
Resolves IP address to MAC address before communication.

---

## 🚫 Blocking Policy

Defined in logger.py:

python self.blocked_pairs = [('10.0.0.2', '10.0.0.4)] 

---

## 📈 Performance Testing

### Latency
```
h1 ping h2
```

### Throughput
```
h2 iperf -s & h1 iperf -c 10.0.0.2 -t 5
```

---

## 🔍 Observations

- ARP packets appear as OTHER (no IP)
- ICMP packets represent actual ping traffic
- Blocked hosts show packet loss in Mininet

---

## 🧩 Conclusion

This project demonstrates how SDN enables:
- Centralized control
- Real-time monitoring
- Dynamic policy enforcement

---

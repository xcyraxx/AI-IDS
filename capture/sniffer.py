from scapy.all import sniff, IP, TCP, UDP, ICMP, conf
from collections import deque
from datetime import datetime
import csv
import os

# ========== CONFIG ==========
MAX_BUFFER_SIZE = 200
SAVE_FILE = "data/traffic.csv"

# Filter settings (change as needed)
ALLOWED_PROTOCOLS = ["TCP", "UDP", "ICMP"]   # or [] for all
ALLOWED_PORTS = [80, 443, 22]                # HTTP, HTTPS, SSH

# Packet buffer (queue)
packet_buffer = deque(maxlen=MAX_BUFFER_SIZE)

# Create CSV if not exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "src_ip", "dst_ip", "protocol", "src_port", "dst_port", "size"])

def protocol_name(pkt):
    if pkt.haslayer(TCP):
        return "TCP"
    elif pkt.haslayer(UDP):
        return "UDP"
    elif pkt.haslayer(ICMP):
        return "ICMP"
    return "OTHER"

def process_packet(pkt):
    if not pkt.haslayer(IP):
        return

    proto = protocol_name(pkt)

    # Protocol filter
    if ALLOWED_PROTOCOLS and proto not in ALLOWED_PROTOCOLS:
        return

    src_port, dst_port = None, None

    if pkt.haslayer(TCP) or pkt.haslayer(UDP):
        src_port = pkt.sport
        dst_port = pkt.dport

        # Port filter
        if ALLOWED_PORTS and dst_port not in ALLOWED_PORTS and src_port not in ALLOWED_PORTS:
            return

    packet_info = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "src_ip": pkt[IP].src,
        "dst_ip": pkt[IP].dst,
        "protocol": proto,
        "src_port": src_port,
        "dst_port": dst_port,
        "size": len(pkt)
    }

    # Add to buffer
    packet_buffer.append(packet_info)

    # Save to CSV
    with open(SAVE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(packet_info.values())

    print(f"[+] {packet_info['src_ip']} → {packet_info['dst_ip']} | {proto} | {packet_info['size']} bytes")

def start_sniffing():
    print("🚀 Packet sniffer started... (Press CTRL+C to stop)")
    from scapy.all import conf

def start_sniffing():
    iface = conf.iface
    print(f"📡 Sniffing on interface: {iface}")
    sniff(prn=process_packet, store=False)

if __name__ == "__main__":
    start_sniffing()

import numpy as np
import uuid
import datetime
from models.traffic import TrafficFlow

def generate_synthetic_traffic(count: int, seed: int = None) -> list[TrafficFlow]:
    if seed is not None:
        np.random.seed(seed)
    
    classes = ["Gaming", "Video Streaming", "Web Browsing", "File Transfer", "VoIP"]
    flows = []
    
    for _ in range(count):
        flow_class = np.random.choice(classes)
        flow_id = str(uuid.UUID(bytes=np.random.bytes(16)))
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Default initialization to be overridden
        protocol = "TCP"
        source_port = np.random.randint(1024, 65535)
        destination_port = 80
        packet_count = 0
        avg_packet_size = 0.0
        duration = 0.0
        tcp_flag_pattern = "ACK,PSH"

        if flow_class == "Gaming":
            protocol = np.random.choice(["UDP", "TCP"], p=[0.8, 0.2])
            destination_port = np.random.choice([27015, 3074, 3478, 443])
            packet_count = int(np.random.normal(500, 300))
            avg_packet_size = max(40.0, np.random.normal(250, 150))
            duration = max(0.5, np.random.normal(5.0, 3.0))
            tcp_flag_pattern = "ACK,PSH" if protocol == "TCP" else "NONE"
            
        elif flow_class == "Video Streaming":
            protocol = np.random.choice(["UDP", "TCP"], p=[0.3, 0.7])
            destination_port = np.random.choice([443, 80])
            packet_count = int(np.random.normal(5000, 2500))
            avg_packet_size = max(500.0, np.random.normal(1000, 400))
            duration = max(10.0, np.random.normal(60.0, 30.0))
            tcp_flag_pattern = "ACK" if protocol == "TCP" else "NONE"
            
        elif flow_class == "Web Browsing":
            protocol = "TCP"
            destination_port = np.random.choice([443, 80])
            packet_count = int(np.random.normal(250, 200))
            avg_packet_size = max(100.0, np.random.normal(600, 400))
            duration = max(0.1, np.random.normal(3.0, 2.5))
            tcp_flag_pattern = "SYN,ACK,FIN"
            
        elif flow_class == "File Transfer":
            protocol = "TCP"
            destination_port = np.random.choice([20, 21, 22, 443])
            packet_count = int(np.random.normal(8000, 4000))
            avg_packet_size = max(800.0, np.random.normal(1300, 250))
            duration = max(5.0, np.random.normal(90.0, 60.0))
            tcp_flag_pattern = "ACK,PSH"
            
        elif flow_class == "VoIP":
            protocol = np.random.choice(["UDP", "TCP"], p=[0.9, 0.1])
            destination_port = np.random.choice([5060, 5061, 10000, 443])
            packet_count = int(np.random.normal(1000, 500))
            avg_packet_size = max(40.0, np.random.normal(160, 80))
            duration = max(5.0, np.random.normal(30.0, 15.0))
            tcp_flag_pattern = "ACK" if protocol == "TCP" else "NONE"
            
        # Add random variations and bounds check
        packet_count = max(1, packet_count)
        duration = max(0.01, duration)
        
        pps = packet_count / duration
        bps = (packet_count * avg_packet_size) / duration
        inter_arrival = duration / packet_count if packet_count > 0 else 0
        
        flows.append(TrafficFlow(
            flowId=flow_id,
            timestamp=timestamp,
            protocol=protocol,
            sourcePort=int(source_port),
            destinationPort=int(destination_port),
            packetCount=int(packet_count),
            averagePacketSize=float(avg_packet_size),
            packetsPerSecond=float(pps),
            bytesPerSecond=float(bps),
            flowDuration=float(duration),
            averageInterArrivalTime=float(inter_arrival),
            tcpFlagPattern=tcp_flag_pattern,
            groundTruthClass=flow_class
        ))
        
    return flows

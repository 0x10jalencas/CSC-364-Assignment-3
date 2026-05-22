from dataclasses import dataclass

@dataclass
class Client_Packet:
    seq_number: int
    checksum: int
    data: int

@dataclass
class Server_Packet:
    ack_number: int

one_chunk = 1024
last_ack_number = 0

with open('gistfile1.txt', 'rb') as f:
    chunk = f.read(one_chunk)
    if not chunk:
        break
    


def slow_start(cwnd, ssthresh, ack, rtt):
    for server_packet in ack:
        if server_packet.ack_number > last_ack_number:
            cwnd += 1
        
        if cwnd >= ssthresh:
            cwnd = ssthresh
            break
    
    return cwnd

def congestion_avoidance(cwnd, ack, ssthresh, rtt):
    for server_packet in ack:
        if server_packet.ack_number > last_ack_number:
            cwnd += 1 / cwnd
            last_ack_number = server_packet.ack_number

    return cwnd, last_ack_number


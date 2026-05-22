from dataclasses import dataclass

@dataclass
class Client_Packet:
    seq_number: int
    checksum: int
    data: int

@dataclass
class Server_Packet:
    ack_number: int

last_ack_number = 0

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

def fast_retransmit(cwnd, ack, ssthresh, rtt, unacked_packets):

    counts = {}
    retransmit_packets = set()

    for server_packet in ack:
        ack_number = server_packet.ack_number

        counts[ack_number] = counts.get(ack_number, 0) + 1

        if counts[ack_number] == 3:
            if ack_number in unacked_packets:
                retransmit_packets.add(ack_number)

                ssthresh = max(cwnd / 2, 1)
                cwnd = ssthresh

    return cwnd, ssthresh, retransmit_packets

def main():

    one_chunk = 1024
    packets = []

    seq_number = 0

    with open('gistfile1.txt', 'rb') as f:
        while True:
            chunk = f.read(one_chunk)
            if not chunk:
                break

            packet = Client_Packet(
                seq_number=seq_number,
                checksum=0,
                data=chunk
            )
            
            packets.append(packet)
            seq_number += len(chunk)

        return packets

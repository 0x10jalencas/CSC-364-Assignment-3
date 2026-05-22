import struct
import socket
from dataclasses import dataclass



@dataclass
class Client_Packet:
    seq_number: int
    checksum: int
    data: bytes

@dataclass
class Server_Packet:
    ack_number: int

last_ack_number = 0

def slow_start(cwnd, ssthresh, ack, rtt, last_ack_number):
    for server_packet in ack:
        if server_packet.ack_number > last_ack_number:
            cwnd += 1
        
        if cwnd >= ssthresh:
            cwnd = ssthresh
            break
    
    return cwnd, last_ack_number

def congestion_avoidance(cwnd, ack, ssthresh, rtt, last_ack_number):
    for server_packet in ack:
        if server_packet.ack_number > last_ack_number:
            cwnd += 1 / cwnd
            last_ack_number = server_packet.ack_number

    return cwnd, last_ack_number

def fast_retransmit(cwnd, ack, ssthresh, rtt, unacked_packets, last_ack_number):

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

def checksum(data):
    return sum(data) % 65535

def serialize_client_packets(packet):
    header = struct.pack('!IH', packet.seq_number, packet.checksum)
    full_packet = header + packet.data
    return full_packet

def deserialize_server_packets(data):
    ack_number = struct.unpack("!I", data)[0]
    return Server_Packet(ack_number=ack_number)
    

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
                checksum=checksum(chunk),
                data=chunk
            )
            
            packets.append(packet)
            seq_number += len(chunk)
    

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(.5)

    server_address = ("localhost", 5000)

    #testing one packet
    serialized_packet = serialize_client_packets(packets[0])
    client_socket.sendto(serialized_packet, server_address)

    ack_bytes, server = client_socket.recvfrom(1024)
    ack_packet = deserialize_server_packets(ack_bytes)

    # printing test
    print(ack_packet.ack_number)

    return packets


if __name__ == "__main__":
    main()
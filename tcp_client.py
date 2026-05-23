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
            last_ack_number = server_packet.ack_number
        
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

def remove_the_acked_packets(unacked_packets, ack_number):
    acked = []

    for seq_number, packet in unacked_packets.items():
        if seq_number + len(packet.data) <= ack_number:
            acked.append(seq_number)

    for seq_number in acked:
        del unacked_packets[seq_number]


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

    cwnd = 1
    ssthresh = 64
    rtt = 0
    last_ack_number = 0

    next_packet_index = 0
    unacked_packets = {}
    duplicate_ack_count = 0

    cwnd_log = []
    retransmission_log = []
    retransmission_count = 0


    while next_packet_index < len(packets) or len(unacked_packets) > 0:

        while next_packet_index < len(packets) and len(unacked_packets) < int(cwnd):
            packet = packets[next_packet_index]

            serialized_packet = serialize_client_packets(packet)
            client_socket.sendto(serialized_packet, server_address)
            


            unacked_packets[packet.seq_number] = packet
            next_packet_index += 1

        try:
            ack_bytes, server = client_socket.recvfrom(1024)
            ack_packet = deserialize_server_packets(ack_bytes)

            print("received ACK:", ack_packet.ack_number)

            if ack_packet.ack_number > last_ack_number:
                duplicate_ack_count = 0

                remove_the_acked_packets(unacked_packets, ack_packet.ack_number)

                if cwnd < ssthresh:
                    cwnd, last_ack_number = slow_start(
                        cwnd,ssthresh, 
                        [ack_packet],
                        rtt,
                        last_ack_number)
                else:
                    cwnd, last_ack_number = congestion_avoidance(
                        cwnd,
                        [ack_packet],
                        ssthresh,
                        rtt,
                        last_ack_number)
                    


            elif ack_packet.ack_number == last_ack_number:
                duplicate_ack_count += 1

                print("duplicate ACK count:", duplicate_ack_count)

                if duplicate_ack_count == 3:
                    missing_seq = ack_packet.ack_number

                    if missing_seq in unacked_packets:
                        packet = unacked_packets[missing_seq]

                        serialized_packet = serialize_client_packets(packet)
                        client_socket.sendto(serialized_packet, server_address)

                        retransmission_count += 1
                        print("fast retransmit packet:", missing_seq)

                        ssthresh = max(cwnd / 2, 1)
                        cwnd = ssthresh
            rtt += 1
            print("cwnd:", cwnd)
            cwnd_log.append((rtt, cwnd))
            retransmission_log.append((rtt, retransmission_count))


        except socket.timeout:
            print("timeout")


            if len(unacked_packets) > 0:
                oldest_seq = min(unacked_packets)
                packet = unacked_packets[oldest_seq]

                serialized_packet = serialize_client_packets(packet)
                client_socket.sendto(serialized_packet, server_address)
            
                retransmission_count += 1
                print("retransmitting packet:", oldest_seq)
                

                ssthresh = max(cwnd / 2, 1)
                cwnd = 1
                duplicate_ack_count = 0


    with open("cwnd_log.csv", "w") as f:
        f.write("rtt,cwnd\n")
        for rtt_value, cwnd_value in cwnd_log:
            f.write(f"{rtt_value},{cwnd_value}\n")

    with open("retransmission_log.csv", "w") as f:
        f.write("rtt,retransmissions\n")
        for rtt_value, retransmission_value in retransmission_log:
            f.write(f"{rtt_value},{retransmission_value}\n")                

    return packets

if __name__ == "__main__":
    main()
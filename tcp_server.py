import struct
import socket
import random
from dataclasses import dataclass

localhost = "127.0.0.1"

@dataclass
class Client_Packet:
    seq_number: int
    checksum: int
    data: bytes

@dataclass
class Server_Packet:
    ack_number: int

def checksum(data):
    return sum(data) % 65535

def deserialize_client_packets(packet_bytes):
    header = packet_bytes[:6]
    data = packet_bytes[6:]

    seq_number, checksum_value = struct.unpack("!IH", header)

    return Client_Packet(
        seq_number=seq_number,
        checksum=checksum_value,
        data=data
    )

def should_drop_packet(loss_probability):
    return random.random() < loss_probability

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((localhost, 5000))

    expected_seq_number = 0
    loss_probability = 0.01
    buffered_packets = {}

    with open("received.txt", "wb") as f:
        while True:
            full_packet, client_address = server_socket.recvfrom(1030)

            if should_drop_packet(loss_probability):
                print("a dropped packet")
                continue

            packet = deserialize_client_packets(full_packet)

            if checksum(packet.data) != packet.checksum:
                continue
        

            if packet.seq_number >= expected_seq_number:
                buffered_packets[packet.seq_number] = packet.data

                while expected_seq_number in buffered_packets:
                    data = buffered_packets[expected_seq_number]

                    f.write(data)
                    f.flush()

                    del buffered_packets[expected_seq_number]
                    expected_seq_number += len(data)

            ack_number = expected_seq_number
            ack_bytes = struct.pack("!I", ack_number)

            server_socket.sendto(ack_bytes, client_address)

            print("received seq:", packet.seq_number)
            print("sending ACK:", ack_number)


if __name__ == "__main__":
    main()
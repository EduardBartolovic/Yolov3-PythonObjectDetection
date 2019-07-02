"""
@author Eduard Bartolovic Eduard.Bartolovic@posteo.de

test client to test object_detection-yolo.py

this program is sending a file and receives a list.

"""

import socket
#import cv2 as cv
#import matplotlib.pyplot as plt
#import matplotlib.image as mpimg


HOST = '127.0.0.1'  # The server's hostname or IP address
PORT01 = 42425        # The port used by the Client
PORT02 = 42426       # Used by Client
PORT03 = 42427       # Used by Client
PORT1 = 42422        # The port used by the server
PORT2 = 42423       # Used by Server
PORT3 = 42424       # Used by Server


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s3:
            s1.bind((HOST, PORT01))
            s2.bind((HOST, PORT02))
            s3.bind((HOST, PORT03))
            
            print("trying to connect")
            s1.connect((HOST, PORT1))
            print("trying to connect")
            s2.connect((HOST, PORT2))
            print("trying to connect")
            s3.connect((HOST, PORT3))

            try:
                while True:
                    print("+++++++++++++++++++++++")
                    
                    buf1= b"1"
                    buf2= b"1"
                    buf3= b"1"
                    s1.sendall(buf1)
                    s2.sendall(buf2)
                    s3.sendall(buf3)
                    
                    data1 = s1.recv(1)
                    print('Amount of detections: ' + data1.decode())
                    for x in range(int.from_bytes(data1, "big")):
                        size = int.from_bytes(s1.recv(1), "big")
                        result = s1.recv(size)
                        print('Received from server: ' + result.decode())

                    data2 = s2.recv(1)
                    print('Amount of detections: ' + data2.decode())
                    for x in range(int.from_bytes(data2, "big")):
                        size = int.from_bytes(s2.recv(1), "big")
                        result = s2.recv(size)
                        print('Received from server: ' + result.decode())

                    data3 = s3.recv(1)
                    print('Amount of detections: ' + data3.decode())
                    for x in range(int.from_bytes(data3, "big")):
                        size = int.from_bytes(s3.recv(1), "big")
                        result = s3.recv(size)
                        print('Received from server: ' + result.decode())

            finally:
                s1.close()
                s2.close()
                s3.close()

"""
@author Eduard Bartolovic Eduard.Bartolovic@posteo.de

test client to test object_detection-yolo.py

this program is sending a file and receives a list.

This Test will be used in CI

"""

import socket
import subprocess
import time
import sys
import shutil

HOST = '127.0.0.1'  # The server's IP address
PORT01 = 42425        # The port used by the Client
PORT02 = 42426       # Used by Client
PORT03 = 42427       # Used by Client
PORT1 = 42422        # The port used by the server
PORT2 = 42423       # Used by Server
PORT3 = 42424       # Used by Server

def getAnswer(soc,listhave):
    data1 = soc.recv(1) # amount of detection
    for _ in range(int.from_bytes(data1, "big")):
        size = int.from_bytes(soc.recv(1), "big") # length of this detection
        result = soc.recv(size)
        print('Received from server: ' + result.decode())
        listhave.append(result.decode()) # append detection to havelist

def checkForEquality(listwant,listhave): # Check if Want and have is equal
    for i in range(len(listwant)):
        expected = listwant[i].split(',') 
        have = listhave[i].split(',')
        if len(expected) != len(have): #syntax right of detection?
            print("")
            print("Error:")
            print("Expected:")
            print(listwant[i])
            print("Have:")
            print(listhave[i])
            print("")
            return True

        if expected[0] != have[0]: #same class as expected?
                print("")
                print("Error:")
                print("Expected:")
                print(listwant[i])
                print("Have:")
                print(listhave[i])
                print("")
                return True

        for k in range(1,len(expected)-1):
            diff = abs(int(expected[k]) - int(have[k]))
            if diff > 10: # if pixel cords are not same there is a threshhold
                print("")
                print("Error:")
                print("Expected:")
                print(listwant[i])
                print("Have:")
                print(listhave[i])
                print("")
                return True # return Error

if __name__ == '__main__':
    proc = subprocess.Popen('python3 src/aadcUser/mlGuys/python/objectDetectionServer.py TestMode',shell=True) # Start MLServer
    time.sleep(20) # wait for 20 Seconds. ML Server needs a bit of Time
    print("prepare Testing:") # Copy Pictures from test folder into this directory to simulate Filter Client
    shutil.copy2('src/aadcUser/mlGuys/python/testpictures/picture-1.jpg', 'picture-1.jpg')
    shutil.copy2('src/aadcUser/mlGuys/python/testpictures/picture-2.jpg', 'picture-2.jpg')
    shutil.copy2('src/aadcUser/mlGuys/python/testpictures/picture-3.jpg', 'picture-3.jpg')

    print("start Testing:") 
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1: # starting Sockets
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
                    print("+++++++++++++++++++++++")
                    
                    buf1= b"1"
                    buf2= b"1"
                    buf3= b"1"
                    s1.sendall(buf1) # sending a byte to Server
                    s2.sendall(buf2) # sending a byte to Server
                    s3.sendall(buf3) # sending a byte to Server

                    listwant = [] # Construct want list
                    #1
                    listwant.append('2,1075,498,756,316,3,')
                    #2.
                    listwant.append('0,806,455,45,134,-1,')
                    #3.
                    listwant.append('2,308,474,1113,68,0,')
                    #4.
                    listwant.append('0,627,464,40,116,3,')
                    listwant.append('0,514,461,40,125,3,')
                    listwant.append('1,564,494,15,39,3,')
                    #5.
                    listwant.append('2,696,503,717,80,0,')
                    #6
                    listwant.append('1,535,532,31,51,3,')
                    listwant.append('1,719,519,47,72,3,')
                    listwant.append('0,430,470,72,97,3,')
                    listwant.append('0,618,470,43,145,3,')

                    listhave = [] # Have list

                    getAnswer(s1,listhave) # Answer from python Server
                    getAnswer(s2,listhave) # Answer from python Server
                    getAnswer(s3,listhave)  # Answer from python Server

                    print("Next Round:")
                    # Copy Next Round of Pictures from test folder into this directory to simulate Filter Client
                    shutil.copy2('src/aadcUser/mlGuys/python/testpictures/picture-4.jpg', 'picture-1.jpg')
                    shutil.copy2('src/aadcUser/mlGuys/python/testpictures/picture-5.jpg', 'picture-2.jpg')
                    shutil.copy2('src/aadcUser/mlGuys/python/testpictures/picture-6.jpg', 'picture-3.jpg')
                    
                    s1.sendall(buf1)# sending a byte to Server
                    s2.sendall(buf2)# sending a byte to Server
                    s3.sendall(buf3)# sending a byte to Server
                    
                    getAnswer(s1,listhave)# Answer from python Server
                    getAnswer(s2,listhave)# Answer from python Server
                    getAnswer(s3,listhave)# Answer from python Server
                        
                    time.sleep(2) 
                        
                finally:
                    s1.close()
                    s2.close()
                    s3.close()
                    proc.terminate() # Stop Server
                    time.sleep(1)
                    print(" ")
                    print("have:")
                    print(listhave)
                    print(" ")
                    print("expected:")
                    print(listwant)
                    if checkForEquality(listwant,listhave): # compare Want To Have
                        print(" ")
                        print("++++++++++++++++++++++++++++++++++")
                        print("Tests are failing :(")
                        print("++++++++++++++++++++++++++++++++++")
                        print(" ")
                        sys.exit(1) # Exit with Error
                    else:
                        print(" ")
                        print("++++++++++++++++++++++++++++++++++")
                        print("Tests are working :)")
                        print("++++++++++++++++++++++++++++++++++")
                        print(" ")
                        sys.exit() # Exit with sucess
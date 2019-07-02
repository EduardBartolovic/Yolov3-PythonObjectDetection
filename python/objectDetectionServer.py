"""
@author Eduard Bartolovic Eduard.Bartolovic@posteo.de
@version: 25.06.2019

Dieser Python Server bekommt einen ping über das Netzwerk wenn der Client ein Bild fertig auf die Platte schreibt.
Dieser Server nutzt die lidarknet.so zum erkennen der Objekte.
Die Erkennungen werden dann noch bearbeitet:
    - Non-maximum suppression
    - Entfernen der Backup results
    - Entfernen doppelter Erkennungen die durch das mapping von emergency zu car entstehen.
    - Mapping der Klassen zu richtigen id und richtung
    - Umwandlung in String
Die Erkannten Elemente werden dann zurück an den Client gesendet.
Die Antwort besteht darin erstmal einen Byte zu senden mit der Menge an Erkennungen.
Darauf hin werden für jede Erkennung ein Byte mit der Länge der Erkennung und der Erkennung selber gesendet.
Im Anschluss wartet der Server auf ein neues Bild. Der Vorgang wiederholt sich.
Dies passiert aktuell auf 3 Threads. Die Anzahl kann man wahrscheinlich veringern.

"""
import socket
from ctypes import c_float,c_int,Structure,POINTER,pointer,c_void_p,c_char_p,CDLL,RTLD_GLOBAL
import threading
import os
import sys

# Parameters for Server
HOST = '127.0.0.1'  # localhost
PORT1 = 42422        # Port to listen on
PORT2 = 42423        # Port to listen on
PORT3 = 42424        # Port to listen on

#Activate print statements 
DEBUG = True

# Initialize the parameters of neuronal network
confThreshold = 0.1  #Confidence threshold
nmsThreshold = 0.2   #Non-maximum suppression threshold

sem = threading.Semaphore() #semaphore to control access to GPU
try:
    if(sys.argv[1] == 'TestMode' or sys.argv[2] == 'TestMode'):# TestMode is used on CI
        print("TestMode")
        LOCATION_LIBDARKNET = "src/aadcUser/mlGuys/python/libdarknetCPU.so"
        LOCATION_CFG = b"src/aadcUser/mlGuys/python/trainedyolo.cfg"
        LOCATION_WEIGHTS = b"src/aadcUser/mlGuys/python/trainedyolo.weights"
        LOCATION_DATA = b"src/aadcUser/mlGuys/python/test.data"
        imloc1 = b"picture-1.jpg"
        imloc2 = b"picture-2.jpg"
        imloc3 = b"picture-3.jpg"
        # Initialize the parameters of neuronal network
        confThreshold = 0.5  #Confidence threshold
        nmsThreshold = 0.4   #Non-maximum suppression threshold
    elif(sys.argv[1] == 'LocalMode'): # LocalMode is used on a local machine
        LOCATION_LIBDARKNET = "libdarknet.so"
        LOCATION_CFG = b"trainedyolo.cfg"
        LOCATION_WEIGHTS = b"trainedyolo.weights"
        LOCATION_DATA = b"training.data"
        imloc1 = b"picture-1.jpg"
        imloc2 = b"picture-2.jpg"
        imloc3 = b"picture-3.jpg"
        # Initialize the parameters of neuronal network
        confThreshold = 0.5  #Confidence threshold
        nmsThreshold = 0.4   #Non-maximum suppression threshold
    else:                             # This Mode is used on Car
        LOCATION_LIBDARKNET = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/libdarknet.so"
        LOCATION_CFG = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/trainedyolo.cfg"
        LOCATION_WEIGHTS = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/trainedyolo.weights"
        LOCATION_DATA = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/training.data"
        imloc1 = b"picture1.png"
        imloc2 = b"picture2.png"
        imloc3 = b"picture3.png"
        # Initialize the parameters of neuronal network
        confThreshold = 0.1  #Confidence threshold
        nmsThreshold = 0.2   #Non-maximum suppression threshold
except:
    LOCATION_LIBDARKNET = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/libdarknet.so"
    LOCATION_CFG = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/trainedyolo.cfg"
    LOCATION_WEIGHTS = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/trainedyolo.weights"
    LOCATION_DATA = b"/home/aadc/AADC/src/aadcUser/mlGuys/python/training.data"
    # Image location
    imloc1 = b"picture1.png"
    imloc2 = b"picture2.png"
    imloc3 = b"picture3.png"
    # Initialize the parameters of neuronal network
    confThreshold = 0.1  #Confidence threshold
    nmsThreshold = 0.2   #Non-maximum suppression threshold


#This is used for the comunication with C++ Libary
class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]

#This is used for the comunication with C++ Libary
class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]

#This is used for the comunication with C++ Libary
class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]

#This is used for the comunication with C++ Libary
class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]


#Load shared object file for Darknetlibary
lib = CDLL(os.path.abspath(LOCATION_LIBDARKNET), RTLD_GLOBAL)
#lib = CDLL(LOCATION_LIBDARKNET, RTLD_GLOBAL)
lib.network_width.argtypes = [c_void_p]
lib.network_width.restype = c_int
lib.network_height.argtypes = [c_void_p]
lib.network_height.restype = c_int

predict = lib.network_predict
predict.argtypes = [c_void_p, POINTER(c_float)]
predict.restype = POINTER(c_float)

get_network_boxes = lib.get_network_boxes
get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int)]
get_network_boxes.restype = POINTER(DETECTION)

make_network_boxes = lib.make_network_boxes
make_network_boxes.argtypes = [c_void_p]
make_network_boxes.restype = POINTER(DETECTION)

free_detections = lib.free_detections
free_detections.argtypes = [POINTER(DETECTION), c_int]

network_predict = lib.network_predict
network_predict.argtypes = [c_void_p, POINTER(c_float)]

load_net = lib.load_network
load_net.argtypes = [c_char_p, c_char_p, c_int]
load_net.restype = c_void_p

do_nms_obj = lib.do_nms_obj
do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

free_image = lib.free_image
free_image.argtypes = [IMAGE]

load_meta = lib.get_metadata
lib.get_metadata.argtypes = [c_char_p]
lib.get_metadata.restype = METADATA

load_image = lib.load_image_color
load_image.argtypes = [c_char_p, c_int, c_int]
load_image.restype = IMAGE

predict_image = lib.network_predict_image
predict_image.argtypes = [c_void_p, IMAGE]
predict_image.restype = POINTER(c_float)

#Detection Methode returns Detections in a list
def detect(net, meta, image, thresh=confThreshold, hier_thresh= confThreshold, nms=nmsThreshold):
    num = c_int(0)
    pnum = pointer(num)

    sem.acquire() #semaphore to control access to GPU
    predict_image(net, image)#only one thread is allowed to access the GPU at once
    sem.release() #semaphore to control access to GPU

    dets = get_network_boxes(net, image.w, image.h, thresh, hier_thresh, None, 0, pnum) #get result
    num = pnum[0] 
    if (nms): # remove overlapping boxes
        do_nms_obj(dets, num, meta.classes, nms)

    res = []
    for j in range(num):
        for i in range(meta.classes):
            if dets[j].prob[i] > 0:
                b = dets[j].bbox
                res.append((meta.names[i], dets[j].prob[i], (b.x, b.y, b.w, b.h)))
    free_image(image)
    free_detections(dets, num)
    return res

#Wait for ping from client so that picture is ready
def getPic(conn):
    print('Wait for Picture')
    conn.recv(1)

# Sending answer back to Client
def sendAnswer(conn,answer):
    #print("sending Answer")
    print("Amount of Detections:"+ str(len(answer)))
    conn.sendall(bytes([len(answer)])) # amount of detections
    for det in answer:
        strin = detectionToString(det) # convert Detection Tuple to string
        conn.sendall(bytes([len(str.encode(strin))])) #size of each detections
        conn.sendall(str.encode(strin))          #  detections itself
    #print("send sucessfull")

#Tuple to String:
# Mapping classes to right id
def detectionToString(detection):
    #print(detection) # detection before mapping
    id = -1
    direction = -1
    if(detection[0]==b'0'): #person
        id = 0
        direction = -1
    elif(detection[0]==b'1'): #personleft
        id = 0
        direction = 0
    elif(detection[0]==b'2'): #personright
        id = 0
        direction = 1
    elif(detection[0]==b'3'): #personbackward
        id = 0
        direction = 2
    elif(detection[0]==b'4'): #personforward
        id = 0
        direction = 3
    elif(detection[0]==b'5'): #child
        id = 1
        direction = -1   
    elif(detection[0]==b'6'): #childleft
        id = 1
        direction = 0
    elif(detection[0]==b'7'): #childright
        id = 1
        direction = 1
    elif(detection[0]==b'8'): #childbackward
        id = 1
        direction = 2
    elif(detection[0]==b'9'): #childforward
        id = 1
        direction = 3
    elif(detection[0]==b'10'): #car
        id = 2
        direction = -1
    elif(detection[0]==b'11'): #carleft
        id = 2
        direction = 0
    elif(detection[0]==b'12'): #carright
        id = 2
        direction = 1
    elif(detection[0]==b'13'): #carbackward
        id = 2
        direction = 2
    elif(detection[0]==b'14'): #carforward
        id = 2
        direction = 3
    elif(detection[0]==b'15'): #emergency
        id = 2 #should be 3 but dataset is too bad for this now
        direction = -1
    elif(detection[0]==b'16'): #emergencyleft
        id = 2 #should be 3 but dataset is too bad for this now
        direction = 0
    elif(detection[0]==b'17'): #emergencyright
        id = 2 #should be 3 but dataset is too bad for this now
        direction = 1
    elif(detection[0]==b'18'): #emergencybackward
        id = 2 #should be 3 but dataset is too bad for this now
        direction = 2
    elif(detection[0]==b'19'): #emergencyforward
        id = 2 #should be 3 but dataset is too bad for this now
        direction = 3
    else: # should not happen 
        print("ERROR: CLASS NOT KNOWN")
        id= -1
        direction = -1
    
    if DEBUG:
        print("Detection: "+ str(id) + " Percantage:" + str(detection[1]) + " X:" + str(detection[2][0]) + " Y:" + str(detection[2][1]) + " Width:" + str(detection[2][2]) + " Height:" + str(detection[2][3]) + " Direction:" +str(direction))

    return f"{id},{int(detection[2][0])},{int(detection[2][1])},{int(detection[2][2])},{int(detection[2][3])},{int(direction)},"# id,x,y,w,h,d;

# Remove backup result if better one is availabel
# Example: In one Frame detections with class 0 and 2 then delete 0 because 2 is more precise
def removeBackup(det):
    if len(det) < 2: # if there is only a single Detection nothing needs to done
        return det

    trueDet = []
    for index in range(len(det)): # iterate over all detections
        #Just interested in Backup class
        if det[index][0] == b'0' or det[index][0] == b'5' or det[index][0] == b'10' or det[index][0] == b'15':
            delete = False
            for index2 in range(len(det)):
                if not delete: #if found stop
                    if index != index2: # dont be yourself
                        v = int(det[index][0])
                        w = int(det[index2][0])
                        #check if both detections are in same class and are the same box
                        delete = w-v < 5 and w-v > 0 and det[index][2] == det[index2][2]
            if not delete:
                trueDet.append(det[index]) # there is nothing better
        else: 
            trueDet.append(det[index]) 
    return trueDet

#Because of the mapping from emergency to car there is a problem of having two same boxes.
def removeDouble(det):
    if len(det) < 2: 
        return det

    trueDet = []
    saved = []
    for index in range(len(det)): #iterate over all detections
        delete = False
        for index2 in range(len(det)):
            if not delete: #if found stop
                if index != index2: # dont be yourself
                    v = int(det[index][0])
                    w = int(det[index2][0])
                    delete =  v>9 and w>9 and det[index][2] == det[index2][2] # if same box cords
                    if delete and index not in saved: # just delete one of the two boxes
                        trueDet.append(det[index2])
                        saved.append(index2)
        if not delete :
            trueDet.append(det[index])
    return trueDet

# Detector Thread
def thread_detector(conn,imloc):
    try:
        print("Thread started")
        for counter in range(9999999):
            print(str(counter))#+"++++++++")
                    
            getPic(conn)

            image = load_image(imloc, 0, 0)
            detections = detect(net, meta, image)
            #print(detections)
            trueDet = removeBackup(detections)
            trueDet2 = removeDouble(trueDet)
            sendAnswer(conn, trueDet2)
    except:
        print("Connection Closed")
        conn.close()
        sys.exit()


#++++++++++++Main+++++++++++++++++++++++++++++++++++++
if __name__ == '__main__':
    net = load_net(os.path.abspath(LOCATION_CFG), os.path.abspath(LOCATION_WEIGHTS), 0) #init net
    meta = load_meta(os.path.abspath(LOCATION_DATA)) # load name file
    #init sockets
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s3:
                s1.bind((HOST, PORT1))
                s2.bind((HOST, PORT2))
                s3.bind((HOST, PORT3))

                s1.listen(1)
                s2.listen(1)
                s3.listen(1)

                print("Waiting for first connection")
                conn1, _ = s1.accept() #init connection
                print("Waiting for seccond connection")
                conn2, _ = s2.accept() #init connection
                print("Waiting for third connection")
                conn3, _ = s3.accept() #init connection


                # we could propabliy lower the amount of threads
                x1 = threading.Thread(target=thread_detector, args=(conn1,imloc1))
                x2 = threading.Thread(target=thread_detector, args=(conn2,imloc2))
                x3 = threading.Thread(target=thread_detector, args=(conn3,imloc3))

                x1.start()
                x2.start()
                x3.start()

    s1.close()
    s2.close()
    s3.close()

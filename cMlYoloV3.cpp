/*
 * Filter fuer die Objectdetection.
 * Dieser Fliter baut eine Verbindung auf zum Pythonserver.
 * Die Bilder kommend vom Fisheye undistorter werden auf die Platte(RAMdrive) gespeichert.
 * Durch einen kleinen Netzwerkping weis der Pythonserver das das Bild bereit ist.
 * Die Antwort kommt als eine Liste von Detections über das Netwerk.
 * Diese Liste wird aufbereitet und auf einen Output Pin geschrieben.
 *
 * Authors:
 *    -Marcel Reineck (reineck@hm.edu)
 *    -Eduard Bartolovic (Eduard.Bartolovic@posteo.de)
 */

#include "stdafx.h"
#include "cMlYoloV3.h"
#include "ADTF3_OpenCV_helper.h"

// Ports für Pythonserver
#define PORT1 42422
#define PORT2 42423
#define PORT3 42424

typedef unsigned char byte;


ADTF_TRIGGER_FUNCTION_FILTER_PLUGIN(CID_ADTF_SAM_ML_YOLOV3,
                                    FILTER_CLASS_LABEL,
                                    cMlYoloV3,
                                    adtf::filter::pin_trigger({ "input" }));

cMlYoloV3::cMlYoloV3() : mDetectionsOutputPin("detections", "singleMlDetection", this)
{
    //create and set inital input format type
    m_sInputFormat.m_strFormatName = ADTF_IMAGE_FORMAT(RGB_24);
    adtf::ucom::object_ptr<IStreamType> pType = adtf::ucom::make_object_ptr<cStreamType>(stream_meta_type_image());
    set_stream_type_image_format(*pType, m_sInputFormat);

    //register input pin
    Register(m_oReader, "input", pType);
    //register output pin
    Register(m_oImagePinWriter, "unused", pType);

    //register callback for type changes
    m_oReader.SetAcceptTypeCallback([this](const adtf::ucom::ant::iobject_ptr<const adtf::streaming::ant::IStreamType>& pType) -> tResult
    {
        return ChangeType(m_oReader, m_sInputFormat, *pType.Get(), m_oImagePinWriter);
    });
}

//implement the Configure function to read ALL Properties
tResult cMlYoloV3::Configure()
{
    // TODO: 26.06.19 put the start client into initialize with run level
    // Setup for the 3 clients
    StartServer(&sock1, &inWork1, PORT1);
    StartServer(&sock2, &inWork2, PORT2);
    StartServer(&sock3, &inWork3, PORT3);

    // TODO: implement RAM Drive or other IPC
//    if (!startedPython) {
//        startedPython = true;
//        system("python3 /home/aadc/AADC/src/aadcUser/mlGuys/python/objectDetectionServer.py");
//    }
//    if (!mountedRamDisk) {
//        mountedRamDisk = true;
//        system("sudo mkdir /home/aadc/AADC/src/aadcUser/mlGuys/python/ramdisk");
//        system("sudo chmod 777 /home/aadc/AADC/src/aadcUser/mlGuys/python/ramdisk");
//        system("sudo mount -t tmpfs -o size=100M none /home/aadc/AADC/src/aadcUser/mlGuys/python/ramdisk");
//        system("sudo mount tmpfs");
//    }
}

tResult cMlYoloV3::Process(tTimeStamp tmTimeOfTrigger)
{
    if (!inWork1) {  //only one Thread should be able to access this part
        inWork1 = true;
        //LOG_INFO("Work1");
        ProcessPicture(&sock1, "/home/aadc/AADC/src/aadcUser/mlGuys/python/picture1.png");
        inWork1 = false;
    }else if (!inWork2) {
        inWork2 = true;
        //LOG_INFO("Work2");
        ProcessPicture(&sock2, "/home/aadc/AADC/src/aadcUser/mlGuys/python/picture2.png");
        inWork2 = false;
    }else if (!inWork3) {
        inWork3 = true;
        //LOG_INFO("Work3");
        ProcessPicture(&sock3, "/home/aadc/AADC/src/aadcUser/mlGuys/python/picture3.png");
        inWork3 = false;
    }
}

tResult cMlYoloV3::StartServer(int *sock, bool *inWork, int port) {
    *sock = 0;
    *inWork = false;

    if ((*sock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        LOG_ERROR("Socket creation error");
        RETURN_ERROR(ERR_NOT_CONNECTED);
    }

    memset(&serv_addr, '0', sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    // Convert IPv4 and IPv6 addresses from text to binary form
    if(inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)<=0)
    {
        LOG_ERROR("Invalid address/ Address not supported");
        RETURN_ERROR(ERR_NOT_CONNECTED);
    }

    if (connect(*sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
        LOG_ERROR("Connection Failed");
        RETURN_ERROR(ERR_NOT_CONNECTED);
    }
    LOG_INFO("CONFIGURATION DONE");
    RETURN_NOERROR;
}

tResult cMlYoloV3::ProcessPicture(int *sock, std::string filepath) {

    object_ptr<const ISample> pReadSample;

    if (IS_OK(m_oReader.GetNextSample(pReadSample))) {
        object_ptr_shared_locked<const ISampleBuffer> pReadBuffer;
        //lock read buffer
        if (IS_OK(pReadSample->Lock(pReadBuffer))) {
            //create a opencv matrix from the media sample buffer
            Mat image(cv::Size(m_sInputFormat.m_ui32Width, m_sInputFormat.m_ui32Height),
                      CV_8UC3, (uchar *) pReadBuffer->GetPtr());

            // TODO: 15.05.19 Maybe dont write the image onto the system -> RAM Disk
            imwrite(filepath, image);
            std::ifstream ifs(filepath);

            //send ping to server
            char buf[1] = {1};
            send(*sock, buf, 1, 0);


            //receive answer from ML Server
            char length_buffer[1] = {0};
            read(*sock, length_buffer, 1); // amount of detections
            int detectionAmount = length_buffer[0];

            char buffer[256] = {0};
            for (int i = 0; i < detectionAmount; i++) {
                read(*sock, length_buffer, 1); // length of this detection
                int lengthOfDetection = length_buffer[0];
                read(*sock, buffer, lengthOfDetection); //class,cord,direction...
                std::string s(buffer);
                // If index is 2 digits long, the program crashes.
                // the reason is this line => std::string s(buffer);
                // but python server should not send anything like that


                //Extracating x_coord :
                int index = 2; // start at 2 because id is fist char then comma is seccond,
                int indexAfter = index;
                do {
                    indexAfter++;
                } while (buffer[indexAfter] != ','); //search for next comma
                std::string xCoord_s = s.substr(index, indexAfter - index);
                int x_coord = std::stoi(xCoord_s.c_str());

                // Extracting y_coord :
                indexAfter++; // Because the index is at the ','
                index = indexAfter;
                do {
                    indexAfter++;
                } while (buffer[indexAfter] != ',');  //search for next comma
                std::string yCoord_s = s.substr(index, indexAfter - index);
                int y_coord = std::stoi(yCoord_s.c_str());

                // Extracting width :
                indexAfter++; // Because the index is at the ','
                index = indexAfter;
                do {
                    indexAfter++;
                } while (buffer[indexAfter] != ','); //search for next comma
                std::string width_s = s.substr(index, indexAfter - index);
                int width = std::stoi(width_s.c_str());

                // Extracting height :
                indexAfter++; // Because the index is at the ','
                index = indexAfter;
                do {
                    indexAfter++;
                } while (buffer[indexAfter] != ','); //search for next comma
                std::string height_s = s.substr(index, indexAfter - index);
                int height = std::stoi(height_s.c_str());

                // Extracting direction :
                indexAfter++; // Because the index is at the ','
                index = indexAfter;
                do {
                    indexAfter++;
                } while (buffer[indexAfter] != ','); //search for last comma
                std::string direction_s = s.substr(index, indexAfter - index);
                int direction = std::stoi(direction_s.c_str());

                // Calculate location: left, middle or right of screen using x_coord
                tInt32 location;
                if (x_coord < 325) { // TODO: Check if this is still right (Using left corner or middle of box?)
                    location = 0;
                } else if (x_coord < 955) {  // TODO: Check if this is still right (Using left corner or middle of box?)
                    location = 1;
                } else {
                    location = 2;
                }

                // TODO: 19.6.19 distance not calculated yet => look in Markerdetector

                //Building Output Struct:
                singleMlDetection detection = {tInt32(buffer[0] - '0'),tInt32(direction),tInt32(location),tInt32(-1)};
                mDetectionsOutputPin.WriteField("id", &detection.id);
                mDetectionsOutputPin.WriteField("facing", &detection.facing);
                mDetectionsOutputPin.WriteField("location", &detection.location);
                mDetectionsOutputPin.WriteField("distance", &detection.distance);
                mDetectionsOutputPin.TransmitSample();
                //LOG_INFO("id: %d, distance: %d, location: %d, facing: %d", detection.id, detection.distance, detection.location, detection.facing);
            }

            if (detectionAmount == 0){ //Backup case if there is no detection in Frame
                singleMlDetection detection = {tInt32(-1),tInt32(-1),tInt32(-1),tInt32(-1)};
                mDetectionsOutputPin.WriteField("id", &detection.id);
                mDetectionsOutputPin.WriteField("facing", &detection.facing);
                mDetectionsOutputPin.WriteField("location", &detection.location);
                mDetectionsOutputPin.WriteField("distance", &detection.distance);
                mDetectionsOutputPin.TransmitSample();
            }

            ifs.close();
        }
    }
    RETURN_NOERROR;
}

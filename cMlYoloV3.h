/*
 * Header file ML YoloV3 Filter.
 */

#pragma once

using namespace adtf_util;
using namespace ddl;
using namespace adtf::ucom;
using namespace adtf::base;
using namespace adtf::streaming;
using namespace adtf::mediadescription;
using namespace adtf::filter;
using namespace std;
using namespace cv;

#include "cOutputPin.h"
#include "sam_structs.h"

/// Name of the filter in ADTF
#define FILTER_CLASS_LABEL "SAM ML YoloV3"
#define CID_ADTF_SAM_ML_YOLOV3 "adtf.sam.ml_yolo_v_drei"

class cMlYoloV3 : public cTriggerFunction {

private:

    // SocketPorts:
    int sock1;
    int sock2;
    int sock3;

    // Synchronisation for Threads
    bool inWork1;
    bool inWork2;
    bool inWork3;
    bool pythonServer;
    bool ramDisk;
    struct sockaddr_in serv_addr;

    /*! The image pin reader */
    cPinReader m_oReader;

    /*! The image pin writer */
    cPinWriter m_oImagePinWriter;

    cOutputPin mDetectionsOutputPin;

    /*! The vector pin writer */
    cPinWriter m_oPosePinWriter;

    //Stream Formats
    /*! The input format */
    adtf::streaming::tStreamImageFormat m_sInputFormat;
    /*! The output format */
    adtf::streaming::tStreamImageFormat m_sOutputFormat;

    //helper Methodes
    tResult StartServer(int *sock, bool *inWork, int port);
    tResult ProcessPicture(int *sock, std::string filepath);

public:

    /*! Default constructor. */
    cMlYoloV3();

    /*! Destructor. */
    virtual ~cMlYoloV3() = default;

    /**
    * Overwrites the Configure
    */
    tResult Configure();
    /**
    * Overwrites the Processs
    */
    tResult Process(tTimeStamp tmTimeOfTrigger);

    // TODO: 26.06.19 initialize methode with correct level of initialization
};
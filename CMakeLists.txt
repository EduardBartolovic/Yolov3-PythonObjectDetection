cmake_minimum_required(VERSION 3.10.0)

project(mlGuys)

include_directories( ${OpenCV_INCLUDE_DIRS} )

set (SOURCEFILES
        stdafx.h
		cMlYoloV3.h
		cMlYoloV3.cpp
		)

adtf_add_filter(${PROJECT_NAME}
				${SOURCEFILES}
)

adtf_install_target(${PROJECT_NAME} bin)

adtf_create_plugindescription(
    TARGET
        ${PROJECT_NAME}
    PLUGIN_SUBDIR
        "bin"
 )

#install dlls for opencv to binary folder

if(WIN32)
	install(FILES "${OpenCV_DIR}/${OpenCV_ARCH}/${OpenCV_RUNTIME}/bin/opencv_world${OpenCV_VERSION_MAJOR}${OpenCV_VERSION_MINOR}${OpenCV_VERSION_PATCH}d.dll" DESTINATION ${CMAKE_INSTALL_BINARY}/debug CONFIGURATIONS Debug)
	install(FILES "${OpenCV_DIR}/${OpenCV_ARCH}/${OpenCV_RUNTIME}/bin/opencv_world${OpenCV_VERSION_MAJOR}${OpenCV_VERSION_MINOR}${OpenCV_VERSION_PATCH}.dll" DESTINATION ${CMAKE_INSTALL_BINARY} CONFIGURATIONS RelWithDebInfo Release)
endif(WIN32)


target_link_libraries(${PROJECT_NAME} LINK_PUBLIC ${OpenCV_LIBS}
		PIN_LIBRARY
		DEFINES_LIBRARY)

#this is to add a folder within the ADTF solution
set_property(TARGET ${PROJECT_NAME} PROPERTY FOLDER mlGuys)
set_property(TARGET ${PROJECT_NAME}_pdgen PROPERTY FOLDER mlGuys)


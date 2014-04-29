#-------------------------------------------------
#
# Project created by QtCreator 2014-04-26T09:35:42
#
#-------------------------------------------------

QT       += core

QT       -= gui

TARGET = cropper
CONFIG   += console
CONFIG   -= app_bundle

TEMPLATE = app


SOURCES += main.cpp

CONFIG += static

INCLUDEPATH += /usr/include/opencv2
LIBS += -lopencv_core
LIBS += -lopencv_highgui

HEADERS +=

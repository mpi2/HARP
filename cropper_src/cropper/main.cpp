#include <QtCore/QCoreApplication>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <iostream>
#include <cstdlib>
#include <fstream>
#include <string>
#include <QFile>
#include <QTextStream>
#include <QDir>
#include <QFileInfo>
#include <QDebug>

using namespace cv;

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    //std::cout << argv[1] << std::endl;
    //cout << "Hello world!" << endl;
    int left = atoi(argv[2]);
    int top  = atoi(argv[3]);
    int width = atoi(argv[4]);
    int height = atoi(argv[5]);

    //read file names from file
    QFile inputFile(argv[1]);
    if (inputFile.open(QIODevice::ReadOnly))
    {
        Mat src;
        Mat cropped;
        int count = 0;
        int count_at = 20;
        QTextStream in(&inputFile);
        while ( !in.atEnd() )
        {

            QString line = in.readLine();
            count += 1;
            if (count % 20 == 0){
                qDebug() << count_at;
                count = 0;
            }
            QFileInfo fi(line);
            QString base = fi.completeBaseName();
            QString outpath = QDir(argv[6]).filePath(base + ".tif");
            std::string inpath = line.toStdString();
            //std::cout << "path" <<  outpath.toStdString();
            src = imread(inpath, CV_LOAD_IMAGE_GRAYSCALE);   // Read the file
            cropped = src(Rect(left,top,width,height)).clone();
            imwrite(outpath.toStdString(), cropped);


         }
         inputFile.close();
         qDebug() << "success";
    }else{
        qDebug() << "failed cropping. Can't read file list";
    }

    return a.exec();
}

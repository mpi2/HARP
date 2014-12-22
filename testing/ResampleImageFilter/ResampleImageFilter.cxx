#include "itkImage.h"
#include "itkImageFileWriter.h"
#include "itkImageFileReader.h"
#include "itkBinShrinkImageFilter.h"
#include <cstdlib>
#include <iostream>
#include "itkRawImageIO.h"





int main(int argc, char *argv[])
{

  
  const long int scaleFactor = 3;//strtol(argv[3], NULL, 10);
  std::cout << "print+++++++++++++"; // Prints OK  
  typedef itk::Image< unsigned char, scaleFactor>         ImageType;
  typedef itk::ImageFileReader<ImageType> ReaderType;
 
  
//  ReaderType::Pointer reader = ReaderType::New();
//  reader->SetFileName(argv[1]);
//  reader->SetUseStreaming(true);
//  reader->Update();
  
  // Output all images as shorts until we know how to get input pixel type
  
  
  
  //Shrink the image
//  typedef itk::BinShrinkImageFilter<ImageType, ImageType> BinShrinkType;
//  BinShrinkType::Pointer shrinker = BinShrinkType::New();
//  shrinker->SetShrinkFactors(2);
//  shrinker->SetInput(reader->GetOutput());
  
  
//  typedef itk::RawImageIO <short, 3> ImageIOType;
//ImageIOType::Pointer rimageio = ImageIOType::New();
//rimageio->SetDimensions( 0, 1086 );
//rimageio->SetDimensions( 1, 1542 );
//rimageio->SetDimensions( 2, 2472);
//rimageio->SetSpacing( 0, 1.0 );
//rimageio->SetSpacing( 1, 1.0 );
//rimageio->SetHeaderSize(1086*1542*2472);

  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName(argv[1]);
  reader->SetImageIO(rimageio);
  reader->SetUseStreaming(true);
  reader->Update();
 
  typedef  itk::ImageFileWriter< ImageType  > WriterType;
  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(argv[2]);
  writer->SetNumberOfStreamDivisions( 2000);
  writer->SetInput(reader->GetOutput());
  writer->Update();

 
}



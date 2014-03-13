#!/usr/bin/python

<<<<<<< HEAD
'''
This script was made using vtk 6.1
'''

from vtk import *
import sys
import os
import matplotlib.animation as animation
import numpy as np
from pylab import *
import subprocess as sub


class Animator:
    def __init__(self, tiff, outputDir):
        file_ = sys.argv[1]
        reader =  vtkTIFFReader()
        reader.SetFileName(file_)
        reader.Update()

        # Color
        colorTransferFunction = vtkColorTransferFunction()
        colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(20.0, 1.0, 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(120.0, 0.0, 1.0, 0.0)
        colorTransferFunction.AddRGBPoint(180.0, 0.0, 0.0, 1.0)
        colorTransferFunction.AddRGBPoint(255.0, 0.0, 1.0, 1.0)

        volumeProperty = vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)

        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()


        self.isoFunction = vtkVolumeRayCastIsosurfaceFunction()
        self.isoFunction.SetIsoValue(45.0)

        volumeMapper = vtkVolumeRayCastMapper()
        volumeMapper.SetVolumeRayCastFunction( self.isoFunction )
        volumeMapper.SetInputConnection(reader.GetOutputPort())

        volume = vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)


        # Bounding box.
        outlineData = vtkOutlineFilter()
        outlineData.SetInputConnection(reader.GetOutputPort())
        outlineMapper = vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outlineData.GetOutputPort())
        outline = vtkActor()
        outline.SetMapper(outlineMapper)
        outline.GetProperty().SetColor(0.9, 0.9, 0.9)

        # Set a better camera position
        camera = vtkCamera()
        camera.SetViewUp(0, 0, 0)
        camera.SetPosition(-2, -2, -2)

        # Create the Renderer, Window and Interator
        self.ren = vtkRenderer()
        #ren.AddActor(outline)
        self.ren.AddVolume(volume)
        self.ren.SetBackground(0.1, 0.1, 0.2)
        self.ren.SetActiveCamera(camera)
        self.ren.ResetCamera()

        self.renWin = vtkRenderWindow()
        self.renWin.AddRenderer(self.ren)
        self.renWin.SetWindowName("CT iso-surface");
        self.renWin.SetSize(500, 500)


        iren = vtkRenderWindowInteractor()
        iren.AddObserver("KeyPressEvent", self.Keypress)
        iren.SetRenderWindow(self.renWin)
        iren.Initialize()
        self.renWin.Render()
        iren.Start()


    def Keypress(self, obj, event):

        key = obj.GetKeySym()
        # make a movie by rotating the scene 360 degrees
        if key == "x":
            self.rotate(obj, event)
        if key == "z":
            self.isovalues(obj, event)


    def rotate(self, obj, event):
        for i in range(0, 180,1):
            w2i = vtkWindowToImageFilter()
            w2i.Modified()
            w2i.SetInput(self.renWin)
            w2i.Update()

            writer = vtkPNGWriter()
            #writer.SetQuality(100)
            writer.SetInputData(w2i.GetOutput())#SetInput is deprecated???
            filename = 'movie_'+'0'*(6-len(str(i)))+str(i)+".png"
            writer.SetFileName(filename)
            writer.Write()
            print filename
            if i <> 720:
                self.ren.GetActiveCamera().Azimuth(2.0)
            self.renWin.Render()
        self.makeMovie()


    def isovalues(self, obj, event):
        '''
        Gradually dissolve away the embryo using varrying ios values
        '''


        path = os.getcwd()
        # make a movie by rotating the scence 360 degrees
        for i in range(0, 180,1):

            self.isoFunction.SetIsoValue(i)
            w2i = vtkWindowToImageFilter()
            w2i.SetInput(self.renWin)
            writer = vtkPNGWriter()
            writer.SetInputData(w2i.GetOutput())
            filename = 'movie_'+'0'*(6-len(str(i)))+str(i)+".png"
            writer.SetFileName(os.path.join(path, filename))
            #writer.Write()
            print os.path.join(path, filename)
            self.renWin.Render()
=======
# Volume rendering of Liver data

from vtk import *
import sys
>>>>>>> 345459f3054c7d246e2a517d240c2489a8f51079


    def makeMovie(self):
        sub.call([])

if __name__=="__main__":
    tiffVol = sys.argv[1]
    outputDir = sys.argv[2]
    animator = Animator(tiffVol, outputDir)


<<<<<<< HEAD
=======
#reader = vtkStructuredPointsReader()
reader =  vtkTIFFReader()
#reader.SetFileName(file_)
reader.ReadVolume(file_)
reader.Update()

cast = vtkImageCast()
cast.SetInputConnection(reader.GetOutputPort() )
cast.SetOutputScalarTypeToUnsignedChar()
cast.ClampOverflowOn()

# Color
colorTransferFunction = vtkColorTransferFunction()
colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
colorTransferFunction.AddRGBPoint(20.0, 1.0, 0.0, 0.0)
colorTransferFunction.AddRGBPoint(120.0, 0.0, 1.0, 0.0)
colorTransferFunction.AddRGBPoint(180.0, 0.0, 0.0, 1.0)
colorTransferFunction.AddRGBPoint(255.0, 0.0, 1.0, 1.0)

volumeProperty = vtkVolumeProperty()
volumeProperty.SetColor(colorTransferFunction)

volumeProperty.ShadeOn()
volumeProperty.SetInterpolationTypeToLinear()

isoFunction = vtkVolumeRayCastIsosurfaceFunction()
isoFunction.SetIsoValue(160.0)

volumeMapper = vtkVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction( isoFunction )
volumeMapper.SetInputConnection(cast.GetOutputPort())

volume = vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volumeProperty)


# Bounding box.
outlineData = vtkOutlineFilter()
outlineData.SetInputConnection(cast.GetOutputPort())
outlineMapper = vtkPolyDataMapper()
outlineMapper.SetInputConnection(outlineData.GetOutputPort())
outline = vtkActor()
outline.SetMapper(outlineMapper)
outline.GetProperty().SetColor(0.9, 0.9, 0.9)

# Set a better camera position
camera = vtkCamera()
camera.SetViewUp(0, 0, -1)
camera.SetPosition(-2, -2, -2)

# Create the Renderer, Window and Interator
ren = vtkRenderer()
ren.AddActor(outline)
ren.AddVolume(volume)
ren.SetBackground(0.1, 0.1, 0.2)
ren.SetActiveCamera(camera)
ren.ResetCamera()

renWin = vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetWindowName("Volume rendering of Liver data");
renWin.SetSize(500, 500)

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

iren.Initialize()
renWin.Render()
iren.Start()
>>>>>>> 345459f3054c7d246e2a517d240c2489a8f51079




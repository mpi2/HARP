#!/usr/bin/python

# Volume rendering of Liver data

from vtk import *
import sys
import os


#Based on file from here

file_ = sys.argv[1]

#reader = vtkStructuredPointsReader()
reader =  vtkTIFFReader()
#reader.SetFileName(file_)
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


isoFunction = vtkVolumeRayCastIsosurfaceFunction()
isoFunction.SetIsoValue(45.0)

volumeMapper = vtkVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction( isoFunction )
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
ren = vtkRenderer()
ren.AddActor(outline)
ren.AddVolume(volume)
ren.SetBackground(0.1, 0.1, 0.2)
ren.SetActiveCamera(camera)
ren.ResetCamera()

renWin = vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetWindowName("CT iso-surface");
renWin.SetSize(500, 500)

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)


def Keypress(obj, event):

    key = obj.GetKeySym()

    global renWin, ren

    path = os.getcwd()
    # make a movie by rotating the scence 360 degrees
    if key == "m":
        for i in range(0, 180,1):

            renWin.Render()
            w2i = vtkWindowToImageFilter()
            w2i.SetInput(renWin)
            writer = vtkPNGWriter()
            #writer.SetQuality(100)
            writer.SetInputData(w2i.GetOutput())
            filename = 'movie_'+'0'*(6-len(str(i)))+str(i)+".png"
            writer.SetFileName(os.path.join(path, filename))
            writer.Write()
            print os.path.join(path, filename)
            if i <> 720:
                ren.GetActiveCamera().Azimuth(2.0)

                # cam1.Azimuth(0.5)


iren.AddObserver("KeyPressEvent", Keypress)




iren.Initialize()
renWin.Render()
iren.Start()




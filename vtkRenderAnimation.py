#!/usr/bin/python


# ARGS  1 = surface filename
#       2 = beads filename


# imports
import sys              # for acessing the parameters
import os               # for interfacing with the operating system
from vtk import  *      # import vtkmethods
surface = None          # the filename of the surface
beads = None            # the filename of the beads


### code

# check the arguments


if len(sys.argv) != 2:
    print 'vtkVolVolViewer.py <stack>'
    sys.exit(0)

# set the arguments
yfp = sys.argv[1]



### VTK
#yfpImg = vtkSLCReader()
yfpImg = vtkTIFFReader()
yfpImg.SetFileName(yfp)

# Smooth the data a little bit
smImg = vtkImageGaussianSmooth()
smImg.SetDimensionality(3)
smImg.SetRadiusFactors([1.0,1.0,1.0])
smImg.SetInput(yfpImg.GetOutput())


# Create transfer mapping scalar value to opacity
opacityTransferFunction = vtkPiecewiseFunction()
opacityTransferFunction.AddPoint(0, 0.0)
opacityTransferFunction.AddPoint(149, 0.1)
opacityTransferFunction.AddPoint(150, 0.5)
opacityTransferFunction.AddPoint(256, 1.0)

# Create transfer mapping scalar value to color
colorTransferFunction = vtkColorTransferFunction()
colorTransferFunction.AddRGBPoint(50.0, 1.0, 0.0, 0.0)
#colorTransferFunction.AddRGBPoint(15.0, 1.0, 0.0, 0.0)
# colorTransferFunction.AddRGBPoint(128.0, 0.0, 0.0, 1.0)
# colorTransferFunction.AddRGBPoint(192.0, 0.0, 1.0, 0.0)
colorTransferFunction.AddRGBPoint(256.0, 1.0, 0.0, 0.0)

# The property describes how the data will look
volumeProperty = vtkVolumeProperty()
volumeProperty.SetColor(colorTransferFunction)
volumeProperty.SetScalarOpacity(opacityTransferFunction)
volumeProperty.ShadeOn(0)
volumeProperty.SetInterpolationTypeToLinear()
print volumeProperty.GetAmbient()
print volumeProperty.GetDiffuse()
print volumeProperty.GetSpecular()
print volumeProperty.GetSpecularPower()
# volumeProperty.SetSpecular(1.0)
# volumeProperty.SetSpecularPower(40.0)
# volumeProperty.SetInterpolationTypeToNearest()

# The mapper / ray cast function know how to render the data
# compositeFunction = vtkVolumeRayCastCompositeFunction()
compositeFunction = vtkVolumeRayCastCompositeFunction()
#compositeFunction = vtkVolumeRayCastMIPFunction()

volumeMapper = vtkVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction(compositeFunction)
volumeMapper.SetSampleDistance(1.0)
volumeMapper.SetInputConnection(yfpImg.GetOutputPort())


# The volume holds the mapper and the property and
# can be used to position/orient the volume
volume = vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volumeProperty)
volume.GetProperty().SetAmbient(0.5)
volume.GetProperty().SetDiffuse(0.7)
volume.GetProperty().SetSpecular(1.0)
volume.GetProperty().SetSpecularPower(20.0)

print volume.GetProperty().GetSpecular()




# Create transfer mapping scalar value to opacity
opacityTransferFunctionTrans2 = vtkPiecewiseFunction()
opacityTransferFunctionTrans2.AddPoint(0, 0.0)
opacityTransferFunctionTrans2.AddPoint(15, 0.005)
opacityTransferFunctionTrans2.AddPoint(256, 0.005)

# Create transfer mapping scalar value to color
colorTransferFunctionTrans2 = vtkColorTransferFunction()
colorTransferFunctionTrans2.AddRGBPoint(0.0, 0.0, 1.0, 0.0)
#colorTransferFunctionTrans.AddRGBPoint(15.0, 0.0, 1.0, 0.0)
# colorTransferFunction.AddRGBPoint(128.0, 0.0, 0.0, 1.0)
# colorTransferFunction.AddRGBPoint(192.0, 0.0, 1.0, 0.0)
colorTransferFunctionTrans2.AddRGBPoint(256.0, 0.0, 1.0, 0.0)

# The property describes how the data will look
volumePropertyTrans = vtkVolumeProperty()
volumePropertyTrans.SetColor(colorTransferFunctionTrans2)
volumePropertyTrans.SetScalarOpacity(opacityTransferFunctionTrans2)
volumePropertyTrans.ShadeOn()
volumePropertyTrans.SetInterpolationTypeToLinear()
# volumeProperty.SetInterpolationTypeToNearest()



ren1 = vtkRenderer()
ren1.AddVolume(volume)


renWin = vtkRenderWindow()
renWin.AddRenderer(ren1)

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)


ren1.SetBackground(0.0, 0.0, 0.0)
renWin.SetSize(320,260)

#Segmentation fault here
ren1.ResetCamera()


ren1.GetActiveCamera().Zoom(1.3)

def Keypress(obj, event):

    key = obj.GetKeySym()

    global renWin, ren1


    # make a movie by rotating the scence 360 degrees
    if key == "m":
        for i in range(0, 180,1):

            renWin.Render()
            w2i = vtkWindowToImageFilter()
            w2i.SetInput(renWin)
            writer = vtkJPEGWriter()
            writer.SetQuality(100)
            writer.SetInput(w2i.GetOutput())
            basename = 'movie_'+'0'*(6-len(str(i)))+str(i)
            writer.SetFileName(basename +'.jpg')
            writer.Write()

            if i <> 720:
                ren1.GetActiveCamera().Azimuth(2.0)

                # cam1.Azimuth(0.5)


iren.AddObserver("KeyPressEvent", Keypress)

renWin.Render()
iren.Initialize()
iren.Start()








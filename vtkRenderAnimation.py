#!/usr/bin/python

'''
This script was made using vtk 6.1
TODO:
Add option to hide the window when processing
'''

#from vtk import *
import sys
import os
import numpy as np
#from pylab import *
import subprocess as sub


class Animator:
    def __init__(self, tiff, out_dir):
        print "started"
        self.out_dir = out_dir
        print "reading in file"
        self.reader =  vtkTIFFReader()
        self.reader.SetFileName(tiff)
        self.reader.Update()
        self.vid_slice =0
        self.mip_projection()



    def mip_projection(self):
        # Color
        print "setting colour"
        colorTransferFunction = vtkColorTransferFunction()
        colorTransferFunction.AddHSVPoint(0, 0.0, 0.0, 0.0)
        colorTransferFunction.AddHSVPoint(55, 0.15, 0.32, 1)
        colorTransferFunction.AddHSVPoint(195, 0.082, 0.78, 1.0)

        opacityTransferFunction = vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(0.0, 0.0)
        opacityTransferFunction.AddPoint(25.0, 0.0)
        opacityTransferFunction.AddPoint(75.0, 0.19)
        opacityTransferFunction.AddPoint(105.0, 0.283)
        opacityTransferFunction.AddPoint(167.0, 0.55)

        volumeProperty = vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)

        #volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()


        self.isoFunction = vtkVolumeRayCastMIPFunction()
        #self.isoFunction.SetIsoValue(45.0)

        volumeMapper = vtkVolumeRayCastMapper()
        volumeMapper.SetVolumeRayCastFunction( self.isoFunction )
        volumeMapper.SetInputConnection(self.reader.GetOutputPort())

        volume = vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

        # Set a better camera position
        camera = vtkCamera()
        camera.SetViewUp(0, 0, 0)
        camera.SetPosition(-2, -2, -2)

        # Create the Renderer, Window and Interator
        self.ren = vtkRenderer()
        #ren.AddActor(outline)
        self.ren.AddVolume(volume)
        self.ren.SetBackground(0.0, 0.0, 0.0)
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

        self.ren.GetActiveCamera().Roll(130.0)
        self.renWin.Render()
        self.rotate()


    def ray_casting(self):

        colorTransferFunction = vtkColorTransferFunction()
        colorTransferFunction.AddHSVPoint(0.0, 0.0, 0.0, 0.0)
        colorTransferFunction.AddHSVPoint(54.0, 0.17, 0.7, 0.16)
        colorTransferFunction.AddHSVPoint(95.0, 0.18, 0.19, 1)
        colorTransferFunction.AddHSVPoint(112.0, 0.095, 0.8, 0.78)
        colorTransferFunction.AddHSVPoint(136.0, 0.0, 1, 0.93)

        self.opacityTransferFunction = vtkPiecewiseFunction()
        #Orgnas
        self.updateOpacity([ 0.0,  0.0,
                             20.0, 0.0,
                             62.6, 0.4,
                             150.0, 0.12,
                             159.0,0.924]
                           )




        rayCastFunction = vtkVolumeRayCastCompositeFunction()
        volumeMapper = vtkVolumeRayCastMapper()
        volumeMapper.SetInputConnection(self.reader.GetOutputPort())
        volumeMapper.SetVolumeRayCastFunction(rayCastFunction)

        volumeProperty = vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()


        #self.isoFunction = vtkVolumeRayCastIsosurfaceFunction()
        #self.isoFunction.SetIsoValue(45.0)



        volume = vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

        # Set a better camera position
        camera = vtkCamera()
        camera.SetViewUp(0, 0, 0)
        camera.SetPosition(-2, -2, -2)

        # Create the Renderer, Window and Interator
        self.ren = vtkRenderer()
        #ren.AddActor(outline)
        self.ren.AddVolume(volume)
        self.ren.SetBackground(0.0, 0.0, 0.0)
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
        #to initially orientate embryo. Not sure if this is needed for all
        self.ren.GetActiveCamera().Roll(130.0)
        self.renWin.Render()
        #iren.Start()

        self.rotate()
        #Orgnas
        self.updateOpacity([ 0.0,  0.0,
                             20.0, 0.0,
                             62.6, 0.043,
                             150.0, 0.12,
                             159.0,0.924]
                           )
        self.rotate()

    def updateOpacity(self, levelsOpacityList):
        l = levelsOpacityList
        for i in xrange(0, len(l)-1, 2):
            self.opacityTransferFunction.AddPoint(l[i], l[i+1])

    def Keypress(self, obj, event):

        key = obj.GetKeySym()
        # make a movie by rotating the scene 360 degrees
        if key == "x":
            self.rotate(obj, event)
        if key == "z":
            self.isovalues(obj, event)


    def rotate(self):
        print "rotate"
        for i in range(0, 360, 1):
            w2i = vtkWindowToImageFilter()
            w2i.Modified()
            w2i.SetInput(self.renWin)
            w2i.Update()

            writer = vtkPNGWriter()
            #writer.SetQuality(100)
            writer.SetInputData(w2i.GetOutput())#SetInput is deprecated???
            basename = 'movie_'+'0'*(6-len(str(i)))+str(self.vid_slice)+".png"
            self.vid_slice += 1
            filename = os.path.join(self.out_dir, basename)
            writer.SetFileName(filename)
            writer.Write()
            print filename
            if i <> 720:
                self.ren.GetActiveCamera().Azimuth(1.0)
                #self.ren.GetActiveCamera().Roll(2.0)
            self.renWin.Render()
        self.makeMovie()
        #sys.exit()


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
            #print os.path.join(path, filename)
            self.renWin.Render()


    def makeMovie(self):
        imagej_arg_string = self.out_dir + ':'+ os.path.join(self.out_dir,'test_isosurfce_animation.avi')
        #print imagej_arg_string
        sub.call(["imagej", "-b", "slices_to_avi.txt", imagej_arg_string ])

if __name__=="__main__":
    tiffVol = sys.argv[1]
    outputDir = sys.argv[2]
    animator = Animator(tiffVol, outputDir)





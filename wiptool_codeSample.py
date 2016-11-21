'''
THE ARTIST LOGBOOK 
YVO VON BERG 

info@yvovonberg.nl

Code samples / small part of the WIP tool / Artist logbook. 
Overview of the tool: https://goo.gl/GGPqdQ

Features:

+ Timer (So take a screenshot every x min/hour/day)
+ Choose viewports including cameras

not included in this sample:
+ Package to gif or mp4 (Using FFmpeg)
+ auto send to dropbox and give public url (using Dropbox API)


'''

# import api modules
import maya.OpenMaya as api
import maya.OpenMayaUI as apiUI
import pymel.mayautils as utils
import maya.utils as ut

import pymel.core as pm
import time, threading


class WIPmaker():
    def __init__(self):

        # current frame
        self.currentFrame = 0
        self.stopRender = False
        self.renderActive = False
        self.errorMsg = False

        self.allCams = pm.ls(cameras=1)

    def getEveryTimer(self):
        '''
        Function to get the timer info from the UI.
        Return: updateInterval: inputField after log every, minhoursec: dropdown min/hour/sec

        '''
        updateInterval = int(UI.logEvery_line.text())
        minhoursec = UI.minhour_dropdwn.currentIndex()

        return updateInterval, minhoursec

    def readInput(self):
        '''
        Get the input from the UI class and start the timer or screenshot/playblast commands

        '''

        # get Values from UI
        everyFrame, everyTime_dropdwn = self.getEveryTimer()
        stopStyle, stopFrames = self.getStopStyle()
        renderStyle = self.getRenderStyle()

        # check if the output directory is set and the camera is selected
        if self.checkSaveLocation() and UI.assignCam_dropdwn.currentText() != 'none':

            # check if we need to enable the timer. 
            # renderStyle == 1 is Log every x sec/min/hour
            if renderStyle == 1:

                # create new timer
                timerVal = threading.Timer(everyFrame, self.readInput)

                # check if: it is OK to start the timer or if we need to stop it and
                # if the number of frames in after x frames is more or equal than 3.
                if (stopStyle == 0 and (everyFrame >= 3) and (self.currentFrame >= stopFrames)) or not self.renderActive:
                    self.startTimer(False, timerVal)
                else:
                    self.startTimer(True, timerVal)

            if renderStyle == 0 or (renderStyle == 1 and self.renderActive):
                # execute the render command / playblast in the mainThread in Maya.
                ut.executeInMainThreadWithResult(self.renderScreen)

            if not self.renderActive or renderStyle == 0:
                self.autoPackFrames(UI.exportPack_dropdwn.currentText(), UI.exportFps_edit.text())


    def checkCamera(self):
        '''
        Function to check if the current camera exist in the scene.

        '''

        # get camera from dropdown
        currentCamera = UI.assignCam_dropdwn.currentText()
        if currentCamera == 'none':
            api.MGlobal.displayWarning('No camera selected!')
            UI.assignCam_dropdwn.setStyleSheet('background-color: red')
            return False

        self.allCams = pm.ls(cameras=1)
        foundCamera = False

        for i in self.allCams:

            if re.search(currentCamera, str(i).replace('Shape','')):
                foundCamera = i
                
        if foundCamera:
            return foundCamera
        else:
            # camera is missing/deleted, going back to default perspective camera
            api.MGlobal.displayWarning(str(currentCamera) + ' is missing/deleted, switching to perspective')
            return 'persp'

    def getViewport(self):
        '''
        Function to get the current maya viewport.
        Return: viewport modelPanel
        
        '''

        # get the current viewport
        pan = pm.getPanel(withFocus=True)
        if not re.search('modelPanel', pan):
            pan = 'modelPanel4'

        return pm.windows.modelPanel(pan, query=True, camera=True)

    def getScreenRes(self):
        '''
        Function to check the user resolution. Make sure it is not > 6000 to prevent a crash.
        Return: resolution from UI.

        '''

        xScreen = int(UI.res_lineX.text())
        yScreen = int(UI.res_lineY.text())

        if xScreen > 6000 or yScreen > 6000:
            api.MGlobal.displayWarning('Output resolution is too high. < 6000 pixels')
            UI.res_lineX.setStyleSheet('background-color: red')
            return False
        else:
            UI.res_lineX.setStyleSheet('background-color: none')
            return xScreen, yScreen

    def renderScreen(self):
        '''
        Render function to make the screenshot. Playblast a single frame.
        '''

        # return camera / viewport
        currentCamera = self.checkCamera()
        originalCam = self.getViewport()
        resScreen = self.getScreenRes()

        if resScreen:

            # temp disable undo 
            pm.undoInfo( openChunk=True, stateWithoutFlush=False )

            # switch current view to camera
            pm.lookThru(currentCamera)

            # file path info from UI inputs
            completeFile = UI.saveLocation + self.getFileNameStyle(includeFormat=True)

            # playblast without scale settings, to prevent visual glitches
            pm.playblast( frame=pm.currentTime(), widthHeight=(resScreen[0],resScreen[1]), offScreen=True, clearCache=True, fp=4, p=100, fo=True, cf=completeFile, format="image", viewer=False, c=str(UI.fileExt_dropdwn.currentText()))
            
            # reset camera back to original viewport
            pm.lookThru(originalCam)

            pm.undoInfo( openChunk=False,closeChunk=True, stateWithoutFlush=True )

            # log info to the user
            if not self.errorMsg:
                api.MGlobal.displayInfo('[#] Log successful  ' + str(datetime.datetime.now().time()))


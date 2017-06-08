import sys
import os.path
from packages.libvlc import vlc
from PyQt4 import QtCore, QtGui
from math import floor
from main_design import Ui_MainWindow


class VlcPlayer(QtGui.QMainWindow):
    resized = QtCore.pyqtSignal()

    def  __init__(self, parent=None):
        super(VlcPlayer, self).__init__(parent=parent)
        self.window = Ui_MainWindow()
        self.window.setupUi(self)
        self.resized.connect(self.windowResized)
         # creating a basic vlc instance
        self.vlcInstance = vlc.Instance()
        # creating an empty vlc media player
        self.mediaPlayer = self.vlcInstance.media_player_new()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.isPaused = False
        self.isFullscreen = False
        self.connectControllers()
        self.setUI();

    def resizeEvent(self, event):
        self.resized.emit()
        return super(VlcPlayer, self).resizeEvent(event)

    def windowResized(self):

        
            cvHeight = 130
            mvMinHeight = 200
            self.window.mediaView.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()-25-cvHeight))
            self.window.controlView.setGeometry(QtCore.QRect(0,self.window.mediaView.height(), self.width(), cvHeight))
            

    def connectControllers(self):
        self.connect(self.window.actionOpen_File, QtCore.SIGNAL("triggered()"), self.OpenFile)
        self.connect(self.window.actionExit, QtCore.SIGNAL("triggered()"), sys.exit)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"),self.updateUI)
        self.connect(self.window.seekBar,QtCore.SIGNAL("sliderMoved(int)"),self.setSeekPosition)
        self.connect(self.window.playState, QtCore.SIGNAL("clicked()"),self.setPlayPause)
        self.connect(self.window.fullscreenButton, QtCore.SIGNAL("clicked()"),self.toggleFullscreen)
        self.connect(self.window.volumeBar,QtCore.SIGNAL("valueChanged(int)"),self.setVolume)
        
    def toggleFullscreen(self):
        self.window.centralwidget.showFullScreen()

    def setUI(self):
        
        self.window.mediaView.setStyleSheet('background-color:blue;border-radius:1px;')
        self.window.playState.setIcon(QtGui.QIcon('icons/svg/play-2.svg'))
        self.window.playState.setIconSize(QtCore.QSize(65,65))
        self.window.playState.setStyleSheet ('background-color:transparent;')
        
        self.window.previous.setIcon(QtGui.QIcon('icons/svg/backward-3.svg'))
        self.window.previous.setIconSize(QtCore.QSize(50,50))
        self.window.previous.setStyleSheet ('background-color:transparent;')

        self.window.next.setIcon(QtGui.QIcon('icons/svg/forward-2.svg'))
        self.window.next.setIconSize(QtCore.QSize(50,50))
        self.window.next.setStyleSheet ('background-color:transparent;')

       
        self.window.seekBar.setMaximum(1000)
        self.window.volumeBar.setMaximum(100)
        self.window.volumeBar.setValue(self.mediaPlayer.audio_get_volume())
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.mediaPlayer.set_xwindow(self.window.mediaView.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaPlayer.set_hwnd(self.window.mediaView.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaPlayer.set_nsobject(self.window.mediaView.winId())
            
    def setSeekPosition(self, position):
        self.mediaPlayer.set_position(position / 1000.0)

    def setPlayPause(self):
        if self.mediaPlayer.is_playing():
            self.mediaPlayer.pause()
            self.window.playState.setIcon(QtGui.QIcon('icons/svg/play.svg'))
            self.isPaused = True
        else:
            if self.mediaPlayer.play() == -1:
                self.OpenFile()
                return
            self.mediaPlayer.play()
            self.window.playState.setIcon(QtGui.QIcon('icons/svg/pause.svg'))
            self.timer.start()
            self.isPaused = False

    def setVolume(self, volume):
        self.mediaPlayer.audio_set_volume(volume)

    def OpenFile(self,filename = None):
        if filename is None:
            filename = QtGui.QFileDialog.getOpenFileName(self, "Open File", os.path.expanduser('~'))
        if not filename:
            return
            
        # create the media
        if sys.version < '3':
            filename = unicode(filename)
        self.media = self.vlcInstance.media_new(filename)
        # put the media in the media player
        self.mediaPlayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))
       
        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        # you have to give the id of the QFrame (or similar object) to
        # vlc, different platforms have different functions for this
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.mediaPlayer.set_xwindow(self.window.mediaView.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaPlayer.set_hwnd(self.window.mediaView.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaPlayer.set_nsobject(self.window.mediaView.winId())
        self.setPlayPause()
        self.mediaPlayer.stop()
        self.mediaPlayer.play()

        self.window.timeLeft.setText(self.stringTimeFormat(self.media.get_duration()))
        
    def stringTimeFormat(self,time) :
        strng = "00:00:00"
        
        if time<0 :
            return strng
        
        hr = floor((time/3600)/1000)
        mnt = floor((time - hr*1000*3600)/60000)
        sec = floor((time - hr*3600*1000 - mnt*60*1000)/1000)
        
        strHr = str(hr)
        strMnt = str(mnt)
        strSec = str(sec)
        
        if hr<10 :
            strHr = "0" + strHr
        if mnt<10 :
            strMnt = "0" + strMnt
        if sec<10 :
            strSec = "0" + strSec

        strng = strHr + ":" + strMnt + ":" + strSec 
        return strng

    def updateUI(self):
        # setting the slider to the desired position
        self.window.seekBar.setValue(self.mediaPlayer.get_position() * 1000)

        if not self.mediaPlayer.is_playing():
            # no need to call this function if nothing is played
            self.timer.stop()
            if not self.isPaused:
                # after the video finished, the play button stills shows
                # "Pause", not the desired behavior of a media player
                # this will fix it
                self.mediaPlayer.stop()
                self.window.playState.setIcon(QtGui.QIcon('icons/svg/play.svg'))
       
        self.window.timeDone.setText(self.stringTimeFormat(int(self.media.get_duration() * self.mediaPlayer.get_position())))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    w = VlcPlayer()
    w.show()
    sys.exit(app.exec_())


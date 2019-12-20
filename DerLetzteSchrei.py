from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time


import math
import cv2
import socket
import os
medianX=0
medianY=0
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
medianLength = 25
pastxValues=[0]*medianLength
pastyValues=[0]*medianLength
currentMode=0
currentVolume=0.5
currentMinFrequency=400
currentMaxFrequency=800
currentDiySound1=17
currentDiySound2=33
currentDiySound3=17
currentDiySound4=33

def dark_palette():

    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(240, 120, 240))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(100, 0, 100))
    dark_palette.setColor(QPalette.AlternateBase, QColor(100, 0, 100))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(100, 0, 100))##dreh und dropdown
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(255, 0, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette) 

def calculateMedian(value, pastValues):
    for i in range(0,len(pastValues)-1,1):
        pastValues[len(pastValues)-1-i]=pastValues[len(pastValues)-2-i]
    pastValues[0]=value
    summe=0
    for i in range(1, len(pastValues),1):
        summe=summe+pastValues[i]
    summe=summe/len(pastValues)
    median=0.7*value+0.2*summe+0.05*pastValues[1]+0.05*pastValues[2]
    return [median, pastValues]

def send_Frequenz_and_Volume_to_pure_Data(x,y,modus):
    global currentMinFrequency
    global currentMaxFrequency
    global currentVolume
    global currentDiySound1
    global currentDiySound2
    global currentDiySound3
    global currentDiySound4
 
    s = socket.socket()
    host = socket.gethostname()
    port = 3000
    s.connect((host, port))
    maxVolume = 100
    width=640
    height=480 #einstellbar!!!!!!!
    frequency = ((x/width)*(currentMaxFrequency-currentMinFrequency)+currentMinFrequency)
    ynew= -1*((y/height)*100)+100
    volume=(10**math.log2(((ynew))/25))*100
    #volume = 100-(-1/187500*((y/height)*maxVolume)**3 + 27/2500*((y/height)*maxVolume)**2 - 2/75*((y/height)*maxVolume))
    #volume = 100 - (47/2275000000*((y/height)*maxVolume)**5 - 1507/1137500000*((y/height)*maxVolume)**4 - 5671/39000000*((y/height)*maxVolume)**3 + 33233/1820000*((y/height)*maxVolume)**2 - 6169/54600*((y/height)*maxVolume))
    #volume=100-(10 ** (((y/height)*maxVolume)/50))-2
    volume=volume*currentVolume
    volume= int(volume)
    if volume>10000:
        volume = 10000
    if volume<0:
        volume = 0


    
    diySoundGesamt = currentDiySound1+currentDiySound2+currentDiySound3+currentDiySound4
    DiySound1 = 100*currentDiySound1 / diySoundGesamt
    DiySound2 = 100*currentDiySound2 / diySoundGesamt
    DiySound3 = 100*currentDiySound3 / diySoundGesamt
    DiySound4 = 100*currentDiySound4 / diySoundGesamt
    
    message = "0 " + str(frequency) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))
    message = "1 " + str(volume) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))
    message = "2 " + str(modus) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))
    message = "3 " + str(DiySound1) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))
    message = "4 " + str(DiySound2) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))
    message = "5 " + str(DiySound3) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))
    message = "6 " + str(DiySound4) + " ;" #Need to add " ;" at the end so pd knows when you're finished writing.
    s.send(message.encode('utf-8'))

class WorkerSignals(QObject):
    x = pyqtSignal(int, int)
    y = pyqtSignal(int)
class Worker(QRunnable):
    '''
    Worker thread
    '''
    def __init__(self):
        super(Worker, self).__init__()
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        global pastxValues
        global pastyValues
        global medianX
        global medianY
        global currentMode
        global currentVolume
        
        '''
        Your code goes in this function
        '''
        print("Thread start") 
        cap = cv2.VideoCapture(0)
        while True:
           
            
            ret, frame = cap.read()
            if ret == False: ## checkt is ein videobild da
                break
            #Frame in Graustufen wandeln
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  
            # height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            # print(width, height)
            
            faces = face_cascade.detectMultiScale(gray, 1.3, 5) 
            for (x,y,w,h) in faces:
                cx=int(x)+int(w/2)
                X_list = calculateMedian(cx, pastxValues)
                y_List = calculateMedian(y,pastyValues)
                pastxValues = X_list[1]
                pastyValues = y_List[1]
                medianX = X_list[0]
                medianY = y_List[0]
                self.signals.x.emit(medianX,medianY)
                
                
                
                try:
                    send_Frequenz_and_Volume_to_pure_Data(medianX+200,medianY,currentMode)
                except ConnectionRefusedError:
                    print("nur für ein gesicht gedacht warte eine sekunde")##muss auch ins overlay
                    os.startfile("Zound_extended.pd") 
        print("Thread complete")   

class Example(QWidget):
    
    def __init__(self):
        
        
        super().__init__()
        
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
        
        
        app.setStyle('Fusion')
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
        self.button()
        
        
        self.Genral()
        self.Drehknopf()
        self.Dropdown()
        self.Frequenzbereich()
        self.Slider()
        self.symbols()
        self.PositionLabel()
        self.Logo()
        self.show()
        

        
    
        

    def oh_no(self):
        worker = Worker()
        worker.signals.x.connect(self.Frequenz_Volume)
        self.threadpool.start(worker) 

    def PositionLabel(self):
        self.XLabel = QLabel("position", self)
        pixmap = QPixmap('saebelzahn_kopf.png')
        self.XLabel.setPixmap(pixmap)
        self.XLabel.move(925,405 )
        self.XLabel.show()

    def Logo(self):
        LogoLabel = QLabel("Logo", self)
        pixmap = QPixmap('Logo_transparent.PNG')
        LogoLabel.setPixmap(pixmap)
        LogoLabel.move(610,7)
         
    def Frequenz_Volume(self, x, y):
        x=5/4*x+560
        y=5/4*y+110
        
        self.XLabel.move(x,y)

    def paintEvent (self, event):
    
        painter=QPainter(self)
        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.SolidPattern)) 

        painter.drawRect(560, 110, 800,600)

    def Genral(self):
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowTitle('Puzzelkiste')
    
    def button(self):
        button = QPushButton("GO!", self)  
        button.pressed.connect(self.oh_no)
        button.setGeometry(890,890,140,70)
        newfont = QFont("Times", 40, QFont.Bold) 
        button.setFont(newfont)
  
    def Dropdown(self):      

        self.lbl = QLabel("Modus", self)

        combo = QComboBox(self)
        combo.addItem("Sinus")
        combo.addItem("Depech Mode")
        combo.addItem("DIY")
        combo.addItem("Schrei")
        newfont = QFont("Times", 30, QFont.Bold) 
        combo.setFont(newfont)

        combo.setGeometry(85,190,250,80)
        self.lbl.move(110, 110)
        newfont2 = QFont("Times", 40, QFont.Bold) 
        self.lbl.setFont(newfont2)

        combo.activated[str].connect(self.onActivatedCombo)  

    def onActivatedCombo(self, text):
        global currentMode
        #self.lbl.setText(text)
        #self.lbl.adjustSize() 
        modedict={
            "Sinus": 0,
            "Depech Mode": 1,
            "DIY": 2,
            "Schrei" : 3,

        }
        currentMode=modedict[text] 
           #entweder returenen oder global variable oder noch ne funktion die die variablen ändert
        
    def Drehknopf(self):
        labeldial = QLabel("Volume", self)

        dial = QDial(self)
        dial.setValue(50)
        dial.setGeometry(1540,160,350,350)

        labeldial.move(1600, 110)
        newfont2 = QFont("Times", 40, QFont.Bold) 
        labeldial.setFont(newfont2)

        dial.valueChanged[int].connect(self.onActivatedDial) #he dial also emits sliderPressed() and sliderReleased() signals when the mouse button is pressed and released. Note that the dial’s value can change without these signals being emitted since the keyboard and wheel can also be used to change the value

    def onActivatedDial(self, number):
        global currentVolume
        currentVolume=number/100

    def Frequenzbereich(self):
        labelfrequenz = QLabel("Frequenzbereich", self)

        newfont = QFont("Times", 25, QFont.Bold) 
        spinBox1 = QSpinBox(self)
        spinBox1.setRange(100, 5000)
        spinBox1.setSingleStep(100)
        spinBox1.setGeometry(1540,580,120,75)
        spinBox1.setValue(400)
        spinBox1.setFont(newfont)

        spinBox2 = QSpinBox(self)
        spinBox2.setRange(100, 5000)
        spinBox2.setSingleStep(100)
        spinBox2.setGeometry(1740,580,120,75)
        spinBox2.setValue(800)
        spinBox2.setFont(newfont)

        labelfrequenz.move(1510, 500)
        newfont2 = QFont("Times", 35, QFont.Bold) 
        labelfrequenz.setFont(newfont2)

        spinBox1.valueChanged[int].connect(self.onActivatedSpinBox1)
        spinBox2.valueChanged[int].connect(self.onActivatedSpinBox2)
    
    def onActivatedSpinBox1(self, nummer):
        global currentMinFrequency
        currentMinFrequency=nummer
   
    def onActivatedSpinBox2(self, nummer):
        global currentMaxFrequency
        currentMaxFrequency=nummer

    def Slider(self):
        labelslider = QLabel("make your own sound", self)

        slider = QSlider(Qt.Horizontal, self)
        slider.setValue(40)
        slider.setGeometry(75,375,390,30)

        slider2 = QSlider(Qt.Horizontal, self)
        slider2.setValue(50)
        slider2.setGeometry(75,445,390,30)

        slider3 = QSlider(Qt.Horizontal, self)
        slider3.setValue(60)
        slider3.setGeometry(75,515,390,30)

        slider4 = QSlider(Qt.Horizontal, self)
        slider4.setValue(60)
        slider4.setGeometry(75,585,390,30)

        labelslider.move(15, 300)
        newfont2 = QFont("Times", 30, QFont.Bold) 
        labelslider.setFont(newfont2)

        slider.valueChanged[int].connect(self.onActivatedSlider1)
        slider2.valueChanged[int].connect(self.onActivatedSlider2)
        slider3.valueChanged[int].connect(self.onActivatedSlider3)
        slider4.valueChanged[int].connect(self.onActivatedSlider4)

    def onActivatedSlider1(self, nummer):
        global currentDiySound1
        currentDiySound1=nummer
    def onActivatedSlider2(self, nummer):
        global currentDiySound2
        currentDiySound2=nummer
    def onActivatedSlider3(self, nummer):
        global currentDiySound3
        currentDiySound3=nummer
    def onActivatedSlider4(self, nummer):
        global currentDiySound4
        currentDiySound4=nummer
    
    def symbols(self):
        label = QLabel(self)
        pixmap = QPixmap('sinus.png')
        label.setPixmap(pixmap)
        label.move(15, 360)#
        
        label2 = QLabel(self)
        pixmap2 = QPixmap('sägezahn.png')
        label2.setPixmap(pixmap2)
        label2.move(15, 430)
       
        label3 = QLabel(self)
        pixmap3 = QPixmap('dreieck.png')
        label3.setPixmap(pixmap3)
        label3.move(15, 500)
        
        label4 = QLabel(self)
        pixmap4 = QPixmap('rechteck.png')
        label4.setPixmap(pixmap4)
        label4.move(15, 570)
        
        slabel = QLabel(self)
        spixmap = QPixmap('saebelzahn.png')
        slabel.setPixmap(spixmap)
        slabel.move(15, 900)
        
        slabel2 = QLabel(self)
        spixmap2 = QPixmap('saebelzahn2.png')
        slabel2.setPixmap(spixmap2)
        slabel2.move(1755, 900)
    
                
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    dark_palette()
    ex = Example()
    sys.exit(app.exec_())
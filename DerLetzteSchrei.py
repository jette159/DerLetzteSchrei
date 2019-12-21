from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time
import math
import cv2
import socket
import os

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

#Variablen die zur Berechnung der Mittelwerte der Gesichtsposition genutzt werden
medianX=0
medianY=0
medianLength = 25
pastxValues=[0]*medianLength
pastyValues=[0]*medianLength

#Varibalen, welche die im Layout gesetzten Werte speichern um sie zu übergeben zwischen verschiedenen Funktionen
currentMode=0
currentVolume=0.5
currentMinFrequency=400
currentMaxFrequency=800
currentDiySound1=17
currentDiySound2=33
currentDiySound3=17
currentDiySound4=33


# Definiert die Farbpalette, welche im Layout genutzt wird. In unserem Fall sehr pinklastig.
def pink_palette():              
    
    pink_palette = QPalette()
    pink_palette.setColor(QPalette.Window, QColor(240, 120, 240))
    pink_palette.setColor(QPalette.WindowText, Qt.white)
    pink_palette.setColor(QPalette.Base, QColor(100, 0, 100))
    pink_palette.setColor(QPalette.AlternateBase, QColor(100, 0, 100))
    pink_palette.setColor(QPalette.ToolTipBase, Qt.white)
    pink_palette.setColor(QPalette.ToolTipText, Qt.white)
    pink_palette.setColor(QPalette.Text, Qt.white)
    pink_palette.setColor(QPalette.Button, QColor(100, 0, 100))
    pink_palette.setColor(QPalette.ButtonText, Qt.white)
    pink_palette.setColor(QPalette.BrightText, Qt.red)
    pink_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    pink_palette.setColor(QPalette.Highlight, QColor(255, 0, 218))
    pink_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(pink_palette) 

#Berechnung des Medians um die Bewegung flüssiger zu machen, hierbei werden die vorherigen Werte in unterschiedlcihen Gewichtungen berücksichtigt
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

#Funktion welche die Werte aus dem Reglern im Layout und aus der Videoverarbeitung an Pure Data weitergibt
def send_Frequenz_and_Volume_to_pure_Data(x,y,modus):
    global currentMinFrequency
    global currentMaxFrequency
    global currentVolume
    global currentDiySound1
    global currentDiySound2
    global currentDiySound3
    global currentDiySound4

    maxVolume = 100
    width_frame=640
    height_frame=480
 
    #Berechnung der zusendenden Werte
    frequency = ((x/width_frame)*(currentMaxFrequency-currentMinFrequency)+currentMinFrequency) # skaliert Framebreite und Frequenzbereich 
    ynew= -1*((y/height_frame)*100)+100 #skaliert Framehöhe mit Volumewerten 0-100 (linear)
    volume=(10**math.log2(((ynew))/25))*100 # Skaliert Volume logarithmisch sodas sich die Erhöhung linear anhört
    
    volume=volume*currentVolume # Volume aus der Videoverarbeitung wird mit dem am Regler eingestelten Wert verbunden
    volume= int(volume) # Wandlung, da Pure Data kein Fan von float Zahlen ist

    #um übersteuerung zu verhindern
    if volume>10000:
        volume = 10000
    if volume<0:
        volume = 0


    #Berechnung der Zusammensetzung des DIY-Sounds aus den Reglerwerten
    diySoundGesamt = currentDiySound1+currentDiySound2+currentDiySound3+currentDiySound4
    DiySound1 = 100*currentDiySound1 / diySoundGesamt
    DiySound2 = 100*currentDiySound2 / diySoundGesamt
    DiySound3 = 100*currentDiySound3 / diySoundGesamt
    DiySound4 = 100*currentDiySound4 / diySoundGesamt
    
    #öffnen des Ports
    s = socket.socket()
    host = socket.gethostname()
    port = 3000
    s.connect((host, port))

    #Der eigentliche Teil in dem die Werte geschickt werden
    message = "0 " + str(frequency) + " ;" 
    s.send(message.encode('utf-8'))
    message = "1 " + str(volume) + " ;" 
    s.send(message.encode('utf-8'))
    message = "2 " + str(modus) + " ;" 
    s.send(message.encode('utf-8'))
    message = "3 " + str(DiySound1) + " ;" 
    s.send(message.encode('utf-8'))
    message = "4 " + str(DiySound2) + " ;"
    s.send(message.encode('utf-8'))
    message = "5 " + str(DiySound3) + " ;" 
    s.send(message.encode('utf-8'))
    message = "6 " + str(DiySound4) + " ;" 
    s.send(message.encode('utf-8'))

#diese klasse beinhaltet die signale die wir aus dem einen thread in den anderen schicken wollen
class WorkerSignals(QObject):
    x = pyqtSignal(int, int)
    y = pyqtSignal(int)

#diese klasse beinhaltet den thread der neben der klasse gui laiufen soll
class Worker(QRunnable):
    
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
        
        #here starts what the thread is supposed to do

        cap = cv2.VideoCapture(0)
        while True:
           
            
            ret, frame = cap.read()
            if ret == False: ## checkt is ein videobild da
                break
           
            #Frame in Graustufen wandeln
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        
            faces = face_cascade.detectMultiScale(gray, 1.3, 5) 

            #Gesichter werden erkannt und Werte in Liste geschrieben
            for (x,y,w,h) in faces:
                cx=int(x)+int(w/2)
                X_list = calculateMedian(cx, pastxValues)
                y_List = calculateMedian(y,pastyValues)
                pastxValues = X_list[1]
                pastyValues = y_List[1]
                medianX = X_list[0]
                medianY = y_List[0]
                self.signals.x.emit(medianX,medianY)
                
                
                #um zu verhindern, das Pure Data sich shcließt, wird es einfahc wieder neu geöffnet
                try:
                    send_Frequenz_and_Volume_to_pure_Data(medianX+200,medianY,currentMode)
                except ConnectionRefusedError:
                    os.startfile("Zound_extended.pd") 
        print("Thread complete")   

#GUI
class GUI(QWidget):
    
    #Initialisierung des gesamten Widget
    def __init__(self):
        
        super().__init__()
        
        self.threadpool = QThreadPool() #initialiesieren von den threads

        #setzt das Grundsätzliche Fensterdesign    
        app.setStyle('Fusion') 
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

        #initalisiert die einzelnen Layoutelemente
        self.Genral()  
        self.button_go()
        self.Dial_Volume()
        self.Select_Modus()
        self.Select_Frequency()
        self.DIYSound_Components()
        self.Icons_DIYSound()
        self.Cursor()
        self.Logo()
        self.show()
 
    # ruft thread auf und ruft cursor movement mit den gesendet signalen von dem thread auf
    def start_thread(self):
        worker = Worker()
        worker.signals.x.connect(self.Cursor_Movement)
        self.threadpool.start(worker) 

    #setzt die Größe des Programmfenster und den Titel
    def Genral(self):
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowTitle('Der letzte Schrei')

    #setzt den Cursor, welcher die Bewegung des Kopfes wiedergibt
    def Cursor(self):
        self.XLabel = QLabel("position", self)
        pixmap = QPixmap('saebelzahn_kopf.png')
        self.XLabel.setPixmap(pixmap)
        self.XLabel.move(925,405 )
        self.XLabel.show()

    #setzt die Logografik oben in der Mitte und der beiden Säbelzahntiger unten links und rechts
    def Logo(self):
        LogoLabel = QLabel("Logo", self)
        pixmap = QPixmap('Logo_transparent.PNG')
        LogoLabel.setPixmap(pixmap)
        LogoLabel.move(610,7)

        slabel = QLabel(self)
        spixmap = QPixmap('saebelzahn.png')
        slabel.setPixmap(spixmap)
        slabel.move(15, 900)
        
        slabel2 = QLabel(self)
        spixmap2 = QPixmap('saebelzahn2.png')
        slabel2.setPixmap(spixmap2)
        slabel2.move(1755, 900)

    #bewegt den Sebelzahntigerkopf     
    def Cursor_Movement(self, x, y):
        x=5/4*x+560
        y=5/4*y+110
        
        self.XLabel.move(x,y)

    #initialisiert das Grüne Rechteck in der Mitte
    def paintEvent (self, event):
    
        painter=QPainter(self)
        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.SolidPattern)) 

        painter.drawRect(560, 110, 800,600)

    #setzt den Knopf, der die Threads startet
    def button_go(self):
        button = QPushButton("GO!", self)  
        button.pressed.connect(self.start_thread)
        button.setGeometry(890,890,140,70)
        newfont = QFont("Times", 40, QFont.Bold) 
        button.setFont(newfont)
    
    #Setzt das Modusauswahlfenster und die dazu gehörende Überschrift und verbindet es, sodass bei Veränderung diese weiter gegeben wird     
    def Select_Modus(self):      

        combo = QComboBox(self)
        combo.addItem("Sinus")
        combo.addItem("Depech Mode")
        combo.addItem("DIY")
        combo.addItem("Schrei")
        newfont = QFont("Times", 30, QFont.Bold) 
        combo.setFont(newfont)
        combo.setGeometry(85,190,250,80)

        self.lbl = QLabel("Modus", self)
        self.lbl.move(110, 110)
        newfont2 = QFont("Times", 40, QFont.Bold) 
        self.lbl.setFont(newfont2)

        combo.activated[str].connect(self.onActivatedCombo) 

    #Schreibt die Veränderung der Modusänderung in die Variabel bei Änderung so gewandelt, das sie weiterverwendet werden kann
    def onActivatedCombo(self, text):
        global currentMode
        modedict={
            "Sinus": 0,
            "Depech Mode": 1,
            "DIY": 2,
            "Schrei" : 3,
        }
        
        currentMode=modedict[text] 
          
    #setzt das Volumerad und das dazugehörende Label und verbindet es, sodass bei Veränderung diese weiter gegeben wird     
    def Dial_Volume(self):
        
        dial = QDial(self)
        dial.setValue(50)
        dial.setGeometry(1540,160,350,350)

        labeldial = QLabel("Volume", self)
        labeldial.move(1600, 110)
        newfont2 = QFont("Times", 40, QFont.Bold) 
        labeldial.setFont(newfont2)

        dial.valueChanged[int].connect(self.onActivatedDial) 

    #Schreibt die Veränderung des Volumerads in die Variabel bei Änderung so gewandelt, das sie weiterverwendet werden kann
    def onActivatedDial(self, number):
        global currentVolume
        currentVolume=number/100

    #setzt die beiden Felder, mit welchen der Frequenzbereich ausgewählt werden kann, und das dazugehörende Label 
    #und verbindet sie, sodass bei Veränderung diese weiter gegeben werden  
    def Select_Frequency(self):
        labelfrequenz = QLabel("Frequenzbereich", self)
        labelfrequenz.move(1510, 500)
        newfont2 = QFont("Times", 35, QFont.Bold) 
        labelfrequenz.setFont(newfont2)

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

        spinBox1.valueChanged[int].connect(self.onActivatedSpinBox1)
        spinBox2.valueChanged[int].connect(self.onActivatedSpinBox2)
    
    #Schreibt die Veränderung der unteren Frequenzgrenze in die Variabel bei Änderung 
    def onActivatedSpinBox1(self, nummer):
        global currentMinFrequency
        currentMinFrequency=nummer
   
    #Schreibt die Veränderung der oberen Frequenzgrenze in die Variabel bei Änderung 
    def onActivatedSpinBox2(self, nummer):
        global currentMaxFrequency
        currentMaxFrequency=nummer

    #setzt die vier Schieber, mit welchen die Gewichtung der Soundkomponenten ausgewählt werden kann
    #und verbindet sie, sodass bei Veränderung diese weiter gegeben werden 
    def DIYSound_Components(self):
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

    #Die Verbindung der vier Schieber für Veränderungen
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
    
    #Positionierung der vier Icons vor den DIYSound-Reglern 
    def Icons_DIYSound(self):
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
    
#start der gesamten Anwendung                
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    pink_palette()
    ex = GUI()
    sys.exit(app.exec_())
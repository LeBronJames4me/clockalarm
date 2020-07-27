import sys

from PyQt5.QtCore import QTime
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Timer
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from player import *
import csv
import os.path


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)


class CWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.player = CPlayer(self)
        self.playlist = []
        self.selectedList = [0]
        self.playOption = QMediaPlaylist.CurrentItemOnce



        self.hour = QLCDNumber(self)
        self.hour.display('')
        self.hour.setDigitCount(8)

        ## LCD 글자색 변경
        #pal = QPalette()
        #pal.setColor(QPalette.WindowText, QColor(155,0,0))
        #self.hour.setPalette(pal)

        ## LCD 배경색 변경
        self.hour.setMaximumWidth(200)
        pal = QPalette()
        pal.setColor(QPalette.Background, QColor(60,90,185))
        self.hour.setPalette(pal)
        self.hour.setAutoFillBackground(True)



        self.setWindowTitle('Rhyme Sound')
        self.setWindowIcon(QIcon('ci.png'))
        self.setGeometry(200,170,900,600)
        self.initUI()

    def initUI(self):

        vbox = QVBoxLayout()

        # 1.Play List####################################################
        box = QVBoxLayout()
        gb = QGroupBox('Play List')
        vbox.addWidget(gb)

        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderItem(0, QTableWidgetItem('SoundTrack'))
        self.table.setHorizontalHeaderItem(1, QTableWidgetItem('Time(24h)'))
        self.table.setHorizontalHeaderItem(2,QTableWidgetItem('Progress'))
        # read only
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # single row selection
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # signal
        self.table.itemSelectionChanged.connect(self.tableChanged)
        self.table.itemDoubleClicked.connect(self.tableDbClicked)
        box.addWidget(self.table)

        hbox = QHBoxLayout()
        btnAdd = QPushButton('Add List')
        btnDel = QPushButton('Del List')
        btnLoad = QPushButton('Load Setting')
        btnAdd.clicked.connect(self.addList)
        btnDel.clicked.connect(self.delList)
        btnLoad.clicked.connect(self.loadList)
        hbox.addWidget(btnAdd)
        hbox.addWidget(btnDel)
        hbox.addWidget(btnLoad)


        box.addLayout(hbox)
        gb.setLayout(box)

        # 2.Play Control##########################################
        box = QHBoxLayout()
        gb = QGroupBox('Play Control')
        vbox.addWidget(gb)

        text = ['▶', '⏸', 'reset']
        grp = QButtonGroup(self)
        for i in range(len(text)):
            btn = QPushButton(text[i], self)
            btn.setMaximumWidth(100)
            grp.addButton(btn, i)
            box.addWidget(btn)
        grp.buttonClicked[int].connect(self.btnClicked)

        self.settimer = QTimeEdit()
        self.settimer.setAlignment(Qt.AlignCenter)
        box.addWidget(self.settimer)

        # Volume
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setMaximumWidth(200)
        self.slider.valueChanged[int].connect(self.volumeChanged)
        box.addWidget(self.slider)
        gb.setLayout(box)

        # 3.Play Option##########################################
        box = QHBoxLayout()
        gb = QGroupBox('Play Option')
        vbox.addWidget(gb)

        str = ['현재 한곡 만', '한곡 반복 재생', '순차 재생', '전체 반복', '랜덤 재생']
        grp = QButtonGroup(self)
        for i in range(len(str)):
            btn = QRadioButton(str[i], self)
            if i == QMediaPlaylist.CurrentItemOnce:
                btn.setChecked(True)
            grp.addButton(btn, i)
            box.addWidget(btn)

        grp.buttonClicked[int].connect(self.radClicked)

        gb.setLayout(box)

        #4. 시간 표시############################################
        box = QHBoxLayout()
        gb = QGroupBox('현재 시각')
        vbox.addWidget(gb)

        box.addWidget(self.hour)

        self.showtime()
        gb.setLayout(box)

        self.setLayout(vbox)
        self.show()

    def tableChanged(self):
        self.selectedList.clear()
        for item in self.table.selectedIndexes():
            self.selectedList.append(item.row())

        self.selectedList = list(set(self.selectedList))

        if self.table.rowCount() != 0 and len(self.selectedList) == 0:
            self.selectedList.append(0)
        # print(self.selectedList)


    def addList(self):
        files = QFileDialog.getOpenFileNames(self
                                             , 'Select one or more files to open'
                                             , ''
                                             , 'Sound (*.mp3 *.wav *.ogg *.flac *.wma)')
        cnt = len(files[0]) #추가된 수
        row = self.table.rowCount()  # 이전 누적 수
        self.table.setRowCount(row + cnt)

        for i in range(row, row + cnt):

            self.table.setItem(i, 0, QTableWidgetItem(files[0][i - row]))
            self.table.setItem(i, 1, QTableWidgetItem('-'))

            #self.input_hour = QLineEdit()
            #self.input_hour.setAlignment(Qt.AlignCenter)
            #self.table.setCellWidget(i, 1, self.input_hour)

            self.pbar = QProgressBar()
            self.pbar.setAlignment(Qt.AlignCenter)
            #self.table.setCellWidget(i, 2, self.pbar)
            self.table.setItem(i, 2, QTableWidgetItem(''))

        self.createPlaylist()

    def delList(self):
        row = self.table.rowCount()

        index = []
        for item in self.table.selectedIndexes():
            index.append(item.row())

        index = list(set(index))
        index.reverse()
        for i in index:
            self.table.removeRow(i)

        self.createPlaylist()

    def loadList(self):

        f = open('settings.csv', 'r', encoding='utf-8')
        rdr = csv.reader(f)

        for line in rdr:
            row = self.table.rowCount()
            self.table.setRowCount(1+row)
            i = int(line[0])
            self.table.setItem(i, 0, QTableWidgetItem(line[1]))
            self.table.setItem(i, 1, QTableWidgetItem(line[2]))
            self.table.setItem(i, 2, QTableWidgetItem(''))
        f.close()
        self.createPlaylist()



    def btnClicked(self, id):

        if id == 0:# play
            if self.table.rowCount() > 0 :
                self.player.play(self.playlist, self.selectedList[0], self.playOption)
        elif id == 1 :
            self.player.pause()
        else:
            self.player.stop()


    def tableDbClicked(self, e):
        #self.player.play(self.playlist, self.selectedList[0], self.playOption)

        f = open('settings.csv', 'w', encoding='utf-8', newline='')
        wr = csv.writer(f)


        timeVar = self.settimer.time()
        time_hour = timeVar.hour()
        time_min = timeVar.minute()
        time_sec = timeVar.second()
        txt = str(time_hour) +' : '+str(time_min)+' : '+str(time_sec)

        if(txt == '0 : 0 : 0'):
            set_time = QTableWidgetItem('-')
        else:
            set_time = QTableWidgetItem(txt)
        set_time.setTextAlignment(Qt.AlignCenter)

        self.table.setItem(self.selectedList[0], 1, set_time)

        row = self.table.rowCount()

        for i in range(0, row):
            fpath = self.table.item(i, 0).text()
            table_time = self.table.item(i, 1).text()
            wr.writerow([i, fpath, table_time])

        #print(self.table.item(self.selectedList[0], 1).text())

        f.close()

    def volumeChanged(self):
        self.player.upateVolume(self.slider.value())

    def radClicked(self, id):
        self.playOption = id
        self.player.updatePlayMode(id)

    def paintEvent(self, e):
        self.table.setColumnWidth(0, self.table.width() * 0.6)
        self.table.setColumnWidth(1, self.table.width() * 0.2)

    def createPlaylist(self):
        self.playlist.clear()
        for i in range(self.table.rowCount()):
            self.playlist.append(self.table.item(i, 0).text())

        # print(self.playlist)

    def updateMediaChanged(self, index):
        if index >= 0:
            self.table.selectRow(index)

    def updateDurationChanged(self, index, msec):
        # print('index:',index, 'duration:', msec)
        self.pbar = self.table.cellWidget(index, 2)
        if self.pbar:
            self.pbar.setRange(0, msec)

    def updatePositionChanged(self, index, msec):
        # print('index:',index, 'position:', msec)
        self.pbar = self.table.cellWidget(index, 2)
        if self.pbar:
            self.pbar.setValue(msec)

    def showtime(self):

        # 1970년 1월 1일 0시 0분 0초 부터 현재까지 경과시간 (초단위)
        t = time.time()
        # 한국 시간 얻기
        kor = time.localtime(t)

        # LCD 표시
        currentTime = QTime.currentTime().toString("HH:mm:ss")
        self.hour.display(currentTime)
        '''
        row = self.table.rowCount()
        for i in range(row, row + cnt):
            self.pbar = QProgressBar(self.table)
            self.pbar.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(i, 2, self.pbar)
        '''
        row = self.table.rowCount()

        time_now = str(kor.tm_hour) +' : '+str(kor.tm_min)+' : '+str(kor.tm_sec)



        for i in range(0, row):
            #print(self.table.item(i, 1).text())
            table_time = self.table.item(i, 1).text()
            match = table_time.find(time_now)
            if(match == 0):
                self.player.play(self.playlist, i, self.playOption)
                time.sleep(1)
                print('play')





        # 타이머 설정  (1초마다, 콜백함수)
        timer = Timer(1, self.showtime)
        timer.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CWidget()
    sys.exit(app.exec_())
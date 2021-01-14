from PyQt5 import QtCore, QtGui, QtWidgets
from pyimzml.ImzMLParser import ImzMLParser
from pyimzml.ImzMLWriter import ImzMLWriter
import numpy as np
from scipy.interpolate import griddata

def PeakIntensitySum(spec,diffl,diffr):
    s=spec[0][np.where(spec[0]<=diffr)]
    ss=spec[1][np.where(s>=diffl)]
    return(ss.sum())

def imzml_peak_finder(mz,inte,cut_value,interval):
    peak_mz = []
    for i in range(1,len(inte)):
        if inte[i]>cut_value:
            if inte[i]>inte[i-1] and inte[i]>inte[i+1]:
                if len(peak_mz)>0 and mz[i]-peak_mz[-1]<interval:
                    pass
                else:
                    peak_mz.append(mz[i])
    return peak_mz

class Average_mz_cal(QtCore.QThread):
    trigger = QtCore.pyqtSignal(int,str)
    trigger2 = QtCore.pyqtSignal(np.ndarray,np.ndarray)

    def __init__(self,a):
        super().__init__()
        self.Imzml = a

    def run(self):
        try:
            self.trigger.emit(10,'')
            p = self.Imzml
            self.trigger.emit(20,'')
            Coor = p.coordinates
            m = p.getspectrum(100)
            x1 = m[0]
            kkk = 0
            for i in range(0,len(Coor)):
                v1 = int((i / (len(Coor) - 1)) * 80)+20
                if (v1-kkk)>=1:
                    self.trigger.emit(v1,'')
                    kkk = v1
                tmp = p.getspectrum(i)
                if i ==0:
                    y1 = tmp[1]
                else:
                    y1 = y1 + tmp[1]
            y1 = y1 / len(Coor)
            self.trigger2.emit(x1,y1)
            self.trigger.emit(100,'')
        except Exception as e:
            m = '运行错误，错误信息：' + str(e)
            self.trigger.emit(-1,m)

class Imzml_draw_thread(QtCore.QThread):
    trigger = QtCore.pyqtSignal(int,str)
    trigger2 = QtCore.pyqtSignal(list,int,int)

    def __init__(self,a,b):
        super().__init__()
        self.Imzml = a
        self.meta_info = b

    def run(self):
        try:
            p = self.Imzml
            Coor = p.coordinates
            total = len(Coor)

            points = []
            intensity = []
            self.trigger.emit(10,'')
            kkk = 10
            for indecount in range(0, total):
                v1= int((indecount / (total - 1)) * 90)
                if v1-kkk>=2:
                    self.trigger.emit(v1,'')
                    kkk = v1
                m = p.getspectrum(indecount)
                tmp_intensity = []
                for meta_index in range(0,len(self.meta_info)):
                    left = float(self.meta_info[meta_index][1])
                    right = float(self.meta_info[meta_index][2])
                    tmp_intensity.append(PeakIntensitySum(m, left, right))
                points.append(list(Coor[indecount][:-1]))
                intensity.append(tmp_intensity)

            points , intensity = np.array(points), np.array(intensity)
            xlen = np.array(Coor)[:,0].max()
            ylen = np.array(Coor)[:,1].max()

            grid_x, grid_y = np.mgrid[1:xlen:(xlen * 2j), 1:ylen:(ylen * 2j)]
            self.trigger.emit(95,'')
            meta_grid_data = []
            for i in range(0,len(self.meta_info)):
                grid_z0 = griddata(points, intensity[:,i], (grid_x, grid_y), method='linear')
                meta_grid_data.append(grid_z0)
            self.trigger2.emit(meta_grid_data,xlen,ylen)
            self.trigger.emit(100,'')
        except Exception as e:
            m = 'Running error, info: ' + str(e)
            self.trigger.emit(-1, m)

class MyImzmlExportthread(QtCore.QThread):
    trigger = QtCore.pyqtSignal(int,str)

    def __init__(self,a,b,c):
        super().__init__()
        self.input = a
        self.output = ImzMLWriter(b)
        self.meta_info = c

    def run(self):
        try:
            print('grterw')
            self.trigger.emit(10,'')
            Coor = self.input.coordinates
            T_spec = len(Coor)
            meta_count = len(self.meta_info)
            kkk = 0
            mzs = []
            for uu in range(0,meta_count):
                mz_data = self.meta_info[uu]
                mzs.append(float(mz_data[0]))
            mzs = np.array(mzs)
            print('retrerewrw')
            for indecount in range(0,T_spec):
                v1 = int((indecount / (T_spec - 1)) * 80)+20
                if v1-kkk>=1:
                    self.trigger.emit(v1,'')
                    kkk = v1
                m = self.input.getspectrum(indecount)
                intensity = []
                for uu in range(0,meta_count):
                    mz_data = self.meta_info[uu]
                    I = PeakIntensitySum(m, float(mz_data[1]), float(mz_data[2]))
                    intensity.append(I)
                intensity =np.array(intensity)
                self.output.addSpectrum(mzs,intensity,Coor[indecount])
            self.trigger.emit(100,'')
            self.output.close()
        except Exception as e:
            m = 'Running error, info: ' + str(e)
            self.trigger.emit(-1, m)

class close_widget_thread(QtCore.QThread):
    trigger = QtCore.pyqtSignal(int)

    def __init__(self,seconds):
        super().__init__()
        self.second = seconds

    def run(self):
        self.msleep(self.second)
        self.trigger.emit(100)
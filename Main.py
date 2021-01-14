# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""

from PyQt5.QtCore import pyqtSlot
import xlrd, xlwt
from PyQt5.QtCore import *
import matplotlib.colors as col
import numpy as np
from Imzml_UI import Ui_Form,My_PeakFinder_Form,My_xls_import_Form,My_xls_export_Form,My_Imzml_Export_Form
from Imzml_UI import My_Message_Form,My_Error_Form,My_Progress_Form
from PyQt5.QtWidgets import QApplication,QWidget,QMenu,QFileDialog
from PyQt5.QtGui import QStandardItemModel,QStandardItem
from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
import os
from Avergemz import Average_mz_cal,close_widget_thread,Imzml_draw_thread
from Avergemz import imzml_peak_finder,MyImzmlExportthread
from pyimzml.ImzMLParser import ImzMLParser
from MatplotlibWidget import MyMplCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class MainWindow(QWidget,Ui_Form):

    def __init__(self, parent=None):
        self.x = []
        self.y = []
        self.Meta_len = 0
        self.current_norm_index = 1
        self.metalist = []
        self.scrollbar_value = []
        self.pic_change_index = 0
        super().__init__()
        self.setupUi(self)
        self.horizontalScrollBar.setValue(eval(self.label_4.text()))
        self.horizontalScrollBar_2.setValue(eval(self.label_5.text()))
        self.horizontalScrollBar.valueChanged.connect(self.scrollbarchanged)
        self.horizontalScrollBar_2.valueChanged.connect(self.scrollbar2changed)
        self.pushButton_1.clicked.connect(self.on_pushButton_clicked)
        self.pushButton_2.clicked.connect(self.imzml_clicked)
        self.pushButton_3.clicked.connect(self.PeakFinder_choose)
        self.pushButton_4.clicked.connect(self.peak_import)
        self.pushButton_5.clicked.connect(self.peak_export)
        self.pushButton_6.clicked.connect(self.peak_imzml_export)
        self.lineEdit_2.setText('0.1')
        self.widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.widget.customContextMenuRequested.connect(self.avg_mz_showMenu)
        self.widget.contextMenu = QMenu(self)
        self.mz_rec = []
        self.model=QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['质荷比','Start','End'])
        self.tableView.setModel(self.model)
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.tableView_showMenu)
        self.tableView.contextMenu = QMenu(self)
        self.tableView_Delete = self.tableView.contextMenu.addAction('删除')
        self.tableView_Delete.triggered.connect(self.tableView_Delete_func)

    def peak_import(self):
        self.xls_import_choose = My_xls_import_Form()
        self.xls_import_choose.pushButton_2.clicked.connect(self.xls_import_data)
        self.xls_import_choose.show()

    def xls_import_data(self):
        try:
            file_name = self.xls_import_choose.lineEdit_1.text()
            if file_name.split('.')[-1]=='xls':
                self.metalist = []
                self.model.removeRows(0,self.model.rowCount())
                self.xls_import_choose.close()
                data = xlrd.open_workbook(file_name)
                table = data.sheets()[0]
                nrows = table.nrows
                col = len(table.row_values(0))
                for i in range(1,nrows):
                    tmp_row = table.row_values(i)
                    metalist_tmp, model_tmp = [] ,[]
                    for j in range(0,col):
                        model_tmp.append(QStandardItem(str(tmp_row[j])))
                        metalist_tmp.append(str(tmp_row[j]))
                    self.model.appendRow(model_tmp)
                    self.metalist.append(metalist_tmp)
        except Exception as e :
            m='Running error, info: '+str(e)
            self.error(m)

    def peak_export(self):
        self.xls_export_choose = My_xls_export_Form()
        self.xls_export_choose.pushButton_2.clicked.connect(self.xls_export_data)
        self.xls_export_choose.show()

    def xls_export_data(self):
        try:
            if self.xls_export_choose.radioButton.isChecked():
                f = xlwt.Workbook()
                sheet1 = f.add_sheet(u'sheet1', cell_overwrite_ok=True)
                title = [u'质荷比','Start','End']
                for i in range(0,len(title)):
                    sheet1.write(0,i,title[i])
                for i in range(0,len(self.metalist)):
                    tmp = self.metalist[i]
                    for j in range(0,len(tmp)):
                        sheet1.write(i+1,j,float(tmp[j]))
                f.save(self.xls_export_choose.lineEdit_1.text())
                print('Metainfo Successfully Exported!')
        except Exception as e :
            m='Running error, info: '+str(e)
            self.error(m)

    def peak_imzml_export(self):
        try:
            r= self.tableView.selectionModel().selectedIndexes()
            if r:
                self.imzml_export_choose = My_Imzml_Export_Form()
                self.imzml_export_choose.pushButton_2.clicked.connect(self.imzml_export_data)
                self.imzml_export_choose.show()
        except Exception as e :
            m='Running error, info: '+str(e)
            self.error(m)

    def imzml_export_data(self):
        try:
            index=self.tableView.selectedIndexes()
            self.selected_row = []
            selected_row_index = []
            for i in range(0,len(index)):
                if index[i].row() not in selected_row_index:
                    selected_row_index.append(index[i].row())
            for i in range(0,len(selected_row_index)):
                self.selected_row.append(self.metalist[selected_row_index[i]])
            self.progressBar = My_Progress_Form()
            self.progressBar.progressBar.setValue(0)
            self.progressBar.pushButton.setVisible(True)
            self.progressBar.pushButton.setText('Cancel')
            self.progressBar.pushButton.clicked.connect(self.thread_terminate)
            self.progressBar.show()
            self.mbt = MyImzmlExportthread(self.p,self.imzml_export_choose.lineEdit_1.text(),self.selected_row)
            self.mbt.trigger.connect(self.progress_update)
            self.mbt.start()
            print('yes')
            self.imzml_export_choose.close()
        except Exception as e :
            m='Running error, info: '+str(e)
            self.error(m)

    def scrollbarchanged(self):
        try:
            max_val ,min_val = self.horizontalScrollBar.value(), self.horizontalScrollBar_2.value()
            norm =col.Normalize(vmin = min_val,vmax = max_val)
            self.label_4.setText(str(max_val))
            number = self.current_norm_index
            if max_val != int(self.max_scroll_value[number][1]):
                self.scrollbar_value['max_'+str(number)] = max_val
                print(number,self.scrollbar_value['max_'+str(number)])
            if self.Meta_len ==1: ax_n = self.imzml_fig.add_subplot(1,1,number)
            elif self.Meta_len == 2 : ax_n = self.imzml_fig.add_subplot(1,2,number)
            elif self.Meta_len == 3 : ax_n = self.imzml_fig.add_subplot(1,3,number)
            elif self.Meta_len == 4: ax_n = self.imzml_fig.add_subplot(1,4,number)
            elif self.Meta_len == 5 or self.Meta_len == 6: ax_n = self.imzml_fig.add_subplot(2,3,number)
            elif self.Meta_len == 7 or self.Meta_len == 8: ax_n = self.imzml_fig.add_subplot(2,4,number)
            elif self.Meta_len == 9 or self.Meta_len == 10: ax_n = self.imzml_fig.add_subplot(2,5,number)
            elif self.Meta_len == 11 or self.Meta_len == 12: ax_n = self.imzml_fig.add_subplot(3,4,number)
            elif self.Meta_len == 13 or self.Meta_len == 14 or self.Meta_len == 15: ax_n = self.imzml_fig.add_subplot(3,5,number)
            elif self.Meta_len == 16: ax_n = self.imzml_fig.add_subplot(4,4,number)
            elif self.Meta_len == 17 or self.Meta_len == 18 or self.Meta_len == 19 or self.Meta_len == 20: ax_n = self.imzml_fig.add_subplot(4,5,number)
            elif self.Meta_len == 21 or self.Meta_len == 22 or self.Meta_len == 23 or self.Meta_len == 24: ax_n = self.imzml_fig.add_subplot(4,6,number)
            elif self.Meta_len == 25 or self.Meta_len == 26 or self.Meta_len == 27 or self.Meta_len == 28: ax_n = self.imzml_fig.add_subplot(4,7,number)
            elif self.Meta_len == 29 or self.Meta_len == 30 or self.Meta_len == 31 or self.Meta_len == 32: ax_n = self.imzml_fig.add_subplot(4,8,number)
            elif self.Meta_len == 33 or self.Meta_len == 34 or self.Meta_len == 35 or self.Meta_len == 36: ax_n = self.imzml_fig.add_subplot(4,9,number)
            elif self.Meta_len == 37 or self.Meta_len == 38 or self.Meta_len == 39 or self.Meta_len == 40: ax_n = self.imzml_fig.add_subplot(4,10,number)

            ax_n.clear()
            self.cb[number-1].remove()
            ax_n.set_title(str(number)+') m/z: '+str(self.selected_row[number-1][0]),fontsize = 8, y=0.9)
            gg = ax_n.imshow(self.imzml_grid_data[number-1].T, extent=(1, self.xlen, self.ylen, 1),norm = norm)
            self.cb[number-1] = plt.colorbar(gg,ax = ax_n)
            ax_n.axis('off')
            self.imzml_fig.canvas.draw()
        except Exception as e:
            m = 'Running error, info: ' + str(e)
            self.error(m)

    def scrollbar2changed(self):
        try:
            max_val ,min_val = self.horizontalScrollBar.value(), self.horizontalScrollBar_2.value()
            norm =col.Normalize(vmin = min_val,vmax = max_val)
            self.label_5.setText(str(min_val))
            number = self.current_norm_index
            if min_val != int(self.max_scroll_value[number][0]):
                self.scrollbar_value['min_'+str(number)] = min_val
                print(number,self.scrollbar_value['min_'+str(number)])
            if self.Meta_len ==1: ax_n = self.imzml_fig.add_subplot(1,1,number)
            elif self.Meta_len == 2 : ax_n = self.imzml_fig.add_subplot(1,2,number)
            elif self.Meta_len == 3 : ax_n = self.imzml_fig.add_subplot(1,3,number)
            elif self.Meta_len == 4: ax_n = self.imzml_fig.add_subplot(1,4,number)
            elif self.Meta_len == 5 or self.Meta_len == 6: ax_n = self.imzml_fig.add_subplot(2,3,number)
            elif self.Meta_len == 7 or self.Meta_len == 8: ax_n = self.imzml_fig.add_subplot(2,4,number)
            elif self.Meta_len == 9 or self.Meta_len == 10: ax_n = self.imzml_fig.add_subplot(2,5,number)
            elif self.Meta_len == 11 or self.Meta_len == 12: ax_n = self.imzml_fig.add_subplot(3,4,number)
            elif self.Meta_len == 13 or self.Meta_len == 14 or self.Meta_len == 15: ax_n = self.imzml_fig.add_subplot(3,5,number)
            elif self.Meta_len == 16: ax_n = self.imzml_fig.add_subplot(4,4,number)
            elif self.Meta_len == 17 or self.Meta_len == 18 or self.Meta_len == 19 or self.Meta_len == 20: ax_n = self.imzml_fig.add_subplot(4,5,number)
            elif self.Meta_len == 21 or self.Meta_len == 22 or self.Meta_len == 23 or self.Meta_len == 24: ax_n = self.imzml_fig.add_subplot(4,6,number)
            elif self.Meta_len == 25 or self.Meta_len == 26 or self.Meta_len == 27 or self.Meta_len == 28: ax_n = self.imzml_fig.add_subplot(4,7,number)
            elif self.Meta_len == 29 or self.Meta_len == 30 or self.Meta_len == 31 or self.Meta_len == 32: ax_n = self.imzml_fig.add_subplot(4,8,number)
            elif self.Meta_len == 33 or self.Meta_len == 34 or self.Meta_len == 35 or self.Meta_len == 36: ax_n = self.imzml_fig.add_subplot(4,9,number)
            elif self.Meta_len == 37 or self.Meta_len == 38 or self.Meta_len == 39 or self.Meta_len == 40: ax_n = self.imzml_fig.add_subplot(4,10,number)

            ax_n.clear()
            self.cb[number-1].remove()
            ax_n.set_title(str(number)+') m/z: '+str(self.selected_row[number-1][0]),fontsize = 8, y=0.9)
            gg = ax_n.imshow(self.imzml_grid_data[number-1].T, extent=(1, self.xlen, self.ylen, 1),norm = norm)
            self.cb[number-1] = plt.colorbar(gg,ax = ax_n)
            ax_n.axis('off')
            self.imzml_fig.canvas.draw()
        except Exception as e:
            m = 'Running error, info: ' + str(e)
            self.error(m)

    def avg_mz_showMenu(self, pos):
        # 菜单显示前,将它移动到鼠标点击的位置
        self.widget.contextMenu.exec_(QCursor.pos())  # 在鼠标位置显示
        self.widget.contextMenu.clear()

    def tableView_showMenu(self, pos):
        # 菜单显示前,将它移动到鼠标点击的位置
        self.tableView.contextMenu.exec_(QCursor.pos())  # 在鼠标位置显示

    def tableView_Delete_func(self):
        r= self.tableView.selectionModel().selectedIndexes()
        if r:
            index=self.tableView.selectedIndexes()
            selected_row_index = []
            for i in range(0,len(index)):
                if index[i].row() not in selected_row_index:
                    selected_row_index.append(index[i].row())
            print(selected_row_index)
            for i in range(0,len(selected_row_index)):
                self.model.removeRow(selected_row_index[i]-i)
                self.metalist.remove(self.metalist[selected_row_index[i]-i])
                d_rec = self.mz_rec[selected_row_index[i]-i]
                self.mz_rec.remove(d_rec)
                pc = PatchCollection([d_rec], facecolor='w', alpha=1, edgecolor=None)
                self.ax.add_collection(pc)
            self.avg_mz_fig.canvas.draw()

    def PeakFinder_choose(self):
        self.peak_finder_choose = My_PeakFinder_Form()
        self.peak_finder_choose.pushButton_2.clicked.connect(self.PeakFinder)
        self.peak_finder_choose.show()

    def PeakFinder(self):
        try:
            cut_value = eval(self.peak_finder_choose.lineEdit_2.text())
            interval = eval(self.lineEdit_2.text())/2
            peak_mz = imzml_peak_finder(self.x,self.y,cut_value,interval)
            self.peak_finder_choose.close()
            self.metalist=[]
            self.model.clear()
            self.model.setHorizontalHeaderLabels(['质荷比','Start','End'])
            pc = PatchCollection(self.mz_rec, facecolor='w', alpha=1, edgecolor=None)
            self.ax.add_collection(pc)
            self.avg_mz_fig.canvas.draw()
            self.mz_rec = []
            rec_height = self.z[3]-self.z[2]
            for i in range(0,len(peak_mz)):
                s = peak_mz[i]
                s_start = round(s-interval,5)
                s_end = round(s+interval,5)
                tmp_rec = Rectangle((s-interval,self.z[2]),interval*2,rec_height)
                self.mz_rec.append(tmp_rec)
                self.model.appendRow([
                        QStandardItem(str(s)),
                        QStandardItem(str(s_start)),
                        QStandardItem(str(s_end)),
                        ])
                self.metalist.append([s,s_start,s_end])
            pc = PatchCollection(self.mz_rec, facecolor='g', alpha=0.6, edgecolor=None)
            self.ax.add_collection(pc)
            self.avg_mz_fig.canvas.draw()
        except Exception as e:
            m = 'Running error, info: ' + str(e)
            self.error(m)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        Slot documentation goes here.
        """
        try:
            path = os.getcwd()
            file_name,_= QFileDialog.getOpenFileName(self,u'Choose Imzml file',path,'Imzml files (*.imzml)')
            if file_name:
                self.lineEdit_1.setText(file_name)
                self.progressBar = My_Progress_Form()
                self.progressBar.progressBar.setValue(0)
                self.progressBar.pushButton.setVisible(True)
                self.progressBar.pushButton.setText('Cancel')
                self.progressBar.pushButton.clicked.connect(self.thread_terminate)
                self.progressBar.show()
                self.p = ImzMLParser(self.lineEdit_1.text())
                self.mbt = Average_mz_cal(self.p)
                self.mbt.trigger.connect(self.progress_update)
                self.mbt.trigger2.connect(self.avg_mz_plot)
                self.mbt.start()
        except Exception as e :
            m='Running error, info: '+str(e)
            self.error(m)

    @pyqtSlot()
    def imzml_clicked(self):
        try:
            r= self.tableView.selectionModel().selectedIndexes()
            if r:
                self.progressBar = My_Progress_Form()
                self.progressBar.progressBar.setValue(0)
                self.progressBar.pushButton.setVisible(True)
                self.progressBar.pushButton.setText('Cancel')
                self.progressBar.pushButton.clicked.connect(self.thread_terminate)
                self.progressBar.show()
                index=self.tableView.selectedIndexes()
                self.selected_row = []
                selected_row_index = []
                for i in range(0,len(index)):
                    if index[i].row() not in selected_row_index:
                        selected_row_index.append(index[i].row())
                if len(selected_row_index)<= 40:
                    for i in range(0,len(selected_row_index)):
                        self.selected_row.append(self.metalist[selected_row_index[i]])
                    self.mbt = Imzml_draw_thread(self.p,self.selected_row)
                    self.mbt.trigger.connect(self.progress_update)
                    self.mbt.trigger2.connect(self.imzml_fig_plot)
                    self.mbt.start()
                else:
                    m = 'Running error, info: Please select less than 32 metabolites for imaging at one time!'
                    self.error(m)
        except Exception as e:
            m='Running error, info: '+str(e)
            self.error(m)

    def imzml_fig_plot(self,meta_grid_data,xlen,ylen):
        try:
            self.xlen , self.ylen = xlen,ylen
            self.imzml_grid_data = meta_grid_data
            self.imzml_fig = self.widget_2.mpl.fig
            self.imzml_fig.canvas.mpl_connect('button_press_event',self.on_imzml_fig_click)
            plt.rcParams['font.sans-serif'] = ['KaiTi']  # 指定默认字体
            plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
            self.imzml_fig.clear()
            self.Meta_len = len(meta_grid_data)
            cb, p, ax_l = [], [], []
            if self.Meta_len ==1: sub_inde = [1,1]
            elif self.Meta_len == 2 : sub_inde = [1,2]
            elif self.Meta_len == 3 : sub_inde = [1,3]
            elif self.Meta_len == 4: sub_inde = [1,4]
            elif self.Meta_len == 5 or self.Meta_len == 6: sub_inde = [2,3]
            elif self.Meta_len == 7 or self.Meta_len == 8: sub_inde = [2,4]
            elif self.Meta_len == 9 or self.Meta_len == 10: sub_inde = [2,5]
            elif self.Meta_len == 11 or self.Meta_len == 12: sub_inde = [3,4]
            elif self.Meta_len == 13 or self.Meta_len == 14 or self.Meta_len == 15: sub_inde = [3,5]
            elif self.Meta_len == 16: sub_inde = [4,4]
            elif self.Meta_len == 17 or self.Meta_len == 18 or self.Meta_len == 19 or self.Meta_len == 20: sub_inde = [4,5]
            elif self.Meta_len == 21 or self.Meta_len == 22 or self.Meta_len == 23 or self.Meta_len == 24: sub_inde = [4,6]
            elif self.Meta_len == 25 or self.Meta_len == 26 or self.Meta_len == 27 or self.Meta_len == 28: sub_inde = [4,7]
            elif self.Meta_len == 29 or self.Meta_len == 30 or self.Meta_len == 31 or self.Meta_len == 32: sub_inde = [4,8]
            elif self.Meta_len == 33 or self.Meta_len == 34 or self.Meta_len == 35 or self.Meta_len == 36: sub_inde = [4,9]
            elif self.Meta_len == 37 or self.Meta_len == 38 or self.Meta_len == 39 or self.Meta_len == 40: sub_inde = [4,10]

            self.scrollbar_value= {}
            self.max_scroll_value = [1]
            self.cb ,self.pp= [],[]
            for k in range(0, self.Meta_len):
                mmm = [meta_grid_data[k].min(),meta_grid_data[k].max()]
                self.scrollbar_value['min_'+str(k+1)] = mmm[0]
                self.scrollbar_value['max_'+str(k+1)] = mmm[1]
                self.max_scroll_value.append(tuple(mmm))
                ax_l.append(self.imzml_fig.add_subplot(sub_inde[0], sub_inde[1], k + 1))
                ax_l[k].clear()
                ax_l[k].axis('off')
                ax_l[k].set_title(str(k+1)+') m/z: '+str(self.selected_row[k][0]),fontsize = 8, y=0.9)
                self.pp.append(ax_l[k].imshow(meta_grid_data[k].T, extent=(1, xlen, ylen, 1)))
                self.cb.append(plt.colorbar(self.pp[k], ax=ax_l[k]))
            self.imzml_fig.subplots_adjust(bottom=0.05, left=0.05, hspace=0.2)  # 调整子图间距
            self.imzml_fig.canvas.draw()
        except Exception as e:
            m = 'Running error, info: ' + str(e)
            self.error(m)

    def on_imzml_fig_click(self,event):
        for i in range(0,len(self.pp)):
            if event.button == 1 and event.inaxes == self.pp[i].axes:
                try:
                    number = i+1
                    self.current_norm_index = number
                    self.pic_change_index = number
                    self.msg = My_Message_Form()
                    self.msg.label.setText(
                        u'Start modifying the colormap of  ' + str(number) + ') ' + str(self.metalist[number - 1][0]))
                    self.msg.show()
                    self.horizontalScrollBar.setMaximum(int(self.max_scroll_value[number][1]))
                    self.horizontalScrollBar.setMinimum(int(self.max_scroll_value[number][0]))
                    self.horizontalScrollBar_2.setMaximum(int(self.max_scroll_value[number][1]))
                    self.horizontalScrollBar_2.setMinimum(int(self.max_scroll_value[number][0]))
                    self.horizontalScrollBar.setValue(int(self.scrollbar_value['max_'+str(number)]))
                    self.horizontalScrollBar_2.setValue(int(self.scrollbar_value['min_'+str(number)]))
                    self.clo_i = close_widget_thread(400)
                    self.clo_i.start()
                    self.clo_i.trigger.connect(self.close_window)
                except Exception as e:
                    m = 'Running Error, info: ' + str(e)
                    self.error(m)
                break

    def avg_mz_plot(self,x,y):
        try:
            self.x,self.y = x,y
            self.model.clear()
            self.model.setHorizontalHeaderLabels(['质荷比','Start','End'])
            self.metalist = []
            self.mz_rec = []
            self.widget.layout.removeWidget(self.widget.mpl)
            self.widget.layout.removeWidget(self.widget.mpl_ntb)
            self.widget.mpl = MyMplCanvas()
            self.widget.mpl_ntb = NavigationToolbar(self.widget.mpl, self)
            self.widget.layout.addWidget(self.widget.mpl)
            self.widget.layout.addWidget(self.widget.mpl_ntb)
            self.avg_mz_fig = self.widget.mpl.fig
            self.ax = self.avg_mz_fig.add_subplot(1,1,1)
            self.ax.clear()
            self.ax.plot(x,y,'k',linewidth = 1)
            self.ax.axis([min(x),max(x),min(y),1.1*max(y)])
            self.z = self.ax.axis()
            self.avg_mz_fig.canvas.draw()
            self.avg_mz_fig.tight_layout()
            self.avg_mz_fig.canvas.mpl_connect('button_press_event', self.on_avg_mz_fig_click)
        except Exception as e:
            m = '运行错误，错误信息：' + str(e)
            self.error(m)

    def on_avg_mz_fig_click(self,event):
        if event.button == 3 and event.xdata is not None and event.key is None:
            m = str(round(event.xdata,5))
            self.widget.mzmenu = self.widget.contextMenu.addAction(m)
            self.widget.mzmenu.triggered.connect(self.mzmenu_action)

    def mzmenu_action(self):
        s = eval(self.widget.sender().text())
        interval = eval(self.lineEdit_2.text())/2
        s_start = round(s-interval,5)
        s_end = round(s+interval,5)
        rec_height = self.z[3]-self.z[2]
        tmp_rec = Rectangle((s-interval,self.z[2]),interval*2,rec_height)
        self.mz_rec.append(tmp_rec)
        pc = PatchCollection([tmp_rec], facecolor='g', alpha=0.6, edgecolor=None)
        self.ax.add_collection(pc)
        self.avg_mz_fig.canvas.draw()
        self.model.appendRow([
            QStandardItem(str(s)),
            QStandardItem(str(s_start)),
            QStandardItem(str(s_end)),
            ])
        self.metalist.append([s,s_start,s_end])

    def error(self,m):
        self.eW=My_Error_Form()
        self.eW.label.setText(m)
        self.eW.show()

    def thread_terminate(self):
        self.mbt.terminate()

    def progress_update(self,val,stry):
        if val!=-1:
            self.progressBar.progressBar.setValue(val)
            if val==100:
                self.progressBar.label.setText('Finished!')
                self.clo = close_widget_thread(1)
                self.clo.start()
                self.clo.trigger.connect(self.close_progressbar)
        else:
            self.progressBar.label.setText('Running error, info: '+stry)
            self.progressBar.progressBar.setValue(0)
            self.progressBar.pushButton.setVisible(True)

    def close_progressbar(self,val):
        if val==100:
            self.progressBar.close()

    def close_window(self,val):
        if val==100:
            self.msg.close()

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())

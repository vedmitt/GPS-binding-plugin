# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GPSbindingDialog
                                 A QGIS plugin
 Description
                             -------------------
        copyright            : (C) 2022 by Ronya14
        email                : ronya14@mail.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import sys

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QApplication, QTreeWidgetItem, QToolButton

from .logic.gps_binding import *
from .logic.CheckableComboBox import CheckableComboBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gps_binding_plugin_dialog_base.ui'))

TREEWIDGET_HEAD = ('Select', 'Name', 'Filepath')
CSV_FILTER = "CSV Files (*.csv, *.txt)"
GPS_FILTER = "GPS Files (*.gpx)"
ACCEPTED_EXT = ('.txt', '.csv', '.gpx')
TIME_COLS = ('DATE', 'TIME')
DATA_FORMATS = ["%m.%d.%yT%H:%M:%S,%f"]
PROJECT_FOLDER = os.path.expanduser("~/Documents")


class GPSbindingDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GPSbindingDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.setWindowTitle('Привязка GPS координат')
        self.inf_tw.setHeaderLabels(TREEWIDGET_HEAD)
        self.gps_tw.setHeaderLabels(TREEWIDGET_HEAD)
        self.inf_add.clicked.connect(lambda: self.openFileNamesDialog(self.inf_tw, [CSV_FILTER], CSV_FILTER))
        self.gps_add.clicked.connect(
            lambda: self.openFileNamesDialog(self.gps_tw, [CSV_FILTER, GPS_FILTER], GPS_FILTER))
        self.inf_del.clicked.connect(lambda: self.removeSelectedItems(self.inf_tw))
        self.gps_del.clicked.connect(lambda: self.removeSelectedItems(self.gps_tw))

        self.inf_dt_cb = CheckableComboBox()
        self.inf_dt_tb = QToolButton()
        self.horizontalLayout_2.addWidget(self.inf_dt_cb)
        self.horizontalLayout_2.addWidget(self.inf_dt_tb)
        self.inf_dt_tb.clicked.connect(lambda: self.updateComboBox(self.inf_dt_cb, 'inf_dt_tb'))

        # self.gps_dt_tb.clicked.connect(lambda: self.updateComboBox(self.gps_dt_cb))

        self.updateComboBox(self.inf_dt_f_cb, 'inf_dt_f_tb')
        self.updateComboBox(self.gps_dt_f_cb, 'gps_dt_f_tb')
        self.inf_dt_f_tb.clicked.connect(lambda: self.updateComboBox(self.inf_dt_f_cb, 'inf_dt_f_tb'))
        self.gps_dt_f_tb.clicked.connect(lambda: self.updateComboBox(self.gps_dt_f_cb, 'gps_dt_f_tb'))

        self.ouf_tb.clicked.connect(self.getSaveFilePath)

        self.progress_line.setVisible(False)

        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.run)

        # self._init_for_debug()

    def _init_for_debug(self):
        # ------ init for debugging ---------
        fpaths = [
            '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/Data/2021-07-21_02-42-06.txt',
            '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/Data/2021-07-21_04-29-56.txt']
        gpxs = ['/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/LOG/00000001.BIN.gpx',
                '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/LOG/00000002.BIN.gpx']
        res_path = '/Users/ronya/PycharmProjects/OUTPUT/output2.txt'

        for path in fpaths:
            item = QTreeWidgetItem()
            item.setCheckState(0, Qt.Checked)
            item.setText(1, 'Name')
            item.setText(2, path)
            self.inf_tw.addTopLevelItem(item)

        self.inf_gb.setEnabled(True)

        for path in gpxs:
            item = QTreeWidgetItem()
            item.setCheckState(0, Qt.Checked)
            item.setText(1, 'Name')
            item.setText(2, path)
            self.gps_tw.addTopLevelItem(item)

        self.gps_gb.setEnabled(False)

        self.ouf_le.setText(res_path)

    def getPathsFromTreeView(self, treeWidget):
        items = [treeWidget.topLevelItem(i) for i in range(treeWidget.topLevelItemCount()) if
                 treeWidget.topLevelItem(i).checkState(0) == 2]
        return [item.text(2) for item in items]

    def getSelectedFromComboBox(self, combo):
        if isinstance(combo, CheckableComboBox):
            entries = [combo.itemText(i) for i in range(combo.count()) if combo.itemChecked(i) == True]
        else:
            entries = combo.currentText()
        return entries

    def updateComboBox(self, combo, sender_name):
        fields = {'inf_dt_tb': self.inf_tw, 'gps_dt_tb': self.gps_tw}
        # sender_name = self.sender().objectName()
        # print(sender_name)

        combo.clear()
        if sender_name in ('inf_dt_f_tb', 'gps_dt_f_tb'):
            combo.addItems(DATA_FORMATS)
        elif sender_name in fields.keys():
            head = read_csv([self.getPathsFromTreeView(fields[sender_name])[0]], onlyHead=True)
            for col in head:
                combo.addItem(col)
                if col in TIME_COLS:
                    combo.setItemChecked(head.index(col), True)
                else:
                    combo.setItemChecked(head.index(col), False)

    def openFileNamesDialog(self, treeWidget, filters, initialFilter):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы", PROJECT_FOLDER,
                                                filter=";;".join(["All Files (*)"] + filters),
                                                initialFilter=initialFilter,
                                                options=options)
        if files:  # если пользователь выбрал файлы
            sender_name = self.sender().objectName()
            if sender_name == 'inf_add':
                self.inf_gb.setEnabled(True)
                # self.updateComboBox(self.inf_dt_cb, 'inf_dt_tb')
            elif sender_name == 'gps_add':
                if files[0].split('.')[-1] == 'gpx':
                    self.gps_gb.setEnabled(False)
                else:
                    self.gps_gb.setEnabled(True)

            for fpath in files:
                fname = os.path.basename(fpath)  # имя файла
                # добавим файлы в treeWidget
                item = QTreeWidgetItem()
                item.setCheckState(0, Qt.Checked)
                item.setText(1, fname)
                # item.setData(2, Qt.UserRole, id(item))
                item.setText(2, fpath)
                treeWidget.addTopLevelItem(item)

    def removeSelectedItems(self, treeWidget):
        listItems = [treeWidget.topLevelItem(i) for i in range(treeWidget.topLevelItemCount()) if
                     treeWidget.topLevelItem(i).checkState(0) == 2]
        # print(listItems)
        if not listItems: self.progress_line.setText('Nothing to remove!')
        for item in listItems:
            itemIndex = treeWidget.indexOfTopLevelItem(item)
            treeWidget.takeTopLevelItem(itemIndex)
        print('Number of items remaining ' + str(treeWidget.topLevelItemCount()))

        if treeWidget.topLevelItemCount() == 0:
            sender_name = self.sender().objectName()
            if sender_name == 'inf_del':
                self.inf_gb.setEnabled(False)
                self.inf_dt_cb.clear()
            elif sender_name == 'gps_del':
                self.gps_gb.setEnabled(False)
                self.gps_dt_cb.clear()

    def getSaveFilePath(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fpath, _ = QFileDialog.getSaveFileName(self, "Save file", PROJECT_FOLDER,
                                               filter=";;".join(["All Files (*)"] + [CSV_FILTER]),
                                               initialFilter=CSV_FILTER,
                                               options=options)
        self.ouf_le.setText(fpath)

    def run(self):
        fpaths = self.getPathsFromTreeView(self.inf_tw)
        gpx_paths = self.getPathsFromTreeView(self.gps_tw)
        extensions = {os.path.splitext(path)[1] for path in fpaths + gpx_paths}

        time_cols = self.getSelectedFromComboBox(self.inf_dt_cb)
        data_format = self.getSelectedFromComboBox(self.inf_dt_f_cb)

        res_path = self.ouf_le.text()
        sep = '\t'

        self.progress_line.setVisible(True)
        if extensions.difference(set(ACCEPTED_EXT)) != set():
            self.progress_line.setText(f'Неподдерживаемый формат данных! Поддерживаемые форматы: {ACCEPTED_EXT}.')
        else:
            if len(time_cols) == 0 or len(time_cols) > 2:
                self.progress_line.setText(
                    f'Количество выбранных столбцов времени входного файла {len(time_cols)}. Должно быть 1-2.')
            else:
                if data_format == '':
                    self.progress_line.setText(f'Выберите формат даты-времени для входного файла.')
                else:
                    if res_path == '':
                        self.progress_line.setText(f'Введите путь для сохранения файла.')
                    else:
                        if not gps_binding((fpaths, time_cols, data_format), gpx_paths, res_path, sep):
                            self.progress_line.setText(f'Файл {res_path} не был сохранен.')
                        else:
                            self.progress_line.setText(f'Файл {res_path} успешно сохранен.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GPSbindingDialog()
    sys.exit(ex.exec_())

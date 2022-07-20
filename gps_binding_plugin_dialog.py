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
from PyQt5.QtWidgets import QFileDialog, QApplication, QTreeWidgetItem, QToolButton, QComboBox

from .logic.gps_binding import GPSBuilder

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gps_binding_plugin_dialog_base.ui'))

TREEWIDGET_HEAD = ('Select', 'Name', 'Filepath')
CSV_FILTER = "CSV Files (*.csv, *.txt)"
GPS_FILTER = "GPS Files (*.gpx)"
# ACCEPTED_EXT = ('.txt', '.csv', '.gpx')
TIME_COLS = ('DATE', 'TIME')
GEOM_COLS = ('LON', 'LAT', 'ALT')
ACCEPTED_TXT_SEPS = {'Space': ' ',
                     'Comma': ',',
                     'Tab': '\t',
                     'Semicolon': ';'}
PROJECT_FOLDER = os.path.expanduser("~/Documents")
DATA_FORMATS = ["%m.%d.%yT%H:%M:%S,%f",
                # "%m-%d-%yT%H:%M:%S,%f",
                # "%m.%y.%dT%H:%M:%S,%f",
                # "%m-%y-%dT%H:%M:%S,%f",
                # "%d.%m.%yT%H:%M:%S,%f",
                # "%d-%m-%yT%H:%M:%S,%f",
                # "%d.%y.%mT%H:%M:%S,%f",
                # "%d-%y-%mT%H:%M:%S,%f",
                # "%y.%m.%dT%H:%M:%S,%f",
                # "%y-%m-%dT%H:%M:%S,%f",
                # "%y.%d.%mT%H:%M:%S,%f",
                # "%y-%d-%mT%H:%M:%S,%f",
                ]


class CheckableComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self._changed = False
        self.view().pressed.connect(self.handleItemPressed)

    def setItemChecked(self, index, checked=False):
        item = self.model().item(index, self.modelColumn())  # QStandardItem object

        if checked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)

        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self._changed = True

    def hidePopup(self):
        if not self._changed:
            super().hidePopup()
        self._changed = False

    def itemChecked(self, index):
        item = self.model().item(index, self.modelColumn())
        return item.checkState() == Qt.Checked


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

        # input fields combobox
        self.inf_dt_cb = CheckableComboBox()
        self.inf_dt_tb = QToolButton()
        self.horizontalLayout_2.addWidget(self.inf_dt_cb)
        self.horizontalLayout_2.addWidget(self.inf_dt_tb)

        # gps fields combobox
        self.gps_dt_cb = CheckableComboBox()
        self.gps_dt_tb = QToolButton()
        self.horizontalLayout_5.addWidget(self.gps_dt_cb)
        self.horizontalLayout_5.addWidget(self.gps_dt_tb)

        # gps geometry combobox
        self.gps_geom_cb = CheckableComboBox()
        self.gps_geom_tb = QToolButton()
        self.horizontalLayout_6.addWidget(self.gps_geom_cb)
        self.horizontalLayout_6.addWidget(self.gps_geom_tb)

        # output fields combobox
        self.ouf_cb = CheckableComboBox()
        self.ouf_tb_2 = QToolButton()
        self.horizontalLayout_7.addWidget(self.ouf_cb)
        self.horizontalLayout_7.addWidget(self.ouf_tb_2)
        self.ouf_tb_2.clicked.connect(lambda: self.updateComboBox(self.ouf_cb, 'ouf_tb_2'))

        self.updateComboBox(self.inf_dt_f_cb, 'inf_dt_f_tb')
        self.updateComboBox(self.gps_dt_f_cb, 'gps_dt_f_tb')

        self.inf_sep_tb.clicked.connect(lambda: self.updateComboBox(self.inf_sep_cb, 'inf_sep_tb'))
        self.inf_dt_tb.clicked.connect(lambda: self.updateComboBox(self.inf_dt_cb, 'inf_dt_tb'))
        self.inf_dt_f_tb.clicked.connect(lambda: self.updateComboBox(self.inf_dt_f_cb, 'inf_dt_f_tb'))
        self.gps_sep_tb.clicked.connect(lambda: self.updateComboBox(self.gps_sep_cb, 'gps_sep_tb'))
        self.gps_dt_tb.clicked.connect(lambda: self.updateComboBox(self.gps_dt_cb, 'gps_dt_tb'))
        self.gps_dt_f_tb.clicked.connect(lambda: self.updateComboBox(self.gps_dt_f_cb, 'gps_dt_f_tb'))
        self.gps_geom_tb.clicked.connect(lambda: self.updateComboBox(self.gps_geom_cb, 'gps_geom_tb'))
        self.ouf_tb_2.clicked.connect(lambda: self.updateComboBox(self.ouf_cb, 'ouf_tb_2'))

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
        # gpxs = ['/Users/ronya/PycharmProjects/TESTDATA/input/read_gps_csv/20210830_f1-6.txt']
        res_path = '/Users/ronya/PycharmProjects/TESTDATA/OUTPUT/output6.txt'

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

        self.updateComboBox(self.inf_sep_cb, 'inf_sep_tb')
        self.updateComboBox(self.gps_sep_cb, 'gps_sep_tb')

        self.gps_gb.setEnabled(True)
        self.ouf_gb.setEnabled(True)
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
        fields = {'inf_dt_tb': self.inf_tw,
                  'gps_dt_tb': self.gps_tw,
                  'gps_geom_tb': self.gps_tw,
                  'ouf_tb_2': self.inf_tw}
        # sender_name = self.sender().objectName()
        # print(sender_name)
        combo.clear()
        if sender_name in ('inf_sep_tb', 'gps_sep_tb'):
            a = {'inf_sep_tb': self.inf_tw,
                  'gps_sep_tb': self.gps_tw}
            combo.addItems(ACCEPTED_TXT_SEPS.keys())
            paths = self.getPathsFromTreeView(a[sender_name])
            if len(paths) > 0:
                sep = GPSBuilder().read_csv(paths, onlySep=True)
                if sep is not None:
                    combo.setCurrentText(list(ACCEPTED_TXT_SEPS.keys())[list(ACCEPTED_TXT_SEPS.values()).index(sep)])
        elif sender_name in ('inf_dt_f_tb', 'gps_dt_f_tb'):
            combo.addItems(DATA_FORMATS)
        elif sender_name in fields.keys():
            seps = {'inf_dt_tb': self.inf_sep_cb,
                    'gps_dt_tb': self.gps_sep_cb,
                    'gps_geom_tb': self.gps_sep_cb,
                    'ouf_tb_2': self.inf_sep_cb}
            sep = ACCEPTED_TXT_SEPS.get(self.getSelectedFromComboBox(seps.get(sender_name)))
            head = GPSBuilder().read_csv([self.getPathsFromTreeView(fields[sender_name])[0]], sep, onlyHead=True)
            if sender_name == 'ouf_tb_2':
                head = GPSBuilder().read_csv([self.getPathsFromTreeView(fields[sender_name])[0]], sep, onlyTHead=True)
                COLS = head
            elif sender_name == 'gps_geom_tb':
                COLS = GEOM_COLS
            else:
                COLS = TIME_COLS
            for col in head:
                combo.addItem(col)
                if col in COLS:
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
        if self.ouf_le.text() != '':
            self.ouf_gb.setEnabled(True)

    def run(self):
        # input files
        fpaths = self.getPathsFromTreeView(self.inf_tw)
        inf_sep = ACCEPTED_TXT_SEPS.get(self.getSelectedFromComboBox(self.inf_sep_cb))
        inf_time_cols = self.getSelectedFromComboBox(self.inf_dt_cb)
        inf_data_format = self.getSelectedFromComboBox(self.inf_dt_f_cb)
        inf_params = (fpaths, inf_sep, inf_time_cols, inf_data_format)

        # gps files
        gps_paths = self.getPathsFromTreeView(self.gps_tw)
        gps_sep = ACCEPTED_TXT_SEPS.get(self.getSelectedFromComboBox(self.gps_sep_cb))
        gps_time_cols = self.getSelectedFromComboBox(self.gps_dt_cb)
        gps_data_format = self.getSelectedFromComboBox(self.gps_dt_f_cb)
        gps_geom_cols = self.getSelectedFromComboBox(self.gps_geom_cb)
        gps_params = (gps_paths, gps_sep, gps_time_cols, gps_data_format, gps_geom_cols)

        # output file
        ouf_path = self.ouf_le.text()
        ouf_sep = '\t'
        ouf_cols = self.getSelectedFromComboBox(self.ouf_cb)
        ouf_params = (ouf_path, ouf_sep, ouf_cols)

        # execute main process
        self.progress_line.setVisible(True)

        if len(inf_time_cols) == 0 or len(inf_time_cols) > 2:
            self.progress_line.setText(
                f'Количество выбранных столбцов времени входного файла {len(inf_time_cols)}. Должно быть 1-2.')
        else:
            if inf_data_format == '':
                self.progress_line.setText(f'Выберите формат даты-времени для входного файла.')
            else:
                if ouf_path == '':
                    self.progress_line.setText(f'Введите путь для сохранения файла.')
                else:
                    m = GPSBuilder().gps_binding(inf_params, gps_params, ouf_params)
                    self.progress_line.setText(m)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GPSbindingDialog()
    sys.exit(ex.exec_())

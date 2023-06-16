#! /usr/bin/python3
'''GUI version of Repair Node parsing'''
#standard library imports
import os
import re
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QLabel, QDialog,\
                            QGridLayout,QPushButton, QFileDialog, QMessageBox

#local imports
from get_repaired_node import read_repair_file, from_unix, read_digest_file
from get_padded_line import get_analyze_file, read_analyze_file, read_4d_nav, qt_append_padded

#colors
accept_color = "#228B22"
alert_color = "#922B21"
warn_color = "#483D8B"

unix_time_pattern = "\d+"                                       #pattern to extract unix time from string
out_pattern = "/dl\d/\w+/\w+/\d{4}-\d{2}-\d{2}/\w+.raw"         #pattern for auto raw file path search
raw_pattern = "/dl\d/\w+/\d{4}-\d{2}-\d{2}/\w+.raw"             #pattern for repair raw file path search
bumper_pattern = "\w+_\d{1,3}_\d{6}_b(\d+)_rsn(\d+)"            #pattern for extracting bumper and serial numbers from file name

__version__ = "prod 0.0.1"

# Versions
# prod 0.0.1 June 2023
# prod 0.0.2 June 2023

#dialog window
class DumbDialog(QDialog):
    def __init__(self,parent = None):
        super(DumbDialog,self).__init__(parent)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint|Qt.WindowCloseButtonHint)
        #buttons and widgets
        self.openButton = QPushButton("Open file")
        self.appendButton = QPushButton("Append line")
        self.paddingButton = QPushButton("Padding check")
        self.infoLabel = QLabel("Select the repair file to read")

        #b&w settings
        self.infoLabel.setStyleSheet("border: 1px solid black;")
        self.infoLabel.setAlignment(Qt.AlignCenter)
        self.appendButton.setEnabled(False)
        self.paddingButton.setEnabled(False)

        #layout
        grid = QGridLayout()
        grid.addWidget(self.openButton,0, 0)
        grid.addWidget(self.appendButton, 0, 1)
        grid.addWidget(self.paddingButton, 0, 2)
        grid.addWidget(self.infoLabel,1,0, 1, 3)

        icon = QIcon()
        icon.addFile("./Resources/wrench.png")
        self.setWindowIcon(icon)

        self.setLayout(grid)
        self.setMinimumSize(500,140)
        self.setMaximumSize(501,141)
        self.setWindowTitle(f"Repair file {__version__}")

        self.openButton.clicked.connect(self.getLine)
        self.appendButton.clicked.connect(self.append_to_file)
        self.paddingButton.clicked.connect(self.get_padded)

    def getLine(self):
        file,check = QFileDialog.getOpenFileName(None, "Select repair file","/qc/", "Text Files (*.txt)",options = QFileDialog.DontUseNativeDialog)
        if check:
            #read the repair file
            lines =  read_repair_file(file)
            try:
                start = [line for line in lines if line.startswith("Start second")][0]
                stop = [line for line in lines if line.startswith("Stop second")][0]
                stop_time = re.search(unix_time_pattern, stop).group(0)
                start_time = re.search(unix_time_pattern, start).group(0)
            except:
                print("Something went wrong")
            try:
                out_str = [line for line in lines if line.startswith("Out File")][0]
                try:
                    out_path = re.search(out_pattern, out_str).group(0)
                except AttributeError as err:
                    print(f"Couldn't extract the Out file path: {err}")
            except IndexError:
                print(f"No 'Out File' string in {repair_file}.")

            try:
                raw_str = [line for line in lines if line.startswith("Created raw file")][0]
                try:
                    raw_path = re.search(raw_pattern, raw_str).group(0)
                except AttributeError as err:
                    print(f"Couldn't extract the raw file path: {err}")
            except IndexError:
                print(f"No 'Created raw file' string in {repair_file}.")

            #assume that we have the raw path
            self.bumper = re.search(bumper_pattern, os.path.basename(raw_path)).groups()[0]
            self.serial = re.search(bumper_pattern, os.path.basename(raw_path)).groups()[1]

            #form the path
            self.ssd_path = os.path.normpath(os.path.join(os.path.split(out_path)[0],os.path.basename(raw_path)))
            #create the output message
            self.pathExists = False
            if os.path.exists(self.ssd_path):
                message = f"<b>Bumper:</b> {self.bumper} <b>Serial:</b> {self.serial}<br><b>Start time:</b> {start_time} \
                {from_unix(start_time)}<br><b>Stop time:</b> {stop_time} {from_unix(stop_time)} <br> <font color = {accept_color}> <b> repair *.raw file is already in Records</b> </font>"
                self.pathExists = True
            else:
                message = f"<b>Bumper:</b> {bumper} <b>Serial:</b> {serial}<br><b>Start time:</b> {start_time} \
                {from_unix(start_time)}<br><b>Stop time:</b> {stop_time} {from_unix(stop_time)} <br> <font color = {warn_color}> <b> repair *.raw must be copied to Records</b> </font>"

            #the output string for further appending
            self.line_out = f"{self.bumper},{self.serial},{start_time},{stop_time},{from_unix(start_time)},{from_unix(stop_time)},{self.ssd_path}"

            self.infoLabel.setText(message)
            self.appendButton.setEnabled(True)
            self.appendButton.setFocus()
            return
        else:
            message = "<b>No file selected</b>"
            self.infoLabel.setText(message)
            return


    def append_to_file(self):
        #check if the line is already in file
        with open(digest_file, 'r', encoding = 'utf-8') as file:
            lines = file.readlines()
            check_list = [line[6:].strip() for line in lines]
        if self.line_out in check_list:
            QMessageBox.warning(self, "Line exits", "Line you try to append alredy exists")
            self.infoLabel.setText(f"<b><font color = {alert_color}>Please, choose another file or delete exisitng line</b></font>")
            self.appendButton.setEnabled(False)
            self.paddingButton.setEnabled(True)
            self.openButton.setFocus()
        else:
            digest_df = read_digest_file(digest_file)
            seq_number = digest_df.number.max() + 1
            to_append = f"{seq_number},{self.line_out}\n"

            try:
                with open(digest_file,'a', encoding='utf-8') as file:
                    file.write(to_append)
                    if self.pathExists == True:
                        message = f"<font color = {accept_color}><b>Line appended</font></b>"
                    else:
                        message = f"<font color = {accept_color}><b>Line appended</font></b><br><fonr color = {alert_color}Don't forget to copy repair *.raw file</font></b>"
            except:
                message = f"<font color = {alert_color}><b>Couldn't append the line</font><b>"
                self.openButton.setFocus()
                self.infoLabel.setText(message)
                self.infoLabel.setText(message)
                self.appendButton.setEnabled(False)

            self.openButton.setFocus()
            self.infoLabel.setText(message)
            self.appendButton.setEnabled(False)
            self.paddingButton.setEnabled(True)

    def get_padded(self):
        analyze_file = get_analyze_file(self.serial)
        if analyze_file:
            #print(os.path.exists(analyze_file), os.stat(analyze_file).st_size)
            message = f"<font color = {accept_color}><b>Found file: {os.path.basename(analyze_file)}</b></font>"
            self.infoLabel.setText(message)
            analyze_file_df = read_analyze_file(analyze_file)
            gp_df = analyze_file_df.query('delta != 1')
            if len(gp_df) == 0:                                 #if no such line
                message = f"No padded samples in {os.path.basename(analyze_file)}"
                self.openButton.setFocus()
                self.infoLabel.setText(message)
                self.appendButton.setEnabled(False)
                self.paddingButton.setEnabled(True)
            else:
                nav_df = read_4d_nav(fdnav_file)
                line_pnt = nav_df.query(f"NodeCode == {self.bumper}")
                line_dct = line_pnt.to_dict(orient='records')[0]
                line = line_dct['Line']
                point = line_dct['Point']
                index = line_dct['Index']

                dct = gp_df.to_dict(orient='records')[0]        #convert to dictionary for some reason
                stop = int(dct['second'])                       #get the last second af gap
                start = stop - int(dct['delta']) +1             #get the first second of gap
                padded_line = f"{line}\t\t{point}\t\t\t{index}\t\t\t{start}\t\t{stop}\n"
                message = qt_append_padded(padded_file,padded_line)

                if len(gp_df) >= 2:
                    padded2 = gp_df.to_dict(orient='records')[1]
                    stop2 = int(padded2['second'])
                    start2 = stop2 - int(padded2['delta']) + 1
                    padded_line2 = f"{line}\t\t{point}\t\t\t{index}\t\t\t{start2}\t\t{stop2}\n"
                    append_padded(padded_file2,padded_line2)
                    message = qt_append_padded

                self.infoLabel.setText(message)
                self.appendButton.setEnabled(False)
                self.paddingButton.setEnabled(False)

        else:
            message = f"<font color = {alert_color}><b>Couldn't find analyze file for serial {self.serial}</font></b>"
            self.openButton.setFocus()
            self.infoLabel.setText(message)
            self.appendButton.setEnabled(False)
            self.paddingButton.setEnabled(True)

if __name__ == "__main__":
    digest_file = r"/home/geo3/Public/zdmefr/02_Tools/Inputs/DigestDownloads.csvManual"
    padded_file = r"/qc/06-ARAM/padding/padded_nodes.txt"
    padded_file2 = r"/qc/06-ARAM/padding/padded_nodes_2.txt"
    fdnav_file = r"/qc/06-ARAM/nav/Postplot_R/4dnav_lines/BR001522_4dnav.csv"
    app = QApplication(sys.argv)
    dialog = DumbDialog()
    dialog.show()
    app.exec_()

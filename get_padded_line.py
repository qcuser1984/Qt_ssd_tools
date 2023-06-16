#!/usr/bin/python3

import os
import re
import sys
import glob
import pandas as pd


accept_color = "#228B22"
alert_color = "#922B21"
warn_color = "#F4D03F"

def get_analyze_file(serial):
    '''returns path to analyze file from the serial number'''
    #changing directory is really important
    os.chdir("/")

    path_list = glob.glob(f"./dl*/RawImageRepairs/*/sn{serial}_analyze.csv")
    #print(f"Path list: {path_list}")
    if len(path_list) == 0:
        print(f"Couldn't find sn{serial}_analyze.csv. Please, check the serial number.")
    elif len(path_list) > 1:
        out_file = path_list[0]
        print(os.path.exists(out_file), os.stat(out_file).st_size)
        if os.path.exists(path_list[0]) and os.stat(path_list[0]).st_size != 0:
            print(f"Found: {len(path_list)} files with serial {serial}, returning {os.path.basename(path_list[0])}.")
            return out_file
        print(f"File: {path_list[0]} doesn't really exits of empty")
        return None
    else:
        out_file = path_list[0]
        #print(f"{out_file} inside function")
        if os.path.exists(path_list[0]) and os.stat(path_list[0]).st_size != 0:
            return out_file
        print(f"File: {path_list[0]} doesn't really exits of empty")
        return None

def get_raw_file(serial):
    '''Get the path to raw file based on serial'''
    os.chdir("/") #probably not a good idea
    path_list = glob.glob(f"./dl*/RawImageRepairs/*/*_rsn{serial}_*.raw")
    if len(path_list) == 0:
        print(f"Couldn't find *snl{serial}_.raw. Please, check the serial number.")
    elif len(path_list) > 1:
        out_file = path_list[0]
        print(os.path.exists(out_file), os.stat(out_file).st_size)
        if os.path.exists(path_list[0]) and os.stat(path_list[0]).st_size != 0:
            print(f"Found: {len(path_list)} files with serial {serial}, returning {os.path.basename(path_list[0])}.")
            return out_file
        print(f"File: {path_list[0]} doesn't really exits of empty")
        return None
    else:
        out_file = path_list[0]
        if os.path.exists(path_list[0]) and os.stat(path_list[0]).st_size != 0:
            return out_file
        print(f"File: {path_list[0]} doesn't really exits of empty")
        return None


def read_analyze_file(path_to_file):
    '''read the sn***analyze.csv and return it in form of DataFrame'''
    af_df = pd.read_csv(path_to_file)
    return(af_df)

def get_sn(file_name):
    '''return bumper from file name in format sn****analyze.csv'''
    nb_list = re.findall(r'\d+',file_name)
    return(nb_list[0])


def read_4d_nav(nav_file):
    '''Read 4dnav file and return pandas DataFrame containing particular columns'''
    if os.path.exists(nav_file) and os.stat(nav_file).st_size != 0:
        try:
            nav_df = pd.read_csv(nav_file, skiprows = 8)
            nav_df = nav_df[["Line","Point","NodeCode","Index"]]
            return nav_df
        except (IOError, OSError) as exc:
            print(f"Error reading {os.path.basename(nav_file)}: {exc}")
            return None
    else:
        print(f"File {os.path.basename(nav_file)} doesn't exist or is an empty file")
        return None

def get_bmp_sn(file_in, serial):
    '''get bumper number from serial number'''
    try:
        bmp_df = pd.read_csv(file_in, sep = "\s+", names = ["Bumper", "Serial"] )
        serial_df = bmp_df.query(f"Serial == {serial}")
        return(serial_df['Bumper'].values[0])
    except (IOError, OSError) as exc:
        print(f"Error reading {os.path.basename(file_in)}: {exc}")
        return None

def qt_append_padded(file_in, line):
    '''append the line to padded file'''
    #check if line already exits
    with open(file_in, 'r', encoding= 'utf-8') as file:
        lines = file.readlines()
    if line in lines:
        line = re.sub('\s+',' ', line)
        message = (f"<font color = {warn_color}><b>{file_in}<br>already has line {line.strip()}</font></b>")
        return message
    else:
        try:
            with open(file_in,'a', encoding = 'utf-8') as file:
                file.write(line)
                message = f"<font color = {accept_color}><b>{line.strip()}<br>added to {file_in}</font></b>"
                return message
        except (IOError, OSError) as exc:
            message = f"<font color = {alert_color}><b>Something went wrong:<br>{exc}</font></b>"
            return message

def append_padded(file_in, line):
    '''append the line to padded file'''
    #check if line already exits
    with open(file_in, 'r', encoding= 'utf-8') as file:
        lines = file.readlines()
    if line in lines:
        line = re.sub('\s+',' ', line)
        print(f"File {os.path.basename(file_in)} already contains line {line.strip()}")
    else:
        try:
            with open(file_in,'a', encoding = 'utf-8') as file:
                file.write(line)
                print(f"{line.strip()} added to {os.path.basename(file_in)}")
        except (IOError, OSError) as exc:
            print(f"Something went wrong: {exc}")

def main():
    '''main function'''
    analyze_file = get_analyze_file(serial_number)
    if analyze_file:
        print(os.path.exists(analyze_file), os.stat(analyze_file).st_size)
        print(f"Found file: {analyze_file}")
    else:
        #error message is produced by get_analyze_file function
        sys.exit(1)

    analyze_file_df = read_analyze_file(analyze_file)
    gp_df = analyze_file_df.query('delta != 1')         #find line(s) where time delta exceeds 1 second
    #print(gp_df)

    if len(gp_df) == 0:                                 #if no such line
        print(f"No padded samples in {os.path.basename(analyze_file)}. Exiting ...")
        sys.exit(1)
    else:
        if len(gp_df) >=2:
            print(f"At least two padded intervals in {os.path.basename(analyze_file)}\nFirst two intervals will be updated\n")
        #get bumper using serial
        bumper = get_bmp_sn(bmp_sn_file, serial_number)
        #print(bumper)
        nav_df = read_4d_nav(fdnav_file)
        line_pnt = nav_df.query(f"NodeCode == {bumper}")

        #in case bumper deos not correspond to serial from the list
        #just take it from the file name, which should be done by default
        if len(line_pnt) == 0:
            print(f"\nBumper {bumper} from {bmp_sn_file} doesn't correspond to bumper in {os.path.basename(fdnav_file)}")
            bumper_pattern = "\w+_\d{1,3}_\d{6}_b(\d+)_rsn(\d+)"
            raw_file = get_raw_file(serial_number)
            bumper = re.search(bumper_pattern, os.path.basename(raw_file)).groups()[0]
            print(f"Using bumper {bumper} from {raw_file}\n")
            line_pnt = nav_df.query(f"NodeCode == {bumper}")


        line_dct = line_pnt.to_dict(orient='records')[0]
        line = line_dct['Line']
        point = line_dct['Point']
        index = line_dct['Index']

        dct = gp_df.to_dict(orient='records')[0]        #convert to dictionary for some reason
        stop = int(dct['second'])                       #get the last second af gap
        start = stop - int(dct['delta']) +1             #get the first second of gap
        padded_line = f"{line}\t\t{point}\t\t\t{index}\t\t\t{start}\t\t{stop}\n"
        append_padded(padded_file,padded_line)

        if len(gp_df) >= 2:
            padded2 = gp_df.to_dict(orient='records')[1]
            stop2 = int(padded2['second'])
            start2 = stop2 - int(padded2['delta']) + 1
            padded_line2 = f"{line}\t\t{point}\t\t\t{index}\t\t\t{start2}\t\t{stop2}\n"
            append_padded(padded_file2,padded_line2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage {sys.argv[0]} serial number")
    else:
        serial_number = sys.argv[1]
        #padded_file = r"/home/geo2/Public/scr/zdmefr/02_SSD_help_tools/padded_nodes.txt"
        padded_file = r"/qc/06-ARAM/padding/padded_nodes.txt"
        padded_file2 = r"/qc/06-ARAM/padding/padded_nodes_2.txt"
        fdnav_file = r"/qc/06-ARAM/nav/Postplot_R/4dnav_lines/BR001522_4dnav.csv"
        bmp_sn_file = r"/qc/06-ARAM/parameters/AllMantaNodes_bumper_rsn.txt"
        main()

#!/usr/bin/python3

#built in modules import
import os
import re
import sys
from datetime import datetime

#side modules import
import pandas as pd

def read_repair_file(file_in):
    '''read repair file from instrumentation and return it in for of a list of lines'''
    with open(file_in, 'r', encoding = 'utf-8') as file:
        lines = [line.strip() for line in file.readlines()]
    return lines

def read_digest_file(file_in):
    '''read digest file and return it in form of pandas DataFrame'''
    if os.path.exists(file_in) and os.stat(file_in).st_size != 0:
        try:
            dgst_df = pd.read_csv(file_in, names = ["number","bumper","serial","unix_start","unix_stop","tm_start","tm_stop","path"])
            return(dgst_df)
        except (IOError, OSError) as exc:
            print(f"Something went wrong: {exc}")
    else:
        print(f"File: {file_in} doesn't exist or empty")
    
def from_unix(unix_time):
    '''convert unix time to string of format YYYY-MM-DD hh:mm:ss, e.g., 2023-06-05 13:31:23'''
    unix_time = datetime.utcfromtimestamp(int(unix_time))
    return datetime.strftime(unix_time,"%Y-%m-%d %H:%M:%S")
     
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


def main():
    ''' main function'''
    #search patterns below
    unix_time_pattern = "\d+"                                       #pattern to extract unix time from string
    out_pattern = "/dl\d/\w+/\w+/\d{4}-\d{2}-\d{2}/\w+.raw"         #pattern for auto raw file path search
    raw_pattern = "/dl\d/\w+/\d{4}-\d{2}-\d{2}/\w+.raw"             #pattern for repair raw file path search
    bumper_pattern = "\w+_\d{1,3}_\d{6}_b(\d+)_rsn(\d+)"            #pattern for extracting bumper and serial numbers from file name
    
    
    lines = read_repair_file(repair_file)
    
    #extract start and stop unix time
    start = [line for line in lines if line.startswith("Start second")][0]
    stop = [line for line in lines if line.startswith("Stop second")][0]
    stop_time = re.search(unix_time_pattern, stop).group(0)
    start_time = re.search(unix_time_pattern, start).group(0)
    
    #extract the initial and repair paths from file
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
   
    #merging path and checking if it exists
    ssd_path = os.path.join(os.path.split(out_path)[0],os.path.basename(raw_path))
    
    if os.path.exists(ssd_path):
        #get bumper from the raw file name
        bumper = re.search(bumper_pattern, os.path.basename(raw_path)).groups()[0]
        serial = re.search(bumper_pattern, os.path.basename(raw_path)).groups()[1]
        #print(bumper, serial)
        
        #check if the line is already in file
        with open(digest_file, 'r', encoding = 'utf-8') as file:
            lines = file.readlines()
            check_list = [line[6:].strip() for line in lines]
        check_line = f"{bumper},{serial},{start_time},{stop_time},{from_unix(start_time)},{from_unix(stop_time)},{ssd_path}"
        if check_line in check_list:
            print(f"{ssd_path} is already in {digest_file}")
        else:
            digest_df = read_digest_file(digest_file)
            seq_number = digest_df.number.max() + 1
            to_append = f"{seq_number},{bumper},{serial},{start_time},{stop_time},{from_unix(start_time)},{from_unix(stop_time)},{ssd_path}\n"
            print(f"The line below appended {os.path.basename(digest_file)}")
            print(to_append)
            with open(digest_file,'a', encoding='utf-8') as file:
                file.write(to_append)
    else:
        print(f"No such file {ssd_path}, please, copy first...")
        sys.exit(0)
    

if __name__ == "__main__":
    digest_file = r"/home/geo2/Public/scr/zdmefr/02_SSD_help_tools/DigestDownloads.csvManual"
    fdnav_file = r"/qc/06-ARAM/nav/Postplot_R/4dnav_lines/BR001522_4dnav.csv"
    #repair_file = r"/home/geo2/Public/scr/zdmefr/02_SSD_help_tools/Node_165.txt"
    if len(sys.argv) == 2:
        repair_file = sys.argv[1] 
        main()
    else:
        print("Please provide full path to repair file")

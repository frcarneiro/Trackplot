#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sys, os
import numpy as np
from colored import stylize, fg
import math
import datetime
from dataclasses import dataclass, field
import time
import pathlib
from typing import Callable, ClassVar, Dict, List, Optional, Tuple
from collections import defaultdict
import typing

##########################################################
#                     Looging Function                   #
##########################################################
def trackplot_logger(message: str, type: str = 'info', noprint: bool = False) -> None:
    if type == 'info':
        if noprint==False: print(message, flush=True) 
        logging.info(message.replace("\n", " ")) 
    elif type == 'warning':
        if noprint==False: print(stylize(f'WARNING: {message}', fg('#FFB000')), flush=True)
        logging.warning(message.replace("\n", " "))
    elif type == 'warning_exit':
        if noprint==False: print(stylize(f'WARNING: {message}', fg('#FFB000')), flush=True)
        logging.warning(message.replace("\n", " "))
        sys.exit()
    elif type == 'error':
        if noprint==False: print(stylize(f'ERROR: {message}', fg('#FE6100')), flush=True)
        logging.error(message.replace("\n", " "))      
    elif type == 'critical':
        if noprint==False: print(stylize(f'CRITICAL: {message}', fg('#FE6100')), flush=True)
        logging.critical(message.replace("\n", " "))
        sys.exit()
    elif type == 'critical_noexit':
        if noprint==False: print(stylize(f'CRITICAL: {message}', fg('#FE6100')), flush=True)
        logging.critical(message.replace("\n", " "))   
    elif type == 'success':
        if noprint==False: print(stylize(f'SUCCESS: {message}', fg('#648FFF')), flush=True)
        logging.info(message.replace("\n", " "))

class EndsWithFilter:
    def __init__(self, *patterns: typing.Iterable[str]):
        self.patterns = tuple(s.lower() for s in patterns)

    def __call__(self, src_path, *args, **kwargs):
        return src_path.lower().endswith(self.patterns)

##########################################################
#                     Timer Function                     #
##########################################################
# https://realpython.com/python-timer/
class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""

@dataclass
class Timer:
    timers: ClassVar[Dict[str, float]] = dict()
    name: Optional[str] = None
    text: str = "Elapsed time: {:0.4f} seconds"
    logger: Optional[Callable[[str], None]] = print
    _start_time: Optional[float] = field(default=None, init=False, repr=False)
    fsize: Optional[float] = np.nan
    gridsize: Optional[int] = np.nan
    probe: Optional[str] = None

    def __post_init__(self) -> None:
        """Add timer to dict of timers after initialization"""
        if self.name is not None:
            self.timers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None

        # Report elapsed time
        if self.logger:
            self.logger('|' + self.text.format(elapsed_time) + '|' + str(self.probe) + '|' + str(round(self.fsize, 1)) + '|' + str(self.gridsize))
        if self.name:
            self.timers[self.name] += elapsed_time

        return elapsed_time
    
##########################################################
#                   Progress bar GUI                     #
##########################################################
# adapt from https://www.pakstech.com/blog/python-gooey/
def print_progress(index: int, total: int) -> None:
    print(f"progress: {index+1}/{total}", flush=True)

def progressBar(index: int, ls: int) -> None:
    print_progress(index, len(ls)) # to have a nice progress bar in the GUI
    if index % math.ceil(len(ls)/10) == 0 and index != (len(ls) - 1): # decimate print
        print(f"Files Process: {index+1}/{len(ls)}", flush=True)
    if index == (len(ls) - 1):
        print(f"Files Process: {index+1}/{len(ls)}", flush=True)
        
##########################################################
#                   Others Function                      #
##########################################################      
#https://stackoverflow.com/questions/23581128/how-to-format-date-string-via-multiple-formats-in-python
def try_parsing_date(text: str) -> datetime.datetime:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%m/%d/%Y %H:%M', '%m-%d-%Y %H:%M'):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

# Julian Day # https://stackoverflow.com/questions/13943062/extract-day-of-year-and-julian-day-from-a-string-date
def dt2jd(dt: datetime.datetime) -> Tuple[str]:
    tt = dt.timetuple()
    jyear = str(tt.tm_year)
    jday = str(tt.tm_yday).zfill(3)
    time = str(tt.tm_hour).zfill(2) + ':' + str(tt.tm_min).zfill(2) + ':' + str(tt.tm_sec).zfill(2)
    jyearday = jyear + '-' + jday
    return jyearday, jyear, jday, time

# List file in subfolder with exclude
#  https://stackoverflow.com/questions/60266991/in-python-how-do-i-create-a-list-of-files-based-on-specified-file-extensions
def list_file(folder: pathlib.Path, ext: List[str], exclude: List[str], processed_list: List[pathlib.Path]) -> List[pathlib.Path]:
    ls = []      
    for root, dirs, files in os.walk(folder, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        for filename in files:
            if filename.lower().endswith(ext):                
                filepath = os.path.join(root, filename)             
                if os.stat(filepath).st_size == 0:
                    trackplot_logger(f'{filepath} is empty. Skip...', type='warning')
                elif filepath in processed_list:
                   pass
                else:            
                    ls.append(filepath)
    return ls

# Folder creation
def folder_creation(trackplot_output_folder: pathlib.Path, vessel_name: str) -> None:
    pass
    # # Folder for Logs and extra
    # folders = ['Concatenate_Raw','Processed\\Dock2Dock', 'Processed\\Dock2Dock\\Caris_Tide', 
    #            'Processed\\Dock2Dock\\SBP_Tide', 'Processed\\Dock2Dock\\Fugro_Seismic_Tide','Processed\\Report']
    # if tide_processing_method == 'Dock to Dock and Line by Line':
    #     foldersArea = ['Processed\\Tide']
    #     for folder in foldersArea:
    #         for area in unique_area:
    #             if not os.path.exists(os.path.join(tidde_output_folder, folder, str(project_name) + "_" + str(vessel_name) + "_" + str(area))):
    #                 os.makedirs(os.path.join(tidde_output_folder, folder, str(project_name) + "_" + str(vessel_name) + "_" + str(area)))
    # # Folders for all the processing data that will be created
    # for folder in folders:
    #     if not os.path.exists(os.path.join(tidde_output_folder, folder)):
    #         os.makedirs(os.path.join(tidde_output_folder, folder))


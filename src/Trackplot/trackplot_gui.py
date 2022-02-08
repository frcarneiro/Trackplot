#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##### trackplot packages #####
from trackplot_process import process, trackplot_prestart
from trackplot_gooey import make_gooey_config, trackplot_gui

##### GUI packages #####
from gooey import Gooey
import datetime
import sys

##########################################################
#                       Main code                        #
##########################################################
# this needs to be *before* the @Gooey decorator!
# (this code allows to only use Gooey when no arguments are passed to the script)
if len(sys.argv) >= 2:
    if not '--ignore-gooey' in sys.argv:
        sys.argv.append('--ignore-gooey')

#GUI Configuration
@Gooey(**make_gooey_config(program_name='trackplot'))
def main():
    args = trackplot_gui(mode='Normal') 
    arguments, list_proc, skip_list = trackplot_prestart(args, mode='Normal')   
    process(arguments, list_proc, skip_list)

if __name__ == "__main__":
    now = datetime.datetime.now() # time the process
    main()
    print('', flush=True)
    print("Process Duration: ", (datetime.datetime.now() - now), flush=True) # print the processing time. It is handy to keep an eye on processing performance.


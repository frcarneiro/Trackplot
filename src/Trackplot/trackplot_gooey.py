#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##### GUI packages #####
from argparse import Namespace
from gooey import GooeyParser

##### General packages #####
import os, json, csv
import pathlib
from dataclasses import dataclass

def make_gooey_config(program_name: str) -> dict:
    gooey_config = dict(
        program_name=program_name,
        #image_dir=local_resource_path('C:\\Users\\patrice.ponchant\\Documents\\GitHub\\magia\\src\\icons'),
        progress_regex=r"^progress: (?P<current>\d+)/(?P<total>\d+)$",
        progress_expr="current / total * 100",
        hide_progress_msg=True,
        richtext_controls=True,
        clear_before_run=True,
        #show_stop_warning=False, # NOTE Do not use
        #richtext_controls=True,
        terminal_font_family='Courier New',  # for tabulate table nice formatation
        default_size=(1280, 624),
        #fullscreen=True,
        timing_options={
            'show_time_remaining': True,
            'hide_time_remaining_on_complete': True
        },
        tabbed_groups=True,
        navigation='Tabbed',
        header_bg_color='#95ACC8',
        #body_bg_color = '#95ACC8',
    menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'trackplot',
                'description': 'Workflow Automation for trackplot MBES Data',
                'version': 'Cedric_beta_version',
                'copyright': '2021',
                'website': 'https://github.com/fugro/furgo.hurricane.seabed2030',
                'developer': 'eduardo.pogeto@fugro.com, fernando.carneiro@fugro.com, patrice.ponchant@fugro.com',
                }]
        },{
        'name': 'Help',
        'items': [{
            'type': 'Link',
            'menuTitle': 'Documentation',
            'url': ''
            }]
        }]
    )
    
    return gooey_config

def trackplot_gui(mode: str) -> Namespace:
    """ Use GooeyParser to build up the arguments we will use in our script
    Save the arguments in a default json file so that we can retrieve them
    every time we run the script.
    """
    stored_args = {}
    stored_vessels = []
        
    args_file = "./assets/config/trackplot-config-args.json"
    if os.path.isfile(args_file):
        with open(args_file) as data_file:
            stored_args = json.load(data_file)
    
    # NOTE: with open(visible_file) as data_file:  DO NOT USE -> crash CUBE.
    visible_file = open("./assets/config/trackplot-config-gui.json")
    stored_visible = json.load(visible_file)
    visible_file.close()
                 
    vessels_file = "./assets/config/trackplot-vessels-list.csv"
    if os.path.isfile(vessels_file):
        with open(vessels_file) as f:
            reader = csv.reader(f, delimiter=',')
            stored_vessels = ['{} - {}'.format(x[0], x[1]) for x in reader][1:]

    desc = "Workflow Automation for trackplot MBES Data"
    parser = GooeyParser(description=desc)  

    # Main Arguments
    mainopt = parser.add_argument_group('Main',
                                        description='Options to be used for the processing',
                                        gooey_options={'columns': 1})
    # RawData Arguments     
    mainopt.add_argument(
        'spl_folder',       
        metavar='SPL folder vessel', 
        help='This is the path where the SPL session.',
        default=stored_args.get('spl_folder'),
        widget='DirChooser',
        gooey_options={'visible': stored_visible.get('spl_folder')})  

    mainopt.add_argument(
        'nav_pattern',
        metavar='CRP Position File Name', 
        widget='TextField',
        default=stored_args.get('nav_pattern'),
        help='SPL position file.',
        gooey_options={'visible': stored_visible.get('nav_pattern')})

    mainopt.add_argument(
        'trackplot_output_folder',       
        metavar='Output Folder', 
        help='Destination of output files',
        default=stored_args.get('trackplot_output_folder'),
        widget='DirChooser',
        gooey_options={'visible': stored_visible.get('trackplot_output_folder')})
    mainopt.add_argument(
        'vessel_name',
        metavar='Vessel Name',
        help='This will be use for the folders naming convention.',
        default=stored_args.get('vessel_name'),
        choices=stored_vessels,
        gooey_options={'visible': stored_visible.get('vessel_name')})
    mainopt.add_argument(
        'project_id',       
        metavar='Shape file name', 
        help='Shape file name',
        default=stored_args.get('project_id'),
        widget='TextField',
        gooey_options={'visible': stored_visible.get('project_id')})
    mainopt.add_argument(
        'interval',       
        metavar='interval', 
        help='Interval to decimate point shapefile',
        default=stored_args.get('interval'),
        widget='TextField',
        gooey_options={'visible': stored_visible.get('interval')})
    
    args = parser.parse_args()
    
    # Store the values of the arguments so we have them next time we run
    with open(args_file, 'w') as data_file:
        # Using vars(args) returns the data as a dictionary
        json.dump(vars(args), data_file, indent=1)
    
    return args

@dataclass
class trackplotArguments:
    # Parameters
    spl_folder: pathlib.Path
    nav_pattern: str
    trackplot_output_folder: pathlib.Path
    vessel_name: str
    vessel_abbreviation: str
    project_id: str
    interval: int
    # Cascade
    #cascade_url: Optional[str] = None # NOTE: Future use

    @staticmethod
    def from_gooey_args(args: Namespace, mode: str):  
        return trackplotArguments(
            # Parameters
            spl_folder = pathlib.Path(args.spl_folder),
            nav_pattern = args.nav_pattern,
            trackplot_output_folder = pathlib.Path(args.trackplot_output_folder),
            vessel_name = args.vessel_name.split(" - ")[0],
            vessel_abbreviation = args.vessel_name.split(" - ")[1],
            project_id = args.project_id,
            interval = args.interval
            #cascade_url = args.cascadeUrl if 'cascadeUrl' in args else None
        )

import json
import configparser
import re
import os
import modules.scripts as scripts
import gradio as gr
import logging

from modules import processing, shared, images
from modules.processing import Processed, process_images, images
from modules.shared import opts, cmd_opts, state
from pathlib import Path


pth = scripts.basedir()
logfile = os.path.join(pth,'Defender.log')
testfile=os.path.join(pth, 'test.txt')

#Setup Logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler(logfile)
file_handler.setFormatter(log_format)
log.addHandler(file_handler)

def FindAndReplace(StringToReview,Replacements):
    TotalReplacements = 0
    for key, value in Replacements.items():
        (StringToReview, count) = re.subn(key, value, StringToReview)
        TotalReplacements = TotalReplacements + int(count)
    return StringToReview, TotalReplacements


def ReviewBlacklist(StringToReview,blacklist): #This works
    for words in blacklist:
        if re.search(words,StringToReview) != None:
            return True
    return False

def LoadConfig(): #How do I test if this works? Logging.
    #Load Options
    configfile = os.path.join(pth, 'config.ini')
    log.info(f'config is at {configfile}')
    blacklistfile=os.path.join(pth, 'blacklist.txt')
    log.info(f'blacklist is at {blacklistfile}')
    replacementfile=os.path.join(pth, 'replacements.ini')

    config_options = {}
    config = configparser.ConfigParser()
    config.read(configfile)
    select = {"True","False"}
    config_options = dict(config.items('DEFAULT'))
    config_options['UseBlacklist'] #stopped here

    #UseBlacklist = config['Default'].getboolean('UseBlacklist')
    #UseFindAndReplace = config['Default'].getboolean('UseFindAndReplace')
    #BlacklistBehavior = config['Default']['BlacklistBehavior']
    #AddToLog = config['Default'].getboolean('AddToLog')
    #CustomPrompt = config['Default']['CustomPrompt']

    #if configonly:
    #    return UseBlacklist, UseFindAndReplace, BlacklistBehavior

    #Load blacklist
    blacklist = []
    with open(blacklistfile,'r') as f: blacklist = f.read().splitlines()
    log.info(f'Loaded {len(blacklist)} items from blacklist')

    #Load Replacement pairs
    replace_dict = {}
    config.read(replacementfile)
    replace_dict = dict(config.items('Replacements'))
    log.info(f'Loaded {len(replace_dict)} replacements')

    return replace_dict, blacklist, config_options #UseBlacklist, UseFindAndReplace, BlacklistBehavior,AddToLog,CustomPrompt



class Script(scripts.Script):
    def title(self):
        return "DiffusionDefender"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self,is_img2img):
        with gr.Accordion("Diffusion Defender"):
            gr.Markdown("Diffusion Defender is Active")
        log.info('Defender loaded into UI')
        return

    def process(self,p):  #This block doesn't appear to be running? Had to change it to process.
        #replacements, blacklist, UseBlacklist, UseFindAndReplace, BlacklistBehavior, AddToLog, CustomPrompt = LoadConfig()
        replacements, blacklist, config_options = LoadConfig()
        TotalReplacements = 0
        BlacklistTripped = False

        prompt = p.prompt

        try:
            if config_options['UseBlacklist']:
                BlacklistTripped = ReviewBlacklist(prompt,blacklist)
        except Exception:
            log.error('Unable to reference prompt against blacklist')

        try:
            if config_options['UseFindAndReplace']:
                new_prompt,TotalReplacements = FindAndReplace(prompt,replacements)
                p.prompt = new_prompt
        except Exception:
            log.error('Unable to execute Find and Replace')

        #Logging
        try:
            if config['AddToLog'] and BlacklistTripped or TotalReplacements > 0:
                if BlacklistTripped:
                        log.info(f'BLACKLIST: {prompt}')
                if TotalReplacements > 0:
                        log.info(f'REPLACEMENTS: {prompt} <|> {new_prompt}')
        except Exception:
            log.error('Unable to add to log')

        BlacklistBehavior = config_options['BlacklistBehavior']
        try:
            if BlacklistTripped:
                if BlacklistBehavior == "StopProcessing":
                    p.batch_size = 1
                    stop = shared.state.skip()
                elif BlacklistBehavior == "ReturnBlank":
                    prompt = ""
                    p.batch_size = 1
                    stop = shared.state.skip()
                elif BlacklistBehavior == "ReturnPrompt":
                    p.prompt = CustomPrompt
                    p.batch_size = 1
                    processed = process_images(p)
                    return processed
                elif BlacklistBehavior == "LogOnly":
                    if not AddToLog:
                        log.info(f'BLACKLIST: {prompt}')
                    processed = process_images(p)
                    return processed
                    #continue and send prompt
                elif BlacklistBehavior == "NoAction":
                    processed = process_images(p)
                    return processed
                else:
                    logging.warning("ScriptName: BlacklistBehavior is not set in .ini file, defaulting to NoAction")
                    processed = process_images(p)
                    return processed
        except Exception:
            log.error('Unable to Enforce Blacklist Behavior')

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
from distutils.util import strtobool

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
        (ReviewedString, count) = re.subn(key, value, StringToReview.lower())
        TotalReplacements = TotalReplacements + int(count)
    if ReviewedString.lower() == StringtoReview.lower():
        ReviewedString = StringToReview
    return StringToReview, TotalReplacements


def ReviewBlacklist(StringToReview,blacklist): #This works
    result = False
    for words in blacklist:
        if re.search(words,StringToReview.lower()) != None:
            result = True
    return result

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

    config_options = dict(config.items('DEFAULT'))
    log.info(f'Config read as: {json.dumps(config_options)}')
    booloptions = ['useblacklist', 'usefindandreplace','addtolog']
    for option in booloptions:
        config_options[option] = bool(strtobool(config_options[option]))


    #UseBlacklist = config['Default'].getboolean('UseBlacklist')
    #UseFindAndReplace = config['Default'].getboolean('UseFindAndReplace')
    #BlacklistBehavior = config['Default']['BlacklistBehavior']
    #AddToLog = config['Default'].getboolean('AddToLog')
    #CustomPrompt = config['Default']['CustomPrompt']

    #if configonly:
    #    return UseBlacklist, UseFindAndReplace, BlacklistBehavior

    #Load blacklist
    blacklist = []
    if config_options['useblacklist']:
        with open(blacklistfile,'r') as f: blacklist = f.read().splitlines()
        log.info(f'Loaded {len(blacklist)} items from blacklist')

    #Load Replacement pairs
    replace_dict = {}
    if config_options['usefindandreplace']:
        config.read(replacementfile)
        replace_dict = dict(config.items('DEFAULT'))
        log.info(f'Loaded {len(replace_dict)} replacement pairs')

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
        new_prompt = ""

        try:
            if config_options['useblacklist']:
                BlacklistTripped = ReviewBlacklist(prompt,blacklist)
        except Exception as ex:
            log.error(f'Unable to reference prompt against blacklist: {type(ex)}')

        try:
            if config_options['usefindandreplace']:
                new_prompt,TotalReplacements = FindAndReplace(prompt,replacements)
                p.prompt = new_prompt
        except Exception:
            log.error('Unable to execute Find and Replace')

        #Logging
        try:
            if config_options['addtolog']:
                if BlacklistTripped:
                    log.info(f'BLACKLIST: {prompt}')
                if TotalReplacements > 0:
                    log.info(f'REPLACEMENTS: {prompt} <|> {new_prompt}')
        except Exception as ex:
            log.error(f'Unable to add to log: {ex=}, {type(ex)}')
            raise

        BlacklistBehavior = config_options['blacklistbehavior']
        try:
            if BlacklistTripped:
                if BlacklistBehavior == "StopProcessing":
                    p.batch_size = 1
                    #shared.state.interru()
                    log.debug('Ending Prompt')
                    shared.state.end()
                    return
                elif BlacklistBehavior == "ReturnBlank":
                    prompt = ""
                    p.batch_size = 1
                    p.prompt = prompt
                    log.debug('Replaced with blank prompt of empty string')
                    return
                elif BlacklistBehavior == "ReturnPrompt":
                    p.prompt = config_options['customprompt']
                    p.batch_size = 1
                    log.debug(f'Returned custom prompt of {p.prompt}')
                elif BlacklistBehavior == "LogOnly":
                    if not config_options['addtolog']:
                        log.info(f'BLACKLIST: {prompt}')
                    #continue and send prompt
                elif BlacklistBehavior == "NoAction":
                    log.debug('No Action Taken')
                else:
                    log.warning("ScriptName: BlacklistBehavior is not set in .ini file, defaulting to NoAction")
                #proc = process_images(p) Doesn't look like I need this?
                return p
        except Exception as ex:
            log.error(f'Unable to Enforce Blacklist Behavior: {ex=}, {type(ex)}')
            raise
            return

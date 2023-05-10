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

def find_and_replace(string_to_review, replacements):
    total_replacements = 0
    old_string, cur_string = string_to_review, string_to_review
    for k, v in replacements.items():
        (cur_string, count) = re.subn(k, v, cur_string.lower())
        total_replacements += int(count)
    if cur_string.lower() == old_string.lower():
        cur_string = old_string
    return cur_string, total_replacements


def ReviewBlacklist(StringToReview,blacklist): #This works
    result = False
    for words in blacklist:
        m = re.search(words,StringToReview.lower())
        if m != None:
            log.info(f'BLACKLIST WORD HIT: {m.group(0)}')
            result = True
    return result

def LoadConfig(configonly=False):
    #Load Options
    configfile = os.path.join(pth, 'config.ini')
    log.debug(f'config is at {configfile}')
    blacklistfile=os.path.join(pth, 'blacklist.txt')
    log.debug(f'blacklist is at {blacklistfile}')
    replacementfile=os.path.join(pth, 'replacements.ini')

    config_options = {}
    config = configparser.ConfigParser()
    config.read(configfile)

    config_options = dict(config.items('DEFAULT'))
    log.debug(f'Config read as: {json.dumps(config_options)}')
    booloptions = ['useblacklist', 'usefindandreplace','addtolog','showboxinui']
    for option in booloptions:
        config_options[option] = bool(strtobool(config_options[option]))
    if configonly:
        return config_options
    #Load blacklist
    blacklist = []
    if config_options['useblacklist']:
        with open(blacklistfile,'r') as f: blacklist = f.read().splitlines()
        log.debug(f'Loaded {len(blacklist)} items from blacklist')

    #Load Replacement pairs
    replace_dict = {}
    if config_options['usefindandreplace']:
        replace = configparser.ConfigParser()
        replace.read(replacementfile)
        replace_dict = dict(replace.items('DEFAULT'))
        log.debug(f'Loaded {len(replace_dict)} replacement pairs')

    return replace_dict, blacklist, config_options



class Script(scripts.Script):
    def title(self):
        return "DiffusionDefender"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self,is_img2img):
        config_options = LoadConfig(True)
        if config_options['showboxinui']:
            with gr.Accordion("Diffusion Defender"):
                gr.Markdown(config_options['customtextinuibox'])
                log.info('Defender loaded into UI')
        return

    def process(self,p):
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
                new_prompt,TotalReplacements = find_and_replace(prompt,replacements)
                p.prompt = new_prompt
                p.all_prompts[0] = new_prompt
        except Exception as ex:
            log.error(f'Unable to execute Find and Replace {ex=}, {type(ex)})')

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

        #Enforce Blacklist Behavior.
        BlacklistBehavior = config_options['blacklistbehavior']
        log.debug(f'BlacklistBehavior set for:{BlacklistBehavior}')
        try:
            if BlacklistTripped:
                if BlacklistBehavior == "StopProcessing":
                    p.batch_size = 1
                    p.n_iter = 1
                    log.debug('Ending Prompt')
                    shared.state.interrupt()
                    shared.state.end()
                elif BlacklistBehavior == "ReturnBlank":
                    prompt = ""
                    p.batch_size = 1
                    p.prompt, p.all_prompts[0] = prompt, prompt
                    p.n_iter = 1
                    log.debug('Replaced with blank prompt of empty string')
                elif BlacklistBehavior == "ReturnPrompt":
                    prompt = config_options['customprompt']
                    p.prompt, p.all_prompts[0] = prompt, prompt
                    p.batch_size = 1
                    p.n_iter = 1
                    log.debug(f'Returned custom prompt of {p.prompt}')
                elif BlacklistBehavior == "LogOnly":
                    if not config_options['addtolog']:
                        log.info(f'BLACKLIST: {prompt}')
                    #continue and send prompt
                elif BlacklistBehavior == "NoAction":
                    log.debug('No Action Taken')
                else:
                    log.warning("ScriptName: BlacklistBehavior is not set in .ini file, defaulting to NoAction")
                #return p
        except Exception as ex:
            log.error(f'Unable to Enforce Blacklist Behavior: {ex=}, {type(ex)}')
            raise
            #return

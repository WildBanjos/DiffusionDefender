import json
import configparser
import re
import os
import modules.scripts as scripts
import gradio as gr

from modules import processing, shared, images
from modules.processing import Processed, process_images, images
from modules.shared import opts, cmd_opts, state
from pathlib import Path


extension_dir = scripts.basedir()
logfile = os.path.join(extension_dir,'flagged_prompts.log')
configfile = os.path.join(extension_dir, 'config.ini')
blacklistfile=os.path.join(extension_dir, 'blacklist.txt')
replacementfile=os.path.join(extension_dir, 'replacements.ini')
testfile=os.path.join(extension_dir, 'test.txt')


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

def LoadConfig(config,configonly=False): #How do I test if this works?
    #Load Options
    config = configparser.ConfigParser()
    config.read(configfile)
    UseBlacklist = config.getboolean('Default','UseBlacklist')
    UseFindAndReplace = config.getboolean('Default','UseFindAndReplace')
    BlacklistBehavior = config['Default']['BlacklistBehavior']
    AddToLog = config.getboolean('Default','AddToLog')
    CustomPrompt = config['Default']['CustomPrompt']

    #if configonly:
    #    return UseBlacklist, UseFindAndReplace, BlacklistBehavior

    #Load blacklist
    blacklist = None
    with open(blacklistfile,'r') as f: blacklist = f.read().splitlines()
    with open(testfile, 'w'), as f: f.write(f'Loaded blacklist: {blacklist[0]}')

    #Load Replacement pairs
    config.read(replacementfile)
    replace_dict = {}
    replace_dict = dict(config.items('Replacements'))

    return replace_dict, blacklist, UseBlacklist, UseFindAndReplace, BlacklistBehavior,AddToLog,CustomPrompt

class Script(scripts.Script):
    def title(self):
        return "DiffusionDefender"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self,is_img2img):
        with gr.Box():
            gr.Markdown("Diffusion Defender is Active")
        return

    def run(self,p):
        #Main
        replacements, blacklist, UseBlacklist, UseFindAndReplace, BlacklistBehavior, AddToLog, CustomPrompt = LoadConfig()
        TotalReplacements = 0
        BlacklistTripped = False

        prompt = p.prompt
        try:
            if UseBlacklist:
                BlacklistTripped = ReviewBlacklist(prompt,blacklist)
        except:
            print('Unable to reference prompt against blacklist')

        try:
            if UseFindAndReplace:
                new_prompt,TotalReplacements = FindAndReplace(prompt,replacements)
                p.prompt = new_prompt
        except:
            print('Unable to execute Find and Replace')

        #Logging
        try:

            if AddToLog and BlacklistTripped or TotalReplacements > 0:
                with open(logfile, 'a') as l:
                    if BlacklistTripped:
                            LogFile.write(f'BLACKLIST: {prompt} \n')
                    if TotalReplacements > 0:
                            LogFile.write(f'REPLACEMENTS: {prompt} <|> {new_prompt} \n')
                    LogFile.close()
        except:
            print('Unable to add to log')

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
                        with open(logfile, 'a') as l:
                            l.write(f'BLACKLIST: {prompt} \n')
                            LogFile.close()
                    processed = process_images(p)
                    return processed
                    #continue and send prompt
                elif BlacklistBehavior == "NoAction":
                    processed = process_images(p)
                    return processed
                else:
                    print("ScriptName: BlacklistBehavior is not set in .ini file, defaulting to NoAction")
                    processed = process_images(p)
                    return processed
        except:
            print('Unable to Enforce Blacklist Behavior')

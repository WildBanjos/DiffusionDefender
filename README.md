# DiffusionDefender
An extension for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) that adds a blacklist feature for administration.

This extension is mainly designed for users running a private or semi-public instance of the repo who want to ensure the safety of submitted prompts. Users can define a list of terms which each and every prompt is checked against. If a prompt is found to contain blacklisted terms, it will be processed as determined by your config file. Potential actions include

# A non-stance on appropriateness
I want to note that this extension is not intended to enforce a certain morality, be prudish, or make any claims about what constitutes an "inappropriate prompt." While the creator of this extension may have had certain types of prompts in mind when designing it, there is no pre-defined blacklist included in the extension. Blacklisting is a necessary moderation technique for any modern service. There may be a variety of situations in which an administrator would want to use a blacklist to prevent specific terms from being submitted for processing. It is up to the administrator to determine what blacklist is appropriate for their specific use case

## Features
- Read incoming prompts and check against a blacklist
- Define the method of enforcement if a prompt contains a blacklist term.
    - Block processing of image
    - Replace prompt with empty string
    - Replace prompt with custom string
    - Only log the offending prompt
    - Take no action
- Run a custom find and replace on all incoming prompts.

## Installation and Configuration
To install this extension, follow these steps:

1. Clone the repo into the Extensions Directory
    git clone https://github.com/WildBanjos/DiffusionDefender.git
2. Configure config.ini
3. Configure blacklist.txt and replacements.ini as needed

##ToDo
- Add option to block loading of extension tab.

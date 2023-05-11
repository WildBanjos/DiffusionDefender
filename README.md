# DiffusionDefender
An extension for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) that adds a blacklist feature for administration.

This extension is mainly designed for users running a private or semi-public instance of the repo who want to ensure the safety of submitted prompts. Users can define a list of terms which each and every prompt is checked against. If a prompt is found to contain blacklisted terms, it will be processed as determined by your config file.


## Features
- Read incoming prompts and check against a blacklist
- Define the method of enforcement if a prompt contains a blacklist term.
    - Block processing of image
    - Replace prompt with empty string
    - Replace prompt with custom string
    - Only log the offending prompt
    - Take no action
- Run a custom find and replace on all incoming prompts.

## Installation
To install this extension, follow these steps:

1. Clone the repo into the Extensions Directory

        git clone https://github.com/WildBanjos/DiffusionDefender.git
2. Configure config.ini
3. Configure blacklist.txt and replacements.ini as needed. Samples are provided in the files.
4. Extension is ready to use

## Configuration
### Blacklist.txt
The blacklist.txt file is easy to configure. On each new line, enter one term or phrase you would like to blackist. 
There is no need to separate terms with a comma or enclose them in quotes. Please be sure to delete the default sample text before adding your list.

Note that the function does not separate by word and may capture other words that contain your blacklisted term. 
For example a blacklisted term of "red" will also block "redmond" or "predict". If you believe this is happening, 
double-check your defender.log file. To remedy this, wrap the expression into "([^\w+]|^)your expression([^\w+]|$)" 
without the quotes. Ex: "([^\w+]|^)red([^\w+]|$)". You do not need to add this by default to all terms.

As suggested by the previous note, regular expressions are allowed in the blacklist. 
However, they have not been thoroughly tested yet and may break things.

### replacements.ini
To configure replacement values, please enter *find:replace* pairs in the replacements.ini file. For example, the replacement pair "blue:red" will replace all instances of the word "blue" with the word "red". As mentioend in the previous section, this may lead to overzealous replacements. This may be solved in a similar way by adding the regular expression tag as noted above. 
## ToDo
- Add option to block loading of extension tab.
- Expand instructions

## This is only a tool, nothing more.
I want to note that this extension is not intended to enforce a certain morality, be prudish, or make any claims about what constitutes an "inappropriate prompt." While the creator of this extension may have had certain types of prompts in mind when designing it, there is no pre-defined blacklist included in the extension. Blacklisting is a necessary moderation technique for any modern service. There may be a variety of situations in which an administrator would want to use a blacklist to prevent specific terms from being submitted for processing. It is up to the administrator to determine what blacklist is appropriate for their specific use case

## Links to various wordlists
Please note that the below lists were simply found online. They are not curated or managed by me. As mentioned, they are not intended to bias or enforce a certain use case or morality.

Please feel free to open a PR with additional wordlist suggestions.

- [Swears](http://www.bannedwordlist.com/lists/swearWords.txt)
- [Banned by Google](https://github.com/coffee-and-fun/google-profanity-words/blob/main/data/list.txt)

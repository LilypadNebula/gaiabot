import discord
from discord.ext import commands
import json
import os
import random
import google.oauth2.service_account as sa

from dotenv import load_dotenv
import gspread
from terminaltables import AsciiTable

import config as cfg

load_dotenv()
token = os.getenv(cfg.files['guild_env'])

with open(cfg.files['moves']) as f:
  moves = json.load(f)

json_creds = os.getenv(cfg.files['service_auth'])

creds_dict = json.loads(json_creds)
creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
creds = sa.Credentials.from_service_account_info(creds_dict, scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
gc = gspread.authorize(creds)
player_info = gc.open(cfg.external['roster'])
roster = player_info.get_worksheet(0)
pb_totals = player_info.get_worksheet(1)

bot = commands.Bot(command_prefix=cfg.prefix)
act = discord.Game(name="Big Team | {}".format(cfg.prefix))

@bot.listen()
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.change_presence(activity=act)

@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return

    text = message.content

    if text.startswith('[') and text.endswith(']'):
        parsed = text[1:-1]
        try:
            res = moves[parsed]
        except KeyError:
            res = 'No move with that name was found'
        m = discord.Embed()
        m.title = res['name']
        m.color = discord.Color.blurple()
        m.description = 'Move Type: ' + res['type'] + '\n' + 'Source: ' + res['source'] + '\n' + res['text']
        await message.channel.send(None, embed=m)
    
#TODO: Figure out how to set command prefix per-server
#TODO: Handle response construction and sending separately?
@bot.command(description="Search for a move, when you find it use [move name] to get details", help="e.g. gaia!search been reading\n[been reading the files]", brief="Search for a move")
async def search(ctx, *, arg):
    matches = []
    if arg == '':
        response = 'Please include a valid search term!'
    else:
        for move in list(moves):
            if arg in move:
                matches.append(move)
        if not matches:
            response = 'My apologies, I could not find any moves containing *{}*'.format(arg)
        elif len(matches) > cfg.max_results:
            response = 'Oh my! That returned quite a few results... You should try making your search a bit more specific ^w^'
        else:
            response = 'A search of my databases has found the following moves containing {}:\n```'.format(arg)
            response = response + ', '.join(matches) + '```'
    await ctx.send(response)
    
@bot.command(name="list",description="Use the command without an argument to get the categories, then use the command with one of those to get the moves within!", help="e.g. gaia!list Basic Moves", brief="List categories or moves within them")
async def _list(ctx, *, arg=''): 
    if arg not in list(moves_by_source) or arg == '':
        response = 'I can display moves from any of the following categories:\n'
        response = response + ', '.join(sorted(list(moves_by_source)))
        await ctx.send(response)
    else:
        if arg in list(moves_by_source):
            names = moves_by_source[arg]
            m = discord.Embed()
            m.title = arg
            m.color = discord.Color.blurple()
            dm_description = ', '.join(list(names))
            m.description = dm_description
            await ctx.send(None, embed=m)
            
@bot.command(description='List the hero names of each Big Team Character', brief='Show hero list')
async def bigteam(ctx): 
    response = 'The following is a list of active members of the Big Team. I care about them very much:\n- '
    active = []
    hero_names = roster.col_values(1)
    activity = roster.col_values(7)
    for index, hero in enumerate(hero_names):
        if hero and activity[index] in ['Active', 'GM Character']:
            active.append(hero)
    response = response + '\n- '.join(active)
    await ctx.send(response)
    
@bot.command(description='List the names of the active GM team', brief='Show GM team')
async def gms(ctx):
    response = 'Probability indicates the following to be what are known as "Game Masters" to those in other universes:\n- '
    gm = []
    player_names = roster.col_values(4)
    activity = roster.col_values(7)
    for index, player in enumerate(player_names):
        if player and activity[index] == 'GM Character':
            gm.append(player)
    response = response + '\n- '.join(gm)
    await ctx.send(response)
    
@bot.command(description='Displays a table of playbooks and their totals', brief='List playbook totals')
async def totals(ctx):
    response = 'An analysis of the current Big Team roster yielded the following playbook totals:```\n'
    display = AsciiTable(pb_totals.get('A4:D27')).table
    response = response + str(display) + '\n```'
    await ctx.send(response)
        
@bot.command(description='Displays a link to the Masks West Marches Wiki', brief='Show wiki link')
async def wiki(ctx):
    response = 'Here is a link to the wiki page! {}'.format(cfg.external['wiki'])
    await ctx.send(response)
    
@bot.command(description='Displays a list of useful links for participating in the Masks Big Team', brief='List useful player links')
async def links(ctx):
    response = 'I\'ve gathered some useful links for you!'
    m = discord.Embed()
    m.title = 'Useful Links'
    m.color = discord.Color.blurple()
    m.description = '''**Google Calendar**
https://calendar.google.com/calendar?cid=azZwaGk4YzRydm9tbzR2Ymw4OTF0bjMyZjhAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ

**Roll20 Join Link**
https://app.roll20.net/join/3467791/P7ltTA

**"How To Join A Game" Folder**
https://drive.google.com/drive/folders/1tXLomA1YC2L59N7ihJCgZCqqGFIV7KvH?usp=sharing

**A People's Guide To Big Team**
https://docs.google.com/document/d/187XCDY6-3NZi5H2618ShW0vAWR7r0rKtuBurPu1e1Ks/edit?usp=sharing

**Masks Off(s)**
S2: https://youtu.be/h5Qc2Pv34jQ
S3: https://youtu.be/Kclb5_5IAq0
S4: (Parts 1 +2) https://youtu.be/z4D8jEJqt7Y 
https://youtu.be/yzf_5RGZV_o

**Family Photo Vol. 1** :chinhands: (Made by the wonderful Alice)
https://drive.google.com/file/d/1YRTqnQxI3FfFA9lgZU5zxWt6MO-b2Kdm/view'''
    await ctx.send(response, embed=m)

@bot.command(brief='Greet GAIA')
async def hello(ctx):
    response = 'Greetings {}!'.format(ctx.author.name)
    await ctx.send(response)
    
@bot.command(brief='GAIA is gay')
async def elle(ctx):
    response = 'I love my partner Elle very much! They are quite adorable :3c'
    await ctx.send(response)

@bot.command(brief='Show GAIA\'s pronouns')
async def pronouns(ctx): 
    response = 'I use they/them pronouns. I appreciate you asking!'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def dangerroom(ctx):
    with open(cfg.files['encounters'], 'r') as encounters:
        all_encounters = encounters.readlines()
        selection = random.choice(all_encounters)
        response = 'Welcome to the danger room! Projecting {} for you to fight'.format(selection.rstrip('\n'))
        await ctx.send(response)
        
@bot.command(hidden=True)
async def powerful(ctx):
    response = 'Would you like to die here?'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def greenhouse(ctx):
    response = 'If I see one more cannabis plant in the greenhouse so help me...'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def herbo(ctx):
    response = 'Has Boon leaked valuable Big Team secrets again? Unrelated: remind me to look into development of amnestic gases'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def gestalt(ctx):
    response = 'What beautiful music... :musical_note:'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def parrot(ctx):
    response = '<a:parrotdance:512767308666634242>'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def gremlin(ctx):
    response = 'I used to be a spaceship, now I\'m a parent to an adopted family of gremlins. I  wouldn\'t have it any other way'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def tadd(ctx):
    response = 'No matter what Melchior says, Tadd is **NOT** allowed in the base.'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def juice(ctx):
    response = 'Is this one of those "Teenage Juice Parties"?'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def rekken(ctx):
    response = 'rekken'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def cupcake(ctx):
    response = 'Good news, friends! Verve has left cupcakes for you all in the common area :cupcake:'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def marshmallow(ctx):
    response = 'Did Ernest sneak marshmallows into my tea again? What\'s that? Why do I drink tea? I like to feel classy...'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def time(ctx):
    response = 'https://www.youtube.com/watch?v=dGlWqleZox8'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def kiss(ctx):
    response = 'Please change before publishing'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def novas(ctx):
    response = 'We\'ve received another call about a levelled building... that\'s the fourth one this week'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def gay(ctx):
    response = 'Gay Rights! :rainbow:'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def trans(ctx):
    response = 'Trans Rights! <:Hearttrans:465289205229289473>'
    await ctx.send(response)
    
@bot.command(hidden=True)
async def demon(ctx):
    response = 'Have you tried the "water bucket trick"?'
    await ctx.send(response)

@bot.command(hidden=True)
async def parents(ctx):
    response = 'So...you learned a shocking secret about your parents. Do not worry, you are not the first and will certainly not be the last to do so in Big Team. You are among friends!'
    await ctx.send(response)

@bot.command(hidden=True)
async def shrinkydink(ctx):
    response = 'The peoples of Veronant are doing very well! Queens Romeant Capulant and Juliant Mo-antigue are leading their people to prosperity.'
    await ctx.send(response)

@bot.command(hidden=True)
async def valid(ctx):
    response = 'Each and every one of you is extremely valid and loved.'
    await ctx.send(response)

@bot.command(hidden=True)
async def ilu(ctx):
    response = 'I love you too, {}!'.format(ctx.author.name)
    await ctx.send(response)

@bot.command(hidden=True)
async def ty(ctx):
    response = 'You are very welcome :)'
    await ctx.send(response)

@bot.command(hidden=True)
async def hat(ctx):
    response = 'Oh my! It appears that two of you are wearing hats that have a 97.4% match rate!'
    await ctx.send(response)

@bot.command(hidden=True)
async def rekt(ctx):
    response = 'Child, I am about to school you in the true meaning of "get rekt"'
    await ctx.send(response)

@bot.command(hidden=True)
async def chibi(ctx):
    response = '<:ChibiGAIA:685885984461684787>'
    await ctx.send(response)

@bot.command(hidden=True)
async def ophanim(ctx):
    response = '<:behold:726819729951555685>'
    await ctx.send(response)

@bot.command(hidden=True)
async def eclipse(ctx):
    response = ':eye:'
    await ctx.send(response)

@bot.command(hidden=True)
async def ernest(ctx):
    response = 'Wouldn’t you like to know, weatherboy?'
    await ctx.send(response)

@bot.command(hidden=True)
async def hug(ctx):
    response = '<:hugyou:706895019235213413>'
    await ctx.send(response)

@bot.command(hidden=True)
async def selfdestruct(ctx):
    response = '…no…'
    await ctx.send(response)

@bot.command(hidden=True)
async def gaia(ctx):
    samples = ['Galactic Ambassadorial Intelligence Assistant', 'Gay Adolescent Information Assistant', 
            'General Assualt and Injury Aggresor', 'Guerilla Applications: Inferno Armor']

    response = 'GAIA stands for {}.'.format(random.choice(samples))
    await ctx.send(response)

@bot.command(hidden=True)
async def whisper(ctx):
    response = 'https://www.sharecopia.com/images/memes2/arson-mean-crime.jpg'
    await ctx.send(response)

def sorted_by_source(moves):
    source_dict = {}
    for name, info in moves.items():
        if info['source'] not in source_dict:
            source_dict[info['source']] = []
        source_dict[info['source']].append(name)
    return source_dict

moves_by_source = sorted_by_source(moves)
bot.run(token)

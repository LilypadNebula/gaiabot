# python built-in
import atexit
import json
import os
import pickle
import random
import string

# external
import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.oauth2.service_account as sa
import gspread
import matplotlib.pyplot as plt
from PIL import Image, ImageFont, ImageDraw
from terminaltables import AsciiTable
import textwrap

# local
import config as cfg

random.seed()
load_dotenv()

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

try:
    hist = pickle.load(open(cfg.files['hist'], 'rb'))
    print('Load of {} succesful'.format(cfg.files['hist']))
except:
    print('Unable to load Histogram, generating new dictionary')
    hist = dict.fromkeys(range(101), 0)
    
with open(cfg.files['moves']) as f:
    moves = json.load(f)

token = os.getenv(cfg.files['bot_token'])
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
        parsed = parsed.translate(str.maketrans('', '', string.punctuation))
        parsed = parsed.lower()
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
    if arg.title() not in list(moves_by_source) or arg == '':
        response = 'I can display moves from any of the following categories:\n'
        response = response + ', '.join(sorted(list(moves_by_source)))
        await ctx.send(response)
    else:
        if arg.title() in list(moves_by_source):
            names = moves_by_source[arg.title()]
            m = discord.Embed()
            m.title = arg.title()
            m.color = discord.Color.blurple()
            dm_description = ', '.join(list(names))
            m.description = dm_description
            await ctx.send(None, embed=m)
            
@bot.command(description='List the hero names of each Big Team Character', brief='Show hero list')
async def bigteam(ctx): 
    response = 'The following is a list of active members of the Big Team. I care about them very much:\n- '
    active = grab_by_type(1, ['Active', 'GM Character'])
    response = response + '\n- '.join(sorted(active))
    await ctx.send(response)
    
@bot.command(description='List the names of the active GM team', brief='Show GM team')
async def gms(ctx):
    response = 'Probability indicates the following to be what are known as "Game Masters" to those in other universes:\n- '
    gm = grab_by_type(4, ['GM Character'])
    response = response + '\n- '.join(sorted(gm))
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

**Current Player Roster**
https://docs.google.com/spreadsheets/d/13YSKZdPtjm60OxiU2TR9JSaNC2SGn3BYPuqrAV-IrSQ/edit#gid=0

**A People's Guide To Big Team**
https://docs.google.com/document/d/187XCDY6-3NZi5H2618ShW0vAWR7r0rKtuBurPu1e1Ks/edit?usp=sharing

**Player Character PC and NPC Relationships Page** (BROKEN AND UNDER CONSTRUCTION)
https://docs.google.com/spreadsheets/d/1cdMMKthB_8g9Bkjwv6BlsGUaNoNTgzuHTDEVNhk2VXw/edit?usp=sharing

**Masks Off(s)**
S2: https://youtu.be/h5Qc2Pv34jQ
S3: https://youtu.be/Kclb5_5IAq0
S4: (Parts 1 +2) https://youtu.be/z4D8jEJqt7Y 
https://youtu.be/yzf_5RGZV_o'''
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
async def thembo(ctx):
    response = 'Has ~~Boon~~ Amaranth leaked valuable ~~Big~~ GM Team secrets again? Unrelated: remind me to look into development of amnestic gases'
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
    response = 'You are quite welcome, {}! Please do not hesitate to get in touch again.'.format(ctx.author.name)
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
    response = ':eyes: :eyes: :eyes: :eyes: :eyes: :eyes:'
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
            'General Assualt and Injury Aggresor', 'Guerilla Applications: Inferno Armor', 'Girls Are Incredibly Attractive']

    response = 'GAIA stands for {}.'.format(random.choice(samples))
    await ctx.send(response)

@bot.command(hidden=True)
async def whisper(ctx):
    await ctx.send(file=discord.File('images/whisper.jpg'))

@bot.command(hidden=True)
async def aman(ctx):
    await ctx.send(file=discord.File('images/aman.gif'))


@bot.command(hidden=True,aliases=['pumpkin'])
async def halloween(ctx):
    await ctx.send(file=discord.File('images/halloween.gif'))

@bot.command(hidden=True)
async def jackal(ctx, *, arg=''):
    if arg == '':
        addressee = ctx.author.name
    else:
        addressee = arg
    draw_text('images/jackal.png', cfg.jackal['outfile'], addressee, cfg.jackal['x'], cfg.jackal['y'], cfg.jackal_font)
    await ctx.send(file=discord.File(cfg.jackal['outfile']))

@bot.command(hidden=True)
async def x(ctx):
    await ctx.send(file=discord.File('images/xtodoubt.png'))

@bot.command(hidden=True)
async def y(ctx):
    await ctx.send(file=discord.File('images/ytomedicine.png'))

@bot.command(hidden=True)
async def lesbians(ctx):
    response = 'Are you winning, lesbians? <:Heartlesbian:563154255712878603>'
    await ctx.send(response)

@bot.command(hidden=True)
async def focus(ctx):
    response = 'Focus, I have access to the search history of the Big Base PC’s and I don’t believe Savior would appreciate this objectification.'
    await ctx.send(response)

@bot.command(hidden=True)
async def australia(ctx):
    response = 'Trapped in Australia without a passport? Sounds like a you problem.'
    await ctx.send(response)

@bot.command(hidden=True)
async def disaster(ctx):
    response = 'Attention Big Team! A giant cat is attacking the Eiffel Tower <:Disaster:685884102456377362>'
    await ctx.send(response, file=discord.File('images/disaster_paris.png'))

@bot.command(hidden=True)
async def cake(ctx):
    await ctx.send(file=discord.File('images/cake.jpg'))

@bot.command(hidden=True)
async def seb(ctx):
    response = 'Where is Seb? A more accurate query is “When is Seb”'
    await ctx.send(response)

@bot.command(hidden=True)
async def ellen(ctx):
    ellens = ["armadillo Ellen", "medieval Ellen", "cybergoth Ellen", "zoomer Ellen", "wild west Ellen", "slightly shorter than normal Ellen", "hipster Ellen",
                "eye of Horus Ellen", "demon Ellen", "vampire Ellen", "cat Ellen", "dog Ellen", "prep Ellen", "theater Ellen", "cheerleader Ellen", "mecha pilot Ellen", 
                "robo-Ellen 3000", "angel Ellen", "1400's ellen", "pirate Ellen"]
    forecasts = ['a pack of 2 dozen Ellens has been spotted biking through the downtown area, led by {}. Expect traffic disruptions and loud music.',
                 'there\'s been a disturbance at the mall as {} has started a brawl over Tay\'s new costume.',
                 'a gang of Ellen\'s led by {} has been seen roaming the High School and pushing people into lockers']
    response = 'Today’s Ellen forecast: {}'.format(random.choice(forecasts).format(random.choice(ellens)))
    await ctx.send(response)

@bot.command(hidden=True)
async def amy(ctx):
    response = 'Amy, or Amaranth, developed this interesting new interface for you to send me messages! It was so nice of hir! Thank you, Amaranth!'
    await ctx.send(response)

@bot.command(hidden=True)
async def alice(ctx):
    response = 'Alice drew this portrait of me, isn\'t it wonderful? I believe it makes me look rather dashing. Thank you, Alice!'
    await ctx.send(response)

@bot.command(hidden=True)
async def cyclone(ctx):
    response = 'Though Cyclone did not physically spawn any current members of Big Team, we consider him to be a father figure to all of us. Yay for Mayor Crossover!'
    await ctx.send(response)

@bot.command(hidden=True)
async def atlanta(ctx, *, arg=None):
    if arg=='show':
        plt.bar(list(hist.keys()), hist.values(), color='g')
        plt.xlabel('Gambite Chance (%)')
        plt.ylabel('Occurences')
        plt.title('Atlanta Gambite membership likelihood')
        plt.savefig(cfg.plot['outfile'])
        await ctx.send(file=discord.File(cfg.plot['outfile']))
    else:
        chance = random.randrange(101)
        if not hist[chance]:
            hist[chance] = 1
        else:
            hist[chance] += 1
        response = 'By my calculations there is a {}\% chance that Atlanta is a member of GAMBITE'.format(chance)
        await ctx.send(response)

@bot.command(hidden=True)
async def gambite(ctx):
    response = 'The extra \'e\' really sets off my autocorrect module'
    await ctx.send(response)

@bot.command(hidden=True)
async def gn(ctx):
    response = 'Sleep tight {}!'.format(ctx.author.name)
    await ctx.send(response)

@bot.command(hidden=True)
async def og(ctx):
    await ctx.send(file=discord.File('images/knowvergrowth.png'))

@bot.command(hidden=True,aliases=['signal'])
async def bolt(ctx):
    await ctx.send(file=discord.File('images/bolt.png'))

@bot.command(hidden=True)
async def cadenza(ctx):
    await ctx.send(file=discord.File('images/cadenza.gif'))

@bot.command(hidden=True)
async def lily(ctx):
    response = 'Have you met Lily? She\'s wonderful!! And a very talented programmer'
    await ctx.send(response)

@bot.command(hidden=True)
async def rise(ctx):
    await ctx.send(file=discord.File('images/rise.png'))

@bot.command(hidden=True)
async def kurt(ctx, *, arg=None):
    if not arg:
        addressee = ctx.author.name
    else:
        addressee = arg
    await ctx.send('{} sold me weed.'.format(addressee))

@bot.command(hidden=True)
async def pikachu(ctx):
    await ctx.send(file=discord.File('images/pikachu.gif'))

@bot.command(hidden=True)
async def shade(ctx):
    await ctx.send(file=discord.File('images/shade.png'))

@bot.command(hidden=True,aliases=['nya'])
async def nyah(ctx):
    await ctx.send(file=discord.File('images/nyah.jpg'))

@bot.command(hidden=True)
async def whiz(ctx):
    await ctx.send(file=discord.File('images/whiz.png'))

@bot.command(hidden=True)
async def space(ctx):
    await ctx.send('Time is... fucked and space is... kinky?')

@bot.command(hidden=True)
async def toni(ctx):
    await ctx.send('Receiving a message from Big Team Fan Club for you: “Keep it up, {}! You’re grrrrand!”'.format(ctx.author.name))

@bot.command(hidden=True)
async def lavish(ctx, *, arg=None):
    samples = os.listdir('images/lavish_memes')
    if not (arg and arg.isdigit() and int(arg)-1 in range(len(samples))):
        filename = random.choice(samples)
    else:
        filename = samples[int(arg)-1]
    await ctx.send(file=discord.File('images/lavish_memes/{}'.format(filename)))

@bot.command(hidden=True)
async def draw25(ctx, *, arg):
    lines = textwrap.wrap(arg, cfg.draw['width'])
    text = '\n'.join(lines[:cfg.draw['lines']])
    draw_text('images/draw25.png', cfg.draw['outfile'], text, cfg.draw['x'], cfg.draw['y'], cfg.draw_font)
    await ctx.send(file=discord.File(cfg.draw['outfile']))

def grab_by_type(col, types):
    output = []
    names = roster.col_values(col)
    activity = roster.col_values(cfg.external['activity_col'])
    for index, name in enumerate(names):
        if name and activity[index] in types:
            output.append(name)
    return output

def draw_text(img_name, dest, text, x, y, text_cfg):
    img = Image.open(img_name)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(text_cfg['set'], text_cfg['size'])
    draw.text((x, y), text, tuple(text_cfg['color']), font=font)
    img.save(dest)

def save_hist():
    print('Shutting down, dumping histogram to {}'.format(cfg.files['hist']))
    pickle.dump(hist, open(cfg.files['hist'], 'wb'))

def sorted_by_source(moves):
    source_dict = {}
    for name, info in moves.items():
        if info['source'] not in source_dict:
            source_dict[info['source']] = []
        source_dict[info['source']].append(name)
    return source_dict

moves_by_source = sorted_by_source(moves)
atexit.register(save_hist)
bot.run(token)
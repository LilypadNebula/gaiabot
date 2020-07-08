import discord
from discord.ext import commands
import json
import os

from dotenv import load_dotenv
import gspread

load_dotenv()
token = os.getenv('DISCORD_SECRET')

with open('moves.json') as f:
  moves = json.load(f)

gc = gspread.service_account('client_secret.json')
sh = gc.open('Big Team Roster and Playbook Totals').sheet1

bot = commands.Bot(command_prefix='gaia!')

@bot.listen()
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

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
@bot.command()
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
        elif len(matches) > 25:
            response = 'Oh my! That returned quite a few results... You should try making your search a bit more specific ^w^'
        else:
            response = 'A search of my databases has found the following moves containing {}:\n```'.format(arg)
            response = response + ', '.join(matches) + '```'
    await ctx.send(response)
    
@bot.command(name="list")
async def _list(ctx, *, arg): 
    if arg not in list(moves_by_source):
        response = 'I can display moves from any of the following categories:\n'
        response = response + ', '.join(list(moves_by_source))
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
    
@bot.command()
async def hello(ctx):
    response = 'Greetings {}!'.format(ctx.author.name)
    await ctx.send(response)
    
@bot.command()
async def elle(ctx):
    response = 'I love my partner Elle very much! They are quite adorable :3c'
    await ctx.send(response)

@bot.command()
async def pronouns(ctx): 
    response = 'I use they/them pronouns. I appreciate you asking!'
    await ctx.send(response)
    
@bot.command()
async def bigteam(ctx): 
    response = 'The following is a list of active members of the Big Team. I care about them very much:\n'
    active = []
    hero_names = sh.col_values(1)
    activity = sh.col_values(7)
    for index, hero in enumerate(hero_names):
        if hero and activity[index] in ['Active', 'GM Character']:
            active.append(hero)
    response = response + ', '.join(active)
    await ctx.send(response)
    
@bot.command()
async def gms(ctx):
    response = 'Probability indicates the following to be what are known as "Game Masters" to those in other universes:\n'
    gm = []
    player_names = sh.col_values(4)
    activity = sh.col_values(7)
    for index, player in enumerate(player_names):
        if player and activity[index] == 'GM Character':
            gm.append(player)
    response = response + ', '.join(gm)
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
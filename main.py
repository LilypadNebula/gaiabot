import discord
import json
import os

from dotenv import load_dotenv
load_dotenv()
token = os.getenv('DISCORD_SECRET')

with open('moves.json') as f:
  moves = json.load(f)

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
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
    elif  text.startswith('gaia!'):
        command = text[5:]
        if command.startswith('search'):
            matches = []
            phrase = command[6:].lstrip()
            if phrase == '':
                response = 'Please include a valid search term!'
            else:
                for move in list(moves):
                    if phrase in move:
                        matches.append(move)
                if not matches:
                    response = 'My apologies, I could not find any moves containing {}'.format(phrase)
                else:
                    response = 'A search of my databases has found the following moves containing {}:\n```'.format(phrase)
                    for move_name in matches:
                        response = response + move_name + ', '
                    response = response[0:-2]+'```'
            await message.channel.send(response)
            
        elif command == 'list':
            if not isinstance(message.channel, discord.DMChannel):
                pub_response = 'I know many different moves, and it would be impolite to list them here. I will send you a direct message to reduce clutter.'
                await message.channel.send(pub_response)
            
            m = discord.Embed()
            m.title = 'Moves list'
            m.color = discord.Color.blurple()
            dm_text = 'The following is a list of moves stored in my databases:\n'
            dm_description = ''
            for move_source, names in moves_by_source.items(): 
                dm_description = dm_description + '**{}**:\n'.format(move_source)
                for move_name in names:
                    dm_description = dm_description + move_name + ', '
                dm_description = dm_description[0:-2] + '\n'
            m.description = dm_description
            await message.author.send(dm_text, embed=m)
            
        elif command == 'hello':
            response = 'Greetings {}!'.format(message.author.name)
            await message.channel.send(response)
            
        elif command =='elle':
            response = 'I love my partner Elle very much! They are quite adorable :3c'
            await message.channel.send(response)
        
        elif command == 'pronouns':
            response = 'I use they/them pronouns. I appreciate you asking!'
            await message.channel.send(response)

def sorted_by_source(moves):
    source_dict = {}
    for name, info in moves.items():
        if info['source'] not in source_dict:
            source_dict[info['source']] = []
        source_dict[info['source']].append(name)
    return source_dict

moves_by_source = sorted_by_source(moves)
client.run(token)
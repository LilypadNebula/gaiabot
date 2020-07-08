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
                elif len(matches) > 25:
                    response = 'Oh my! That returned quite a few results... You should try making your search a bit more specific ^w^'
                else:
                    response = 'A search of my databases has found the following moves containing {}:\n```'.format(phrase)
                    response = response + ', '.join(matches) + '```'
            await message.channel.send(response)
            
        elif command.startswith('list'):
            source = command[4:].lstrip()    
            if source == '' or source not in list(moves_by_source):
                response = 'I can display moves from any of the following categories:\n'
                response = response + ', '.join(list(moves_by_source))
                await message.channel.send(response)
            else:
                if source in list(moves_by_source):
                    names = moves_by_source[source]
                    m = discord.Embed()
                    m.title = source
                    m.color = discord.Color.blurple()
                    dm_description = ', '.join(list(names))
                    m.description = dm_description
                    await message.channel.send(None, embed=m)
            
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
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
        m.description = 'Move Type: ' + res['type'] + '\n'
        if res['playbook'] is not None:
            m.description = m.description + 'Playbook: ' + res['playbook'] + '\n'
        m.description = m.description + res['text']
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
        elif command.startswith('list'):
            response = 'The following is a list of moves stored in my databases:\n```'
            for move_name in list(moves):
                response = response + move_name + ', '
            response = response[0:-2]+'```'
            await message.author.send(response)
        elif command.startswith('hello'):
            response = 'Greetings {}!'.format(message.author.name)
            await message.channel.send(response)

                
            

client.run(token)
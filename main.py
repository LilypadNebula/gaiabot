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
        m.description = res['text']
        await message.channel.send(None, embed=m)

client.run(token)
import discord
import json
import asyncio
from datetime import datetime

from urllib.parse import urlencode

from lolzapi import LolzteamApi
import time

with open("tokenfile.json", "r") as file:
    tokenfile = json.load(file)

class MyClient(discord.Client):
    token = tokenfile["api_token"]
    profile_id = tokenfile["profile_id"]
    api = LolzteamApi(token, profile_id)

    with open("config.json", "r") as file:
        config = json.load(file)

    roleID = config["role_id_to_ping"]
    prefix = config["prefix"]
    channel_id = config["channel_id"]
    cheapest_price = config["cheapest_price"]

    currentLastAccountID = ''

    #create a function that runs every 15 seconds
    async def check_for_new_accounts(self, channel : discord.TextChannel):
        embedColor = 0xeee657
        while True:
            #check if there are any new accounts
            accounts = self.api.get(f"steam/rust?currency=usd&mm_ban=nomatter&order_by=pdate_to_down_upload")

            if 'errors' in accounts:
                error_message = accounts['errors'][0]
                #send a message to accountChannelID
                await channel.send(f"Error Collecting: {error_message}")
                return

            #get the most recent account
            account = accounts['items'][0]

            i = 1
            while (account['price'] > self.cheapest_price):
                account = accounts['items'][i]
                i += 1

            mostRecentAccountID = account['item_id']

            last_activity_date = datetime.fromtimestamp(account['steam_last_activity'])
            current_date = datetime.now()

            time_diff = current_date - last_activity_date

            if time_diff.days < 1:
                # time_diff is less than 10 days
                embedColor = 0xFF0000  
            elif time_diff.days < 10:
                # time_diff is less than 10 days
                embedColor = 0xeee657
            else:
                # time_diff is 10 days or more
                embedColor = 0x00FF00
                

            #format time_diff to be in days, hours, minutes, seconds
            time_diff = time_diff.days, time_diff.seconds//3600, (time_diff.seconds//60)%60, time_diff.seconds%60
            time_diff = f"{time_diff[0]} Days : {time_diff[1]} Hours"


            registered_date = time.strftime('%Y-%m-%d', time.localtime(account['steam_register_date']))

            #if the most recent account ID is different from the current last account ID
            if mostRecentAccountID != self.currentLastAccountID:
                #set the current last account ID to the most recent account ID
                self.currentLastAccountID = mostRecentAccountID
                #send a message to the channel
                await channel.send(f"||<@&{self.roleID}>||")
                #create embed
                embed = discord.Embed(
                    title=account['title_en'],
                    description="Price (USD): $" + str(account['price']),
                    color=embedColor
                )

                embed.add_field(name="Rust Hours Played", value=str(account['account_full_games']['list']['252490']['playtime_forever']) + "hrs", inline=False)
                embed.add_field(name="Last Active", value=str(time_diff), inline=True)
                embed.add_field(name="Registered Date", value=registered_date, inline=True)
                embed.add_field(name="Guarantee", value=account['guarantee']['durationPhrase'], inline=True)
                embed.add_field(name="Steam Activity (Last 2 Weeks)", value=str(account['steam_hours_played_recently']) + "hrs", inline=True)
                embed.add_field(name="Link", value="https://lzt.market/" + str(account['item_id']), inline=False)
                #embed.add_field(name="Recent Hours Player" , value=account['account_full_games']['list']['252490']['playtime_2weeks'], inline=False)

                embed.set_footer(text="Created by: " + "dylancanada")

                #send the embed to the accountChannelID
                await channel.send(embed=embed)

            await asyncio.sleep(15)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        channel_id = int(self.channel_id)
        channel = client.get_channel(channel_id)
        if channel is None:
            print(f"Channel with ID {self.channel_id} not found.")
            return
        self.loop.create_task(self.check_for_new_accounts(channel))
        
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!recentaccounts'):
            try:          
                accounts = self.api.get(f"steam/rust?currency=usd&mm_ban=nomatter&order_by=pdate_to_down_upload")


                #put accounts into a json file 
                file_path = "api_response.json"
                with open(file_path, 'w') as outfile:
                    json.dump(accounts, outfile)

                if 'errors' in accounts:
                    error_message = accounts['errors'][0]
                    await message.channel.send(f"Error Collecting: {error_message}")
                    return

                for i in range(0, 5):
                    account = accounts['items'][i]

                    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(account['published_date']))
                    last_active = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(account['steam_last_activity']))
                    registered_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(account['steam_register_date']))

                    embed = discord.Embed(
                    title="Recent Accounts #" + str(i+1),
                    description=account['title_en'], 
                    color=0xeee657)

                    embed.add_field(name="Price", value=account['price'], inline=True)
                    embed.add_field(name="Hours Played", value=account['account_full_games']['list']['252490']['playtime_forever'], inline=False)
                    embed.add_field(name="Link", value="https://lzt.market/" + str(account['item_id']), inline=False)
                    embed.add_field(name="Last Active", value=last_active, inline=False)
                    embed.add_field(name="Registered Date", value=registered_date, inline=True)
                    embed.add_field(name="Posted At", value=date, inline=True)
                    #embed.add_field(name="Recent Hours Player" , value=account['account_full_games']['list']['252490']['playtime_2weeks'], inline=False)

                    await message.channel.send(embed=embed)
            except requests.exceptions.RequestException as e:
                print(e)
                await message.channel.send("Error: Request Exception")
            except Exception as e:
                print(e)
                await message.channel.send("Error: " + str(e))
                return

        if message.content.startswith('!accountstatus'):
            try:
                account = self.api.market_me()
                #send account name and status
                print(account)
                await message.channel.send(account["username"] + " " + account["status"])
            except Exception as e:
                print(e)
                await message.channel.send("Error: " + str(e))
                return

            
            



        
intents = discord.Intents.default()
intents.message_content = True


client = MyClient(intents=intents)
client.run(tokenfile["token"])
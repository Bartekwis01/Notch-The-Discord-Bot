# Notch the discord bot

Simple-ish Discord bot that monitors a configured channel for member messages and if a message that contains a valid Minecraft username is sent it uses RCON to add the specified username to the server whitelist and creates an account via the AuthMe plugin with a secure, random password that is sent to the user via a Discord DM.

## Why

This bot is useful for automatically adding users to the whitelist without the need of admin intervention. It's primary use case is private Minecraft SMP's that are running in offline mode. This bot saves the time of admins and ensures that no one is able to break into someone's else's account in the gap between adding an account to the whitelist and the account owner joining the server and registering a password. It also encourages the usage of strong passwords by providing a copy-paste login command to the account owner.

## How it works overview

1. Wait for a message to be sent on a specific channel of a discord server
2. Create a discord thread from that message
3. Check whether the author of the message hasn't already added a nickname to the whitelist
4. Validate that the message contains a valid Minecraft username(characters, length)
5. Connect to the Minecraft server using RCON and add the username to the whitelist
6. Create an AuthME account for the user with a secure, random password
7. Send that password via a DM to that user
8. Save that user's discord account ID and the specified Minecraft nickname to json files in order to prevent multi-accounting and account duplicates

In between of all the steps, the bot logs some debugging info(saved in `bot.log` and `discord.log`) 

At the end the bot posts a short message in the created discord thread notifying of the success or failure in which case the user gets a message about the possible cause of the issue

## Requirements

This bot needs the python packages listed in the `requirements.txt` file.
You can install all the packages using `pip install -r requirements.txt`

Additionally, you need to provide the bot with the following using the .env file:

> DISCORD_TOKEN - specify the discord token of the discord bot you want this code to be run for
>
> USERNAME_CHANNEL_ID - specify the channel ID of the channel where users will post their minecraft usernames
> 
> WHITELIST_PATH - specify the path where the whitelist file will be saved(for duplicate-prevention). Do NOT confuse it with the `whitelist.json` file created and used by the Minecraft server - these are completely separate
> 
> DISCORD_IDS_PATH - specify the path where the discord IDs should be saved of the members which minecraft usernames are successfully added to the whitelist(for multi-accounting prevention)
> 
> LOGGING_LEVEL - specify the logging level to be used. Available levels: debug, info, warning, error
> 
> RCON_HOST - specify the IP of the Minecraft server
> 
> RCON_PORT - specify the PORT of the Minecraft server's remote console
> 
> RCON_PASSWORD - specify the password of the Minecraft server's remote console

An example `.env` file has been included

Lastly, make sure that your server has the AuthME plugin installed in order for the account creation with random passwords to work

## Lastly

This is my first discord bot so, while I have done everything I could to make it reliable, it could have issues and please beware of that while using it.

While the documentation is in English, the bot responds to discord messages in Polish.
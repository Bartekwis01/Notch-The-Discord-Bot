from json import JSONDecodeError
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json
import colorlog
from mcrcon import MCRcon
import secrets
import string

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
USERNAME_CHANNEL = int(os.getenv('USERNAME_CHANNEL_ID'))
DISCORD_IDS_PATH = os.getenv('DISCORD_IDS_PATH')
WHITELIST_PATH = os.getenv('WHITELIST_PATH')
ALLOWED_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
LOGGING_LEVEL_ENV = os.getenv('LOGGING_LEVEL').upper()
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = os.getenv('RCON_PORT')
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

LOG_LEVEL = getattr(logging, LOGGING_LEVEL_ENV, logging.INFO)  # fallback to INFO

formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    "%Y/%m/%d %H:%M:%S"
)

color_formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    "%Y/%m/%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "white",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
)

#bot logging
bot_logger = logging.getLogger("bot")
bot_logger.setLevel(LOG_LEVEL)

#file
bot_file_handler = logging.FileHandler("bot.log", encoding="utf-8", mode="w")
bot_file_handler.setFormatter(formatter)
bot_logger.addHandler(bot_file_handler)

#console
bot_console_handler = logging.StreamHandler()
bot_console_handler.setFormatter(color_formatter)
bot_logger.addHandler(bot_console_handler)

#discord logging
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(LOG_LEVEL)

#file
discord_file_handler = logging.FileHandler("discord.log", encoding="utf-8", mode="w")
discord_file_handler.setFormatter(formatter)
discord_logger.addHandler(discord_file_handler)

#console
discord_console_handler = logging.StreamHandler()
discord_console_handler.setFormatter(color_formatter)
discord_logger.addHandler(discord_console_handler)

def handler(message, tier="info"):
    if tier == "debug":
        bot_logger.debug(message)
    if tier == "info":
        bot_logger.info(message)
    if tier == "warning":
        bot_logger.warning(message)
    if tier == "error":
        bot_logger.error(message)

handler(f'Loading the bot...')

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

class DuplicateMinecraftError(Exception):
    pass

class DuplicateDiscordError(Exception):
    pass

class TooLongError(Exception):
    pass

class InvalidCharactersError(Exception):
    pass

class FailedRCONError(Exception):
    pass

def load_file(path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (JSONDecodeError, ValueError) as e:
            handler(e, "error")
            return []
    else:
        handler(f'{path} does not exist, returning empty list', "debug")
        return []

def save_file(path, data):
    handler(f'Saving {path}', "debug")
    if os.path.exists(path):
        handler(f'{path} already exists, overwriting', "debug")
    else:
        handler(f"{path} doesn't exist, creating", "debug")
    with open(path, 'w') as f:
        json.dump(data, f)
        handler(f'{path} saved')

def password_generator(size=16):
    alphabet = string.ascii_letters + string.digits

    password = ''.join(secrets.choice(alphabet) for _ in range(size))

    handler(f'Successfully generated a password.', "debug")
    return password

def add_to_whitelist(discord_member, minecraft_username):
    whitelist = load_file(WHITELIST_PATH)
    discord_ids = load_file(DISCORD_IDS_PATH)

    discord_id=discord_member.id

    #check if it's a duplicate
    handler(f'Checking if {discord_member} has already added a username to the whitelist', "debug")
    if discord_id in discord_ids:
        raise DuplicateDiscordError(f'{discord_member} has already added a username to the whitelist', "debug")
    handler(f'{discord_member} has not added a username to the whitelist', "debug")

    handler(f'Checking if {minecraft_username} is already in the whitelist', "debug")
    if minecraft_username in whitelist:
        raise DuplicateMinecraftError(f'{minecraft_username} is already in the whitelist', "debug")
    handler(f'{minecraft_username} is not in the whitelist', "debug")

    #check if it's a valid username
    handler(f'Checking if {minecraft_username} is a valid username', "debug")
    if not 3 <= len(minecraft_username) <= 16:
        raise TooLongError(f'{minecraft_username} is too long and is invalid')
    for char in minecraft_username:
        if not char in ALLOWED_CHARACTERS:
            raise InvalidCharactersError(f'{minecraft_username} has "{char} which is not a valid character for a Minecraft username')
    handler(f'{minecraft_username} is a valid username', "debug")

    #add to whitelist and create a password
    handler(f'Connecting with RCON', "debug")
    mcrcon = MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT)
    try:
        mcrcon.connect()
    except:
        handler(f'Failed to connect to RCON', "error")
        raise FailedRCONError(f'Failed to connect to RCON')
    handler(f'Executing /whitelist add {minecraft_username}', "debug")
    response = mcrcon.command(f"/whitelist add {minecraft_username}")
    handler(response, "info")
    handler(f'Generating a password for {minecraft_username}', "debug")
    random_password = password_generator()
    handler(f'Executing /authme register {minecraft_username} [redacted_password]', "debug")
    response = mcrcon.command(f'/authme register {minecraft_username} {random_password}')
    handler(response, "info")
    handler(f'Disconnecting from RCON', "debug")
    mcrcon.disconnect()

    #save the files
    handler(f'Adding {minecraft_username} to whitelist file', "debug")
    whitelist.append(minecraft_username)
    handler(f'Added {minecraft_username} to whitelist file')
    handler(f'Adding Discord ID {discord_id} of {discord_member} to {DISCORD_IDS_PATH} file', "debug")
    discord_ids.append(discord_id)
    handler(f'Added Discord ID {discord_id}) of {discord_member} to {DISCORD_IDS_PATH} file', "debug")

    handler(f'Saving the files', "debug")
    save_file(DISCORD_IDS_PATH, discord_ids)
    save_file(WHITELIST_PATH, whitelist)

    #return the password in order to send it to the user
    return random_password

@bot.event
async def on_ready():
    handler(f'{bot.user.name} has successfully connected to Discord!')

@bot.event
async def on_message(message):
    try:
        handler(f'{message.author} said "{message.content}"', "debug")
        if message.author == bot.user:
            handler(f'It was me, ignoring', "debug")
            return
        if message.channel.id != USERNAME_CHANNEL:
            handler(f'It was in the wrong channel, ignoring', "debug")
            return
        handler(f'Responding to {message.author}: {message.content}')
        discord_member = message.author
        minecraft_username = message.content
        try:
            handler(f'Creating a new thread for {discord_member}', "debug")
            thread = await message.create_thread(name=f'Dodawanie {minecraft_username[:16]} do whitelisty', auto_archive_duration=60)
        except:
            handler(f"Couldn't create thread for {message.author}", "error")
            return

        try:
            password = add_to_whitelist(discord_member, minecraft_username)
            await thread.send(f'Dodano **{minecraft_username}** do whitelisty!')
            await discord_member.send(f'Aby zalogować się na swoje konto serwerowe, użyj komendy `/login {password}`. Możesz zmienić hasło używając komendy `/changepassword {password} <nowe hasło>` po zalogowaniu.')
        except DuplicateDiscordError:
            handler(f'{discord_member} has already added a username to the whitelist')
            await thread.send(f'Istnieje już nick na whitelist powiązany z kontem **{discord_member}**!')
            return
        except DuplicateMinecraftError:
            handler(f'{discord_member} has been already added to the whitelist')
            await thread.send(f'**{minecraft_username}** został już dodany do whitelisty!')
            return
        except TooLongError:
            handler(f'{minecraft_username[:64]} is too long and is invalid')
            await thread.send(f'Nick **{minecraft_username[:64]}** jest za długi i nie prawidłowy!')
            return
        except InvalidCharactersError:
            handler(f'{minecraft_username} contains invalid characters')
            await thread.send(f'Nick **{minecraft_username[:64]}** zawiera nieprawidłowe znaki!')
            return
        except FailedRCONError:
            await thread.send(f'Nie udało się dodać nicku do whitelisty! Skontaktuj się z Administratorem podając kod błędu: `FailedRCONError`')
            return

        handler(f'Changing the username of {discord_member} to {minecraft_username}', "debug")
        try:
            await message.author.edit(nick=minecraft_username)
            handler(f'Successfully changed the nickname of {discord_member} to {minecraft_username}')
        except PermissionError:
            handler(f'Couldn\'t change the nickname of {discord_member} to {minecraft_username} because of permission error', "error")
            await thread.send(f'Nie udało się zmienić nicku **{discord_member}** na **{minecraft_username}**! Skontaktuj się z Administratorem podając kod błędu: FailedRCONError.')
            return

    finally:
        await bot.process_commands(message)
bot.run(DISCORD_TOKEN)
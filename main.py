# main.py

# Main file to VirtualGM - a discord bot written with the pycord library

import asyncio
import logging

# imports
import os
import sys

import websockets
from dotenv import load_dotenv

import EPF.Data.Kineticist_DB
import EPF.Data.Spell_DB
import database_operations
from API.VGM_API import start_uvicorn
from Bot import bot
from EPF.EPF_Automation_Data import upload_data
from database_operations import socket

# import tracemalloc

# Set up logging
# warnings.filterwarnings("always", category=exc.RemovedIn20Warning)


# environmental variables - if Production - use the token and database of the production model, if Production is False,
# then its running locally and use the local postgres server and the beta token. This allows one .env and code for both
# testing and production.

# import database_operations


load_dotenv(verbose=True)
if os.environ["PRODUCTION"] == "True":
    logging.basicConfig(level=logging.WARNING)
    logging.info("Script Started")

else:
    logging.basicConfig(level=logging.INFO)
    logging.info("Script Started")

TOKEN = os.environ["BOT_TOKEN"]
GUILD = os.getenv("GUILD")
DATABASE = os.getenv("DATABASE")

# tracemalloc.start()


# Print Status on Connected - Outputs to server log
@bot.event
async def on_ready():
    logging.warning("Updating tables...")
    database_operations.create_roll_log()

    await upload_data(EPF.Data.Kineticist_DB.Kineticist_DB)
    await upload_data(EPF.Data.Spell_DB.Cantrips)
    await upload_data((EPF.Data.Spell_DB.Psychic_Cantrips))
    # await database_operations.update_global_manager()
    # await database_operations.update_tracker_table()
    # await database_operations.update_con_table()
    # database_operations.create_reminder_table()
    # logging.warning("Tables updated")
    logging.warning(f"Connected to {len(bot.guilds)} servers.")
    logging.warning(f"{bot.user} is connected.")
    loop = asyncio.get_running_loop()
    start_uvicorn(loop)
    # loop.create_task( async_partial(socket.start))
    # loop.run_forever()
    # await socket.start()
    serve = await websockets.serve(socket.handle, "0.0.0.0", 6270)
    # loop = asyncio.get_running_loop()
    # loop.create_task(async_partial(self.handle))
    await serve.wait_closed()


@bot.event
async def on_disconnect():
    # await bot.connect()
    logging.warning("Disconnected")


@bot.event
async def on_error():
    logging.error(f"on_error: {sys.exc_info()}")


# Initialize the database for the 4e lookup
# lookup_parser.parser()

# Load the bot
# bot.load_extension("Query.query_results")
bot.load_extension("dice_roller_cog")
bot.load_extension("initiative")
bot.load_extension("error_reporting_cog")
bot.load_extension("help_cog")
bot.load_extension("timekeeping")
bot.load_extension("macro_cog")
bot.load_extension("options_cog")
bot.load_extension("PF2e.pf2_cog")
bot.load_extension("automation_cog")
bot.load_extension("Update_and__Maintenance_Cog")
bot.load_extension("reminder_cog")
bot.load_extension("STF.stf_cog")
bot.load_extension("RED.RED_cog")

bot.run(TOKEN)

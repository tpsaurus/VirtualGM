# d4e_cog.py
# For slash commands specific to oathfinder 2e
# system specific module
import logging
import os

# imports
import discord
from discord.commands import SlashCommandGroup, option
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import D4e.D4e_Tracker
import D4e.d4e_functions

import ui_components
from auto_complete import character_select_gm
from database_models import Global, get_condition, get_tracker
from database_operations import get_asyncio_db_engine
from error_handling_reporting import ErrorReport

# define global variables
from utils.utils import get_guild

load_dotenv(verbose=True)
if os.environ["PRODUCTION"] == "True":
    TOKEN = os.getenv("TOKEN")
    USERNAME = os.getenv("Username")
    PASSWORD = os.getenv("Password")
    HOSTNAME = os.getenv("Hostname")
    PORT = os.getenv("PGPort")
else:
    TOKEN = os.getenv("BETA_TOKEN")
    USERNAME = os.getenv("BETA_Username")
    PASSWORD = os.getenv("BETA_Password")
    HOSTNAME = os.getenv("BETA_Hostname")
    PORT = os.getenv("BETA_PGPort")

GUILD = os.getenv("GUILD")
SERVER_DATA = os.getenv("SERVERDATA")
DATABASE = os.getenv("DATABASE")


# ---------------------------------------------------------------
# ---------------------------------------------------------------
# UTILITY FUNCTIONS


# Checks to see if the user of the slash command is the GM, returns a boolean



class D4eCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # ---------------------------------------------------
    # ---------------------------------------------------
    # Autocomplete Methods

    # Provide a list of conditions with the visible and flex tags
    async def cc_select_visible_flex(self, ctx: discord.AutocompleteContext):
        engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=SERVER_DATA)
        character = ctx.options["character"]

        try:
            async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            guild = await get_guild(ctx, None)
            Tracker = await get_tracker(ctx, engine, id=guild.id)
            Condition = await get_condition(ctx, engine, id=guild.id)

            async with async_session() as session:
                char_result = await session.execute(select(Tracker.id).where(Tracker.name == character))
                char = char_result.scalars().one()
            async with async_session() as session:
                con_result = await session.execute(
                    select(Condition.title)
                    .where(Condition.character_id == char)
                    .where(Condition.visible == true())
                    .where(Condition.flex == true())
                )
                condition = con_result.scalars().all()
            await engine.dispose()
            return condition

        except Exception as e:
            logging.warning(f"cc_select: {e}")
            report = ErrorReport(ctx, self.cc_select.__name__, e, self.bot)
            await report.report()
            return []

    ########################################
    ########################################
    # Slash Commands

    dd = SlashCommandGroup("d4e", "D&D 4th Edition Specific Commands")

    @dd.command(description="D&D 4e auto save")
    # @commands.slash_command(name="d4e_save", guild_ids=[GUILD])
    @option("character", description="Character Attacking", autocomplete=character_select_gm)
    @option("condition", description="Select Condition", autocomplete=cc_select_visible_flex)
    async def save(self, ctx: discord.ApplicationContext, character: str, condition: str, modifier: str = ""):
        engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=SERVER_DATA)
        await ctx.response.defer()
        guild = await get_guild(ctx, None)
        if guild.system == "D4e":
            output_string = await D4e.d4e_functions.save(ctx, engine, self.bot, character, condition, modifier)
            await engine.dispose()
            await ctx.send_followup(output_string)
        else:
            await ctx.send_followup("No system set, command inactive.")
        await engine.dispose()
        return

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("4e Cog Loaded")
        # We recreate the view as we did in the /post command.
        view = discord.ui.View(timeout=None)

        engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=SERVER_DATA)
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with async_session() as session:
            result = await session.execute(select(Global).where(Global.last_tracker.isnot(None)))
            guild_list = result.scalars().all()

            for guild in guild_list:
                if guild.system == "D4e":
                    try:# Error handling to avoid locking on a bad message
                        view.clear_items()
                        tracker_channel = self.bot.get_channel(guild.tracker_channel)
                        last_tracker = await tracker_channel.fetch_message(guild.last_tracker)

                        view = await D4e.D4e_Tracker.D4eTrackerButtons(None, self.bot, guild)
                        view.add_item(ui_components.InitRefreshButton(None, self.bot, guild=guild))
                        view.add_item(ui_components.NextButton(self.bot, guild=guild))
                        await last_tracker.edit(view=view)
                        logging.info("D4e View Updated")
                    except Exception as e:
                        logging.error(f"d4e on ready attach buttons: {e} {guild.id}")
                        # TODO add in more robust error reporting for this to see if it becomes an issue

                else:
                    try:
                        view.clear_items()
                        tracker_channel = self.bot.get_channel(guild.tracker_channel)
                        last_tracker = await tracker_channel.fetch_message(guild.last_tracker)
                        view = discord.ui.View(timeout=None)
                        view.add_item(ui_components.InitRefreshButton(None, self.bot, guild=guild))
                        view.add_item(ui_components.NextButton(self.bot, guild=guild))
                        await last_tracker.edit(view=view)
                        logging.info("View Updated")
                    except Exception as e:
                        logging.error(f"pf2 on ready attach buttons: {e} {guild.id}")
                        # TODO add in more robust error reporting for this to see if it becomes an issue


def setup(bot):
    bot.add_cog(D4eCog(bot))

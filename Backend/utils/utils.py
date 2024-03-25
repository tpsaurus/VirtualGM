import logging
import os

import discord
from dotenv import load_dotenv
from sqlalchemy import or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from Backend.Database.database_models import Global, get_tracker
from Backend.Database.database_operations import get_asyncio_db_engine
from Backend.utils.error_handling_reporting import ErrorReport

load_dotenv(verbose=True)
if os.environ["PRODUCTION"] == "True":
    # TOKEN = os.getenv("TOKEN")
    USERNAME = os.getenv("Username")
    PASSWORD = os.getenv("Password")
    HOSTNAME = os.getenv("Hostname")
    PORT = os.getenv("PGPort")
else:
    # TOKEN = os.getenv("BETA_TOKEN")
    USERNAME = os.getenv("BETA_Username")
    PASSWORD = os.getenv("BETA_Password")
    HOSTNAME = os.getenv("BETA_Hostname")
    PORT = os.getenv("BETA_PGPort")

GUILD = os.getenv("GUILD")
SERVER_DATA = os.getenv("SERVERDATA")
DATABASE = os.getenv("DATABASE")

NPC_Iterator = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]


async def get_guild(ctx, guild, refresh=False, id=None):
    engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=SERVER_DATA)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    if guild is not None and not refresh:
        return guild
    if ctx is None and guild is None:
        raise LookupError("No guild reference")

    try:
        async with async_session() as session:
            if ctx is None:
                logging.info("Refreshing Guild")
                result = await session.execute(select(Global).where(Global.id == guild.id))
            else:
                result = await session.execute(
                    select(Global).where(
                        or_(
                            Global.tracker_channel == ctx.interaction.channel_id,
                            Global.gm_tracker_channel == ctx.interaction.channel_id,
                        )
                    )
                )

            guild_result = result.scalars().one()
            # await engine.dispose()
            return guild_result
    except Exception:
        if id is not None:
            # print(id)
            async with async_session() as session:
                result = await session.execute(select(Global).where(Global.id == id))
                guild_result = result.scalars().one()
                # await engine.dispose()
                return guild_result
        else:
            raise NoResultFound("No guild referenced")


async def gm_check(ctx, engine):
    logging.info("gm_check")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Global.gm).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            gm = result.scalars().one()
            if int(gm) != int(ctx.interaction.user.id):
                return False
            else:
                return True
    except Exception:
        raise


async def player_check(ctx: discord.ApplicationContext, engine, bot, character: str):
    logging.info("player_check")
    try:
        Tracker = await get_tracker(ctx, engine)
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

        async with async_session() as session:
            char_result = await session.execute(select(Tracker).where(Tracker.name == character))
            character = char_result.scalars().one()
        return character

    except Exception as e:
        logging.warning(f"player_check: {e}")
        report = ErrorReport(ctx, player_check.__name__, e, bot)
        await report.report()


def relabel_roll(roll: str):
    try:
        parsed_roll = roll.split(" ", maxsplit=1)
        if len(parsed_roll) > 1 and parsed_roll[1][0] != "[":
            output = f"{parsed_roll[0]} [{parsed_roll[1]}]"
        else:
            output = roll
    except Exception:
        output = roll
    return output


async def direct_message(user: discord.User, message: str, embeds=[]):
    dm_channel = user.dm_channel
    if dm_channel is None:
        await user.create_dm()
        dm_channel = user.dm_channel
        # await dm_channel.send(
        #     "This is the beginning of your audit log with VirtualGM.  If you do not wish to see "
        #     "these messages, it can be turned off in the `/admin options` command."
        # )

    await dm_channel.send(message, embeds=embeds)
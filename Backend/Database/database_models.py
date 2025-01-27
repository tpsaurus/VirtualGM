# database_models.py

import logging

import discord
import sqlalchemy as db
from sqlalchemy import Column, JSON
from sqlalchemy import ForeignKey
from sqlalchemy import Integer, BigInteger
from sqlalchemy import String, Boolean
from sqlalchemy import or_, select
from sqlalchemy.orm import declarative_base


import Systems.RED.RED_Support
from Systems.EPF import EPF_Support
from Systems.STF import STF_Support
from Backend.Database.engine import async_session

Base = declarative_base()
LookupBase = declarative_base()
RollLogBase = declarative_base()


# Database Models


# Global Class
class Global(Base):
    __tablename__ = "global_manager"
    # ID Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger())
    gm = Column(String())
    # Feature Flags
    explode = Column(Boolean(), default=False)
    aliases = Column(Boolean(), default=False)
    block = Column(Boolean(), default=False)
    system = Column(String(), default=None, nullable=True)
    # Initiative Tracker
    initiative = Column(Integer())
    round = Column(Integer(), default=0)
    saved_order = Column(String(), default="")
    tracker = Column(BigInteger(), nullable=True)
    tracker_channel = Column(BigInteger(), nullable=True, unique=True)
    gm_tracker = Column(BigInteger(), nullable=True)
    gm_tracker_channel = Column(BigInteger(), nullable=True, unique=True)
    rp_channel = Column(BigInteger(), nullable=True, unique=True)
    last_tracker = Column(BigInteger(), nullable=True)
    # Timekeeper Functionality
    timekeeping = Column(Boolean(), default=False)
    time = Column(BigInteger(), default=6, nullable=False)
    time_second = Column(Integer(), nullable=True)
    time_minute = Column(Integer(), nullable=True)
    time_hour = Column(Integer(), nullable=True)
    time_day = Column(Integer(), nullable=True)
    time_month = Column(Integer(), nullable=True)
    time_year = Column(Integer(), nullable=True)
    # Extra
    block_data = Column(JSON(), nullable=True)
    audit_log = Column(String(), default="GM")
    members = Column(JSON(), default=[])


#########################################
#########################################
# Tracker Table


# Tracker Get Function
async def get_tracker(ctx: discord.ApplicationContext, id=None, system=None):
    if ctx is None and id is None:
        raise Exception

    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
            system = guild.system
        id = guild.id
    else:
        try:
            async with async_session() as session:
                result = await session.execute(select(Global).where(Global.id == id))
                guild = result.scalars().one()
                system = guild.system
        except Exception:
            pass

    if system == "EPF":
        return await get_EPF_tracker(ctx, id=id)
    elif system == "RED":
        return await get_RED_tracker(ctx, id=id)
    elif system == "STF":
        return await get_STF_tracker(ctx, id=id)
    else:
        tablename = f"Tracker_{id}"
        logging.info(f"get_tracker: Guild: {id}")

        DynamicBase = declarative_base(class_registry=dict())

        class Tracker(DynamicBase):
            __tablename__ = tablename
            __table_args__ = {"extend_existing": True}

            id = Column(Integer(), primary_key=True, autoincrement=True)
            name = Column(String(), nullable=False, unique=True)
            init = Column(Integer(), default=0)
            player = Column(Boolean(), nullable=False)
            user = Column(BigInteger(), nullable=False)
            current_hp = Column(Integer(), default=0)
            max_hp = Column(Integer(), default=1)
            temp_hp = Column(Integer(), default=0)
            init_string = Column(String(), nullable=True)
            active = Column(Boolean(), default=True)
            pic = Column(String(), nullable=True)
            variables = Column(
                JSON(),
                nullable=True,
            )

        logging.info("get_tracker: returning tracker")
        return Tracker


# Old Tracker Get Fuctcion
async def get_tracker_table(ctx, metadata, guild=None):
    if ctx is None and guild is None:
        raise LookupError("No guild reference")

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
        guild = result.scalars().one()

    if guild.system == "EPF":
        table = EPF_Support.PF2_Character_Model(ctx, metadata, guild.id).pf2_character_model_table()
    elif guild.system == "RED":
        table = Systems.RED.RED_Support.RED_Character_Model(ctx, metadata, guild.id).RED_character_model_table()

    elif guild.system == "STF":
        table = STF_Support.STF_Character_Model(ctx, metadata, guild.id).stf_character_model_table()
    else:
        table = TrackerTable(ctx, metadata, guild.id).tracker_table()
    return table


# Old Tracker (emp) Class
class TrackerTable:
    def __init__(self, ctx, metadata, id):
        self.guild = ctx.interaction.guild_id
        self.channel = ctx.interaction.channel_id
        self.metadata = metadata
        self.id = id

    def tracker_table(self):
        tablename = f"Tracker_{self.id}"
        emp = db.Table(
            tablename,
            self.metadata,
            db.Column("id", db.INTEGER(), autoincrement=True, primary_key=True),
            db.Column("name", db.String(255), nullable=False, unique=True),
            db.Column("init", db.INTEGER(), default=0),
            db.Column("player", db.BOOLEAN, default=False),
            db.Column("user", db.BigInteger(), nullable=False),
            db.Column("current_hp", db.INTEGER(), default=0),
            db.Column("max_hp", db.INTEGER(), default=1),
            db.Column("temp_hp", db.INTEGER(), default=0),
            db.Column("init_string", db.String(255), nullable=True),
            db.Column("active", db.BOOLEAN, default=True),
            db.Column("pic", db.String(), nullable=True),
            db.Column("variables", db.JSON(), nullable=True),
        )
        return emp


async def get_EPF_tracker(ctx: discord.ApplicationContext, id=None):
    if ctx is None and id is None:
        raise Exception
    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global.id).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
            tablename = f"Tracker_{guild}"
            logging.info(f"get_tracker: Guild: {guild}")

    else:
        tablename = f"Tracker_{id}"

    DynamicBase = declarative_base(class_registry=dict())

    class Tracker(DynamicBase):
        __tablename__ = tablename
        __table_args__ = {"extend_existing": True}

        # The original tracker table
        id = Column(Integer(), primary_key=True, autoincrement=True)
        name = Column(String(), nullable=False, unique=True)
        init = Column(Integer(), default=0)
        player = Column(Boolean(), nullable=False)
        user = Column(BigInteger(), nullable=False)
        current_hp = Column(Integer(), default=0)
        max_hp = Column(Integer(), default=1)
        temp_hp = Column(Integer(), default=0)
        init_string = Column(String(), nullable=True)
        active = Column(Boolean(), default=True)

        # General
        char_class = Column(String(), nullable=False)
        level = Column(Integer(), nullable=False)
        ac_base = Column(Integer(), nullable=False)
        class_dc = Column(Integer(), nullable=False)

        # Stats
        str = Column(Integer(), nullable=False)
        dex = Column(Integer(), nullable=False)
        con = Column(Integer(), nullable=False)
        itl = Column(Integer(), nullable=False)
        wis = Column(Integer(), nullable=False)
        cha = Column(Integer(), nullable=False)

        # Saves
        fort_prof = Column(Integer(), nullable=False)
        will_prof = Column(Integer(), nullable=False)
        reflex_prof = Column(Integer(), nullable=False)

        # Proficiencies
        perception_prof = Column(Integer(), nullable=False)
        class_prof = Column(Integer(), nullable=False)
        key_ability = Column(String(), nullable=False)

        unarmored_prof = Column(Integer(), nullable=False)
        light_armor_prof = Column(Integer(), nullable=False)
        medium_armor_prof = Column(Integer(), nullable=False)
        heavy_armor_prof = Column(Integer(), nullable=False)

        unarmed_prof = Column(Integer(), nullable=False)
        simple_prof = Column(Integer(), nullable=False)
        martial_prof = Column(Integer(), nullable=False)
        advanced_prof = Column(Integer(), nullable=False)

        arcane_prof = Column(Integer(), nullable=False)
        divine_prof = Column(Integer(), nullable=False)
        occult_prof = Column(Integer(), nullable=False)
        primal_prof = Column(Integer(), nullable=False)

        acrobatics_prof = Column(Integer(), nullable=False)
        arcana_prof = Column(Integer(), nullable=False)
        athletics_prof = Column(Integer(), nullable=False)
        crafting_prof = Column(Integer(), nullable=False)
        deception_prof = Column(Integer(), nullable=False)
        diplomacy_prof = Column(Integer(), nullable=False)
        intimidation_prof = Column(Integer(), nullable=False)
        medicine_prof = Column(Integer(), nullable=False)
        nature_prof = Column(Integer(), nullable=False)
        occultism_prof = Column(Integer(), nullable=False)
        performance_prof = Column(Integer(), nullable=False)
        religion_prof = Column(Integer(), nullable=False)
        society_prof = Column(Integer(), nullable=False)
        stealth_prof = Column(Integer(), nullable=False)
        survival_prof = Column(Integer(), nullable=False)
        thievery_prof = Column(Integer(), nullable=False)

        # Plan to save parsable lists here
        lores = Column(String())
        feats = Column(String())

        # Calculated stats
        str_mod = Column(Integer())
        dex_mod = Column(Integer())
        con_mod = Column(Integer())
        itl_mod = Column(Integer())
        wis_mod = Column(Integer())
        cha_mod = Column(Integer())

        # Saves
        fort_mod = Column(Integer())
        will_mod = Column(Integer())
        reflex_mod = Column(Integer())

        acrobatics_mod = Column(Integer())
        arcana_mod = Column(Integer())
        athletics_mod = Column(Integer())
        crafting_mod = Column(Integer())
        deception_mod = Column(Integer())
        diplomacy_mod = Column(Integer())
        intimidation_mod = Column(Integer())
        medicine_mod = Column(Integer())
        nature_mod = Column(Integer())
        occultism_mod = Column(Integer())
        performance_mod = Column(Integer())
        religion_mod = Column(Integer())
        society_mod = Column(Integer())
        stealth_mod = Column(Integer())
        survival_mod = Column(Integer())
        thievery_mod = Column(Integer())

        arcane_mod = Column(Integer())
        divine_mod = Column(Integer())
        occult_mod = Column(Integer())
        primal_mod = Column(Integer())

        ac_total = Column(Integer())
        resistance = Column(JSON())
        perception_mod = Column(Integer())
        macros = Column(String())
        attacks = Column(JSON())
        spells = Column(JSON())
        bonuses = Column(JSON())
        eidolon = Column(Boolean(), default=False)
        partner = Column(String())
        pic = Column(String(), nullable=True)
        variables = Column(JSON(), nullable=True)

    logging.info("get_tracker: returning tracker")
    return Tracker


async def get_STF_tracker(ctx: discord.ApplicationContext, id=None):
    if ctx is None and id is None:
        raise Exception
    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global.id).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
            tablename = f"Tracker_{guild}"
            logging.info(f"get_tracker: Guild: {guild}")

    else:
        tablename = f"Tracker_{id}"

    DynamicBase = declarative_base(class_registry=dict())

    class Tracker(DynamicBase):
        __tablename__ = tablename
        __table_args__ = {"extend_existing": True}

        # The original tracker table
        id = Column(Integer(), primary_key=True, autoincrement=True)
        name = Column(String(), nullable=False, unique=True)
        init = Column(Integer(), default=0)
        player = Column(Boolean(), nullable=False)
        user = Column(BigInteger(), nullable=False)
        current_hp = Column(Integer(), default=0)
        current_stamina = Column(Integer(), default=0)
        max_stamina = Column(Integer(), default=1)
        max_hp = Column(Integer(), default=1)
        temp_hp = Column(Integer(), default=0)
        init_string = Column(String(), nullable=True)
        active = Column(Boolean(), default=True)
        char_class = Column(String(), default="")

        level = Column(Integer(), nullable=False)
        base_eac = Column(Integer(), nullable=False)
        base_kac = Column(Integer(), nullable=False)
        bab = Column(Integer(), nullable=False)
        max_resolve = Column(Integer(), default=1)
        resolve = Column(Integer(), default=1)
        key_ability = Column(String(), default="")

        str = Column(Integer(), nullable=False)
        dex = Column(Integer(), nullable=False)
        con = Column(Integer(), nullable=False)
        itl = Column(Integer(), nullable=False)
        wis = Column(Integer(), nullable=False)
        cha = Column(Integer(), nullable=False)

        # Saves
        fort = Column(Integer(), nullable=False)
        will = Column(Integer(), nullable=False)
        reflex = Column(Integer(), nullable=False)

        acrobatics = Column(Integer(), nullable=False)
        athletics = Column(Integer(), nullable=False)
        bluff = Column(Integer(), nullable=False)
        computers = Column(Integer(), nullable=False)
        culture = Column(Integer(), nullable=False)
        diplomacy = Column(Integer(), nullable=False)
        disguise = Column(Integer(), nullable=False)
        engineering = Column(Integer(), nullable=False)
        intimidate = Column(Integer(), nullable=False)
        life_science = Column(Integer(), nullable=False)
        medicine = Column(Integer(), nullable=False)
        mysticism = Column(Integer(), nullable=False)
        perception = Column(Integer(), nullable=False)
        physical_science = Column(Integer(), nullable=False)
        piloting = Column(Integer(), nullable=False)
        sense_motive = Column(Integer(), nullable=False)
        sleight_of_hand = Column(Integer(), nullable=False)
        stealth = Column(Integer(), nullable=False)
        survival = Column(Integer(), nullable=False)

        str_mod = Column(Integer())
        dex_mod = Column(Integer())
        con_mod = Column(Integer())
        itl_mod = Column(Integer())
        wis_mod = Column(Integer())
        cha_mod = Column(Integer())

        fort_mod = Column(Integer())
        will_mod = Column(Integer())
        reflex_mod = Column(Integer())

        acrobatics_mod = Column(Integer())
        athletics_mod = Column(Integer())
        bluff_mod = Column(Integer())
        computers_mod = Column(Integer())
        culture_mod = Column(Integer())
        diplomacy_mod = Column(Integer())
        disguise_mod = Column(Integer())
        engineering_mod = Column(Integer())
        intimidate_mod = Column(Integer())
        life_science_mod = Column(Integer())
        medicine_mod = Column(Integer())
        mysticism_mod = Column(Integer())
        perception_mod = Column(Integer())
        physical_science_mod = Column(Integer())
        piloting_mod = Column(Integer())
        sense_motive_mod = Column(Integer())
        sleight_of_hand_mod = Column(Integer())
        stealth_mod = Column(Integer())
        survival_mod = Column(Integer())

        eac = Column(Integer())
        kac = Column(Integer())

        macros = Column(JSON())
        attacks = Column(JSON())
        spells = Column(JSON())
        bonuses = Column(JSON())
        resistance = Column(JSON())
        pic = Column(String(), nullable=True)
        variables = Column(JSON(), nullable=True)

    logging.info("get_tracker: returning tracker")
    return Tracker


async def get_RED_tracker(ctx: discord.ApplicationContext, id=None):
    if ctx is None and id is None:
        raise Exception
    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global.id).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
            tablename = f"Tracker_{guild}"
            logging.info(f"get_tracker: Guild: {guild}")

    else:
        tablename = f"Tracker_{id}"

    DynamicBase = declarative_base(class_registry=dict())

    class Tracker(DynamicBase):
        __tablename__ = tablename
        __table_args__ = {"extend_existing": True}

        # The original tracker table
        id = Column(Integer(), primary_key=True, autoincrement=True)
        name = Column(String(), nullable=False, unique=True)
        init = Column(Integer(), default=0)
        player = Column(Boolean(), nullable=False)
        user = Column(BigInteger(), nullable=False)
        current_hp = Column(Integer(), default=0)
        max_hp = Column(Integer(), default=1)
        temp_hp = Column(Integer(), default=0)
        init_string = Column(String(), nullable=True)
        active = Column(Boolean(), default=True)

        # General
        char_class = Column(String(), nullable=False)
        level = Column(Integer(), nullable=False)

        # Additional Consumables
        humanity = Column(JSON(), nullable=False)
        current_luck = Column(Integer(), nullable=False)

        # JSONs
        stats = Column(JSON(), nullable=False)
        skills = Column(JSON(), nullable=False)
        attacks = Column(JSON(), nullable=False)
        armor = Column(JSON(), nullable=False)
        cyber = Column(JSON(), nullable=False)
        net = Column(JSON(), nullable=False)

        # Functional Stuff
        macros = Column(JSON())
        bonuses = Column(JSON())
        resistances = Column(JSON())
        pic = Column(String(), nullable=True)
        net_status = Column(Boolean(), default=False)
        tie_breaker = Column(Integer())
        variables = Column(JSON(), nullable=True)

    logging.info("get_tracker: returning tracker RED")
    return Tracker


#########################################
#########################################
# Condition Table


# Condition Get Function
async def get_condition(ctx: discord.ApplicationContext, id=None):
    if ctx is None and id is None:
        raise Exception

    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
        id = guild.id
    else:
        async with async_session() as session:
            result = await session.execute(select(Global).where(Global.id == id))
            guild = result.scalars().one()
            # print(f"From ID:{guild.id}")

    if guild.system == "EPF" or guild.system == "RED" or guild.system == "STF":
        return await get_EPF_condition(ctx, id=id)
    else:
        tablename = f"Condition_{id}"

        DynamicBase = declarative_base(class_registry=dict())

        class Condition(DynamicBase):
            __tablename__ = tablename
            __table_args__ = {"extend_existing": True}

            id = Column(Integer(), primary_key=True, autoincrement=True)
            character_id = Column(Integer(), nullable=False)
            counter = Column(Boolean(), default=False)
            title = Column(String(), nullable=False)
            number = Column(Integer(), nullable=True, default=False)
            auto_increment = Column(Boolean(), nullable=False, default=False)
            time = Column(Boolean(), default=False)
            visible = Column(Boolean(), default=True)
            flex = Column(Boolean(), default=False)
            target = Column(Integer(), nullable=False)

        logging.info("get_condition: returning condition")
        return Condition


async def get_EPF_condition(ctx: discord.ApplicationContext, id=None):
    if ctx is None and id is None:
        raise Exception
    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global.id).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
            tablename = f"Condition_{guild}"
            logging.info(f"get_EPF_condition: Guild: {guild}")

    else:
        tablename = f"Condition_{id}"

    DynamicBase = declarative_base(class_registry=dict())

    class Condition(DynamicBase):
        __tablename__ = tablename
        __table_args__ = {"extend_existing": True}

        id = Column(Integer(), primary_key=True, autoincrement=True)
        character_id = Column(Integer(), nullable=False)
        counter = Column(Boolean(), default=False)
        title = Column(String(), nullable=False)
        number = Column(Integer(), nullable=True, default=False)
        auto_increment = Column(Boolean(), nullable=False, default=False)
        time = Column(Boolean(), default=False)
        visible = Column(Boolean(), default=True)
        flex = Column(Boolean(), default=False)
        action = Column(String(), default="")
        target = Column(Integer(), nullable=False)
        stable = Column(Boolean(), default=False)
        value = Column(Integer())
        eot_parse = Column(Boolean(), default=False)

    logging.info("get_condition: returning condition")
    return Condition


async def get_condition_table(ctx, metadata, guild=None):
    if guild is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
    if guild.system == "EPF" or guild.system == "STF" or guild.system == "RED":
        return EPF_Support.EPF_ConditionTable(ctx, metadata, guild.id).condition_table()

    table = ConditionTable(ctx, metadata, guild.id).condition_table()
    return table


class ConditionTable:
    def __init__(self, ctx, metadata, id):
        self.metadata = metadata
        self.id = id

    def condition_table(
        self,
    ):
        tablename = f"Condition_{self.id}"
        con = db.Table(
            tablename,
            self.metadata,
            db.Column("id", db.INTEGER(), autoincrement=True, primary_key=True),
            db.Column("character_id", db.INTEGER(), ForeignKey(f"Tracker_{self.id}.id")),
            db.Column("counter", db.BOOLEAN(), default=False),
            db.Column("title", db.String(255), nullable=False),
            db.Column("number", db.INTEGER(), nullable=True, default=None),
            db.Column("auto_increment", db.BOOLEAN, nullable=False, default=False),
            db.Column("time", db.BOOLEAN, default=False),
            db.Column("visible", db.BOOLEAN, default=True),
            db.Column("flex", db.BOOLEAN, default=False),
            db.Column("target", db.INTEGER()),
        )
        return con


#########################################
#########################################
# Macro Table


class Macro(Base):
    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id = Column(Integer(), primary_key=True, autoincrement=True)
    character_id = Column(Integer(), nullable=False)
    name = Column(String(), nullable=False, unique=False)
    macro = Column(String(), nullable=False, unique=False)


async def get_macro(ctx: discord.ApplicationContext, id=None):
    if ctx is None and id is None:
        raise Exception
    if id is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global.id).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()
            logging.info(f"get_macro: Guild: {guild}")
            tablename = f"Macro_{guild}"

    else:
        tablename = f"Macro_{id}"

    DynamicBase = declarative_base(class_registry=dict())

    class Macro(DynamicBase):
        __tablename__ = tablename
        __table_args__ = {"extend_existing": True}

        id = Column(Integer(), primary_key=True, autoincrement=True)
        character_id = Column(Integer(), nullable=False)
        name = Column(String(), nullable=False, unique=False)
        macro = Column(String(), nullable=False, unique=False)

    logging.info("get_macro: returning macro")
    return Macro


async def get_macro_table(ctx, metadata, guild=None):
    if guild is None:
        async with async_session() as session:
            result = await session.execute(
                select(Global).where(
                    or_(
                        Global.tracker_channel == ctx.interaction.channel_id,
                        Global.gm_tracker_channel == ctx.interaction.channel_id,
                    )
                )
            )
            guild = result.scalars().one()

    table = MacroTable(ctx, metadata, guild.id).macro_table()
    return table


class MacroTable:
    def __init__(self, ctx, metadata, id):
        self.guild = ctx.interaction.guild_id
        self.channel = ctx.interaction.channel_id
        self.metadata = metadata
        self.id = id

    def macro_table(self):
        tablename = f"Macro_{self.id}"
        macro = db.Table(
            tablename,
            self.metadata,
            db.Column("id", db.INTEGER(), autoincrement=True, primary_key=True),
            db.Column("character_id", db.INTEGER(), ForeignKey(f"Tracker_{self.id}.id")),
            db.Column("name", db.String(255), nullable=False, unique=False),
            db.Column("macro", db.String(255), nullable=False, unique=False),
        )
        return macro


class Character_Vault(Base):
    __tablename__ = "character_vault"
    # ID Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    guild_id = Column(Integer(), nullable=False)
    disc_guild_id = Column(BigInteger())
    system = Column(String(), default=None, nullable=True)
    name = Column(String(), nullable=False)
    user = Column(BigInteger(), nullable=False)


def disease_table(metadata):
    tablename = "disease"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("Type", db.Text()),
        db.Column("ID", db.INTEGER(), primary_key=True, autoincrement=False),
        db.Column("Title", db.String(255)),
        db.Column("URL", db.String(255), default=""),
    )
    return emp


def feat_table(metadata):
    tablename = "feat"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("Type", db.Text()),
        db.Column("ID", db.INTEGER(), primary_key=True, autoincrement=False),
        db.Column("Title", db.String(255)),
        db.Column("URL", db.String(255), default=""),
    )
    return emp


def power_table(metadata):
    tablename = "power"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("Type", db.Text()),
        db.Column("ID", db.INTEGER(), primary_key=True, autoincrement=False),
        db.Column("Title", db.String(255)),
        db.Column("URL", db.String(255), default=""),
    )
    return emp


def monster_table(metadata):
    tablename = "monster"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("Type", db.Text()),
        db.Column("ID", db.INTEGER(), primary_key=True, autoincrement=False),
        db.Column("Title", db.String(255)),
        db.Column("URL", db.String(255), default=""),
    )
    return emp


def item_table(metadata):
    tablename = "item"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("Type", db.Text()),
        db.Column("ID", db.INTEGER(), primary_key=True, autoincrement=False),
        db.Column("Title", db.String(255)),
        db.Column("Category", db.String(255)),
        db.Column("URL", db.String(255), default=""),
    )
    return emp


def ritual_table(metadata):
    tablename = "ritual"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("Type", db.Text()),
        db.Column("ID", db.INTEGER(), primary_key=True, autoincrement=False),
        db.Column("Title", db.String(255)),
        db.Column("URL", db.String(255), default=""),
    )
    return emp


# Global Class
class Reminder(Base):
    __tablename__ = "reminder_table"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    user = Column(String())
    guild_id = Column(BigInteger())
    channel = Column(BigInteger(), nullable=False, unique=False)
    message = Column(String(), nullable=False)
    timestamp = Column(Integer(), nullable=False)


def reminder_table(metadata):
    tablename = "reminder_table"
    emp = db.Table(
        tablename,
        metadata,
        db.Column("id", db.INTEGER(), primary_key=True, autoincrement=True),
        db.Column("user", db.String(255)),
        db.Column("guild_id", db.BigInteger()),
        db.Column("channel", db.BigInteger(), nullable=False, unique=False),
        db.Column("message", db.String(), nullable=False),
        db.Column("timestamp", db.INTEGER(), nullable=False),
    )
    return emp


class NPC(LookupBase):
    __tablename__ = "npc_data"
    # Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(), unique=True)
    level = Column(Integer())
    creatureType = Column(String())
    alignment = Column(String())
    ac = Column(Integer())
    hp = Column(Integer())
    init = Column(String())
    fort = Column(Integer())
    reflex = Column(Integer())
    will = Column(Integer())
    dc = Column(Integer())
    macros = Column(String())


class PF2_Lookup(LookupBase):
    __tablename__ = "pf2_lookup_data"
    # Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(), unique=True)
    endpoint = Column(String())
    data = Column(JSON())


class Log(RollLogBase):
    __tablename__ = "roll_log"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    guild_id = Column(Integer(), nullable=False)
    character = Column(String(), nullable=False)
    message = Column(String(), nullable=False)
    timestamp = Column(BigInteger())
    secret = Column(Boolean(), default=False)

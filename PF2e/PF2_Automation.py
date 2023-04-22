import logging

import d20
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from PF2e.pf2_functions import PF2_base_dc, PF2_eval_succss

from Base.Automation import Automation
from database_models import get_macro
from error_handling_reporting import error_not_initialized
from utils.Char_Getter import get_character
from utils.Macro_Getter import get_macro_object
from utils.parsing import ParseModifiers


class PF2_Automation(Automation):
    def __init__(self, ctx, engine, guild):
        super().__init__(ctx, engine, guild)

    async def attack(self, character, target, roll, vs, attack_modifier, target_modifier):
        # Strip a macro:
        roll_list = roll.split(":")
        # print(roll_list)
        if len(roll_list) == 1:
            roll = roll
        else:
            roll = roll_list[1]
        print(roll)
        try:
            Macro_Model = await get_macro_object(self.ctx, engine=self.engine, guild=self.guild)
            roll_string: str = f"({await Macro_Model.get_macro(character, roll)}){ParseModifiers(attack_modifier)}"
            dice_result = d20.roll(roll_string)
        except:
            roll_string: str = f"({roll}){ParseModifiers(attack_modifier)}"
            dice_result = d20.roll(roll_string)

        Target_Model = await get_character(target, self.ctx, guild=self.guild, engine=self.engine)
        con_vs = 0
        match vs:  # noqa
            case "AC":
                con_vs = Target_Model.ac
            case "Fort":
                con_vs = Target_Model.fort
            case "Reflex":
                con_vs = Target_Model.reflex
            case "Will":
                con_vs = Target_Model.will
            case "DC":
                con_vs = Target_Model.dc

        goal_value = con_vs + (PF2_base_dc if vs in ["Fort", "Will", "Reflex"] else 0)

        try:
            goal_string: str = f"({goal_value}){ParseModifiers(target_modifier)}"
            goal_result = d20.roll(goal_string)
        except Exception as e:
            logging.warning(f"attack: {e}")
            return "Error"

        # Format output string
        success_string = PF2_eval_succss(dice_result, goal_result)
        output_string = f"{character} rolls {roll} vs {target} {vs} {target_modifier}:\n{dice_result}\n{success_string}"
        return output_string

    async def save(self, character, target, save, dc, modifier):
        if target is None:
            output_string = "Error. No Target Specified."
            return output_string

        orig_dc = dc
        Character_Model = await get_character(character, self.ctx, engine=self.engine, guild=self.guild)
        Target_Model = await get_character(target, self.ctx, engine=self.engine, guild=self.guild)
        con_vs = 0
        match save:
            case "AC":
                con_vs = Target_Model.ac
            case "Fort":
                con_vs = Target_Model.fort
            case "Reflex":
                con_vs = Target_Model.reflex
            case "Will":
                con_vs = Target_Model.will
            case "DC":
                con_vs = Target_Model.dc

        try:
            roll = f"1d20+{con_vs}"
            # print(roll)

            if dc is None:
                dc = Character_Model.dc
                if Character_Model.dc is None:
                    dc = 0
            # print(dc)
            try:
                dice_result = d20.roll(roll)
                goal_string: str = f"{dc}{ParseModifiers(modifier)}"
                goal_result = d20.roll(goal_string)
            except Exception as e:
                logging.warning(f"attack: {e}")
                return False

            success_string = PF2_eval_succss(dice_result, goal_result)
            # Format output string
            if character == target:
                output_string = f"{character} makes a {save} save!\n{dice_result}\n{success_string if orig_dc else ''}"
            elif Character_Model.player == True:
                output_string = (
                    f"{target} makes a DC{dc} {save} save!\n{character} forced the"
                    f" save.\n{dice_result}\n{success_string}"
                )
            else:
                output_string = (
                    f"{target} makes a {save} save!\n{character} forced the save.\n{dice_result}\n{success_string}"
                )

        except NoResultFound:
            await self.ctx.channel.send(error_not_initialized, delete_after=30)
            return False
        except Exception as e:
            logging.warning(f"attack: {e}")
            return False

        return output_string
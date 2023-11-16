import logging
from math import floor

import d20
import discord
import lark
from lark import Lark
from sqlalchemy.exc import NoResultFound

from EPF.EPF_Character import EPF_Character, get_EPF_Character
from EPF.EPF_Support import EPF_Conditions
from EPF.EPF_resists import damage_calc_resist, roll_dmg_resist
from PF2e.pf2_functions import PF2_eval_succss
from database_operations import engine
from error_handling_reporting import error_not_initialized
from utils.Char_Getter import get_character
from utils.parsing import ParseModifiers
from utils.utils import get_guild


async def get_attack(character, attack_name, ctx, guild=None):
    guild = await get_guild(ctx, guild)
    CharacterModel = await get_character(character, ctx, guild=guild, engine=engine)
    try:
        attack_data = await CharacterModel.get_weapon(attack_name)
    except Exception:
        attack_data = ""
    return Attack(ctx, guild, CharacterModel, attack_name, attack_data)


class Attack:
    def __init__(self, ctx, guild, character: EPF_Character, attack_name: str, attack_data: dict):
        print("Initializing Attack")
        self.ctx = ctx
        self.guild = guild
        self.character = character
        self.attack_name = attack_name
        self.attack = attack_data
        self.output = None

        if type(attack_data) == dict:
            if "complex" in attack_data.keys():
                if attack_data["complex"]:
                    self.complex = True
                else:
                    self.complex = False
            else:
                self.complex = False
        else:
            self.complex = False

        if self.complex:
            self.attack_type = attack_data["type"]["value"]
        else:
            self.attack_type = None
        print("Success")

    def success_color(self, success_string):
        if success_string == "Critical Success":
            color = discord.Color.gold()
        elif success_string == "Success":
            color = discord.Color.green()
        elif success_string == "Failure":
            color = discord.Color.red()
        else:
            color = discord.Color.dark_red()

        return color

    async def format_output(self, Attack_Data, Target_Model: EPF_Character):
        if Attack_Data.dmg_string is not None:
            dmg_output_string = f"{self.character.char_name} damages {Target_Model.char_name} for:"
            for item in Attack_Data.dmg_string:
                dmg_output_string += f"\n{item['dmg_output_string']} {item['dmg_type'].title()}"
            await Target_Model.change_hp(Attack_Data.total_damage, heal=False, post=False)
            if Target_Model.player:
                output = (
                    f"{Attack_Data.output}\n{dmg_output_string}\n{Target_Model.char_name} damaged for"
                    f" {Attack_Data.output}.New HP: {Target_Model.current_hp}/{Target_Model.max_hp}"
                )
            else:
                output = (
                    f"{Attack_Data.output}\n{dmg_output_string}\n{Target_Model.char_name} damaged for"
                    f" {Attack_Data.total_damage}. {await Target_Model.calculate_hp()}"
                )
        else:
            output = Attack_Data.output

        embed = discord.Embed(
            title=f"{self.character.char_name} vs {Target_Model.char_name}",
            fields=[discord.EmbedField(name=self.attack_name.title(), value=output)],
            color=self.success_color(Attack_Data.success_string),
        )
        embed.set_thumbnail(url=self.character.pic)

        self.output = embed

    async def roll_attack(self, target, vs, attack_modifier, target_modifier):
        if self.complex:
            return await self.complex_attack(target, vs, attack_modifier, target_modifier)
        else:
            return await self.simple_attack(target, vs, attack_modifier, target_modifier)

    async def simple_attack(self, target, vs, attack_modifier, target_modifier):
        print("simple attack")
        try:
            roll_string: str = f"{self.attack_name}{ParseModifiers(attack_modifier)}"
            dice_result = d20.roll(roll_string)
        except Exception:
            roll_string = f"({await self.character.get_roll(self.attack_name)}){ParseModifiers(attack_modifier)}"
            dice_result = d20.roll(roll_string)

        opponent = await get_character(target, self.ctx, guild=self.guild, engine=engine)
        goal_value = await opponent.get_dc(vs)

        try:
            goal_string: str = f"{goal_value}{ParseModifiers(target_modifier)}"
            goal_result = d20.roll(goal_string)
        except Exception as e:
            logging.warning(f"attack: {e}")
            return "Error"

        success_string = PF2_eval_succss(dice_result, goal_result)
        output_string = (
            f"{self.character.char_name} rolls {self.attack_name} vs"
            f" {opponent.char_name} {vs} {target_modifier}:\n{dice_result}\n{success_string}"
        )

        Data = Attack_Data(None, 0, success_string, output_string)

        await self.format_output(Data, opponent)

        return self.output

    async def complex_attack(self, target, vs, attack_modifier, target_modifier):
        return []

    async def save(self, target, dc, modifier):
        if target is None:
            embed = discord.Embed(
                title=self.character.char_name,
                fields=[discord.EmbedField(name=self.attack_name, value="Invalid Target")],
            )
            self.output = embed
            return self.output

        opponent = await get_EPF_Character(target, self.ctx, guild=self.guild, engine=engine)

        orig_dc = dc

        if dc is None:
            dc = await self.character.get_dc("DC")
        try:
            dice_result = d20.roll(f"{await opponent.get_roll(self.attack_name)}{ParseModifiers(modifier)}")
            goal_result = d20.roll(f"{dc}")
        except Exception as e:
            logging.warning(f"attack: {e}")
            return False

        try:
            success_string = PF2_eval_succss(dice_result, goal_result)

            if self.character.char_name == target:
                output_string = (
                    f"{self.character.char_name} makes a"
                    f" {self.attack_name} save!\n{dice_result}\n{success_string if orig_dc else ''}"
                )
            else:
                output_string = (
                    f"{opponent.char_name} makes a {self.attack_name} save!\n{self.character.char_name} forced the"
                    f" save.\n{dice_result}\n{success_string}"
                )

            Data = Attack_Data(None, 0, success_string, output_string)
            await self.format_output(Data, opponent)

            return self.output

        except NoResultFound:
            await self.ctx.channel.send(error_not_initialized, delete_after=30)
            return False
        except Exception as e:
            logging.warning(f"attack: {e}")
            return False

    async def damage(self, target, modifier, healing, damage_type: str, crit=False):
        Target_Model = await get_character(target, self.ctx, engine=engine, guild=self.guild)
        weapon = None

        if self.complex:
            # TODO Add complex damage roll
            pass
        else:
            try:
                roll_result: d20.RollResult = d20.roll(f"({self.attack_name}){ParseModifiers(modifier)}")
                dmg = roll_result.total
                if not healing:
                    dmg = await damage_calc_resist(dmg, damage_type, Target_Model, weapon=weapon)
                roll_string = f"{roll_result} {damage_type}"
            except Exception:
                try:
                    dmg_output, total_damage = await roll_dmg_resist(
                        self.character, Target_Model, self.attack_name, crit, modifier, dmg_type_override=damage_type
                    )
                    roll_string = ""
                    for item in dmg_output:
                        roll_string += f"{item['dmg_output_string']} {item['dmg_type'].title()}\n"
                    dmg = total_damage
                except Exception:
                    try:
                        roll_result = d20.roll(
                            f"{await self.character.get_roll(self.attack_name)}{ParseModifiers(modifier)}"
                        )
                        dmg = roll_result.total
                        if not healing:
                            dmg = await damage_calc_resist(dmg, damage_type, Target_Model, weapon=weapon)
                        roll_string = f"{roll_result} {damage_type}"
                    except Exception:
                        roll_result = d20.roll("0 [Error]")
                        dmg = roll_result.total
                        roll_string = roll_result

        await Target_Model.change_hp(dmg, healing, post=False)
        output_string = (
            f"{self.character.char_name} {'heals' if healing else 'damages'}  {target} for: \n{roll_string}"
            f"\n{f'{dmg} Damage' if not healing else f'{dmg} Healed'}\n"
            f"{await Target_Model.calculate_hp()}"
        )

        Data = Attack_Data(None, dmg, None, output_string)

        await self.format_output(Data, Target_Model)

        return self.output

    async def auto(self, target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override):
        Target_Model = await get_character(target, self.ctx, engine=engine, guild=self.guild)

        if self.complex:
            Attack_Data = await self.auto_complex(
                target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override
            )
        else:
            Attack_Data = await self.auto_simple(
                target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override
            )

        await self.format_output(Attack_Data, Target_Model)

        return self.output

    async def auto_simple(self, target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override):
        Target_Model = await get_character(target, self.ctx, engine=engine, guild=self.guild)

        roll_string = f"({await self.character.get_roll(self.attack_name)})"
        dice_result = d20.roll(f"{roll_string}{ParseModifiers(attack_modifier)}")

        goal_value = Target_Model.ac_total
        try:
            goal_string: str = f"{goal_value}{ParseModifiers(target_modifier)}"
            goal_result = d20.roll(goal_string)
        except Exception as e:
            logging.warning(f"auto: {e}")
            return "Error"

        # Format output string

        success_string = PF2_eval_succss(dice_result, goal_result)
        attk_output_string = (
            f"{self.character.name} attacks"
            f" {Target_Model.char_name} {'' if target_modifier == '' else f'(AC {target_modifier})'} with their"
            f" {self.attack_name}:\n{dice_result}\n{success_string}"
        )

        # Damage
        if success_string == "Critical Success" and "critical-hits" not in Target_Model.resistance.keys():
            dmg_string, total_damage = await roll_dmg_resist(
                self.character,
                Target_Model,
                self.attack_name,
                True,
                flat_bonus=dmg_modifier,
                dmg_type_override=dmg_type_override,
            )
        elif success_string == "Success" or success_string == "Critical Success":
            dmg_string, total_damage = await roll_dmg_resist(
                self.character,
                Target_Model,
                self.attack_name,
                False,
                flat_bonus=dmg_modifier,
                dmg_type_override=dmg_type_override,
            )
        else:
            dmg_string = None
            total_damage = 0

        return Attack_Data(dmg_string, total_damage, success_string, attk_output_string)

    async def auto_complex(self, target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override):
        print("Complex Attack")
        print(self.attack)

        if self.attack_type == "attack":
            return await self.auto_complex_attack(
                target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override
            )

    async def auto_complex_attack(self, target, attack_modifier, target_modifier, dmg_modifier, dmg_type_override):
        Target_Model = await get_EPF_Character(target, self.ctx, guild=self.guild, engine=engine)
        roll_string = f"({await self.character.get_roll('class_dc')})"
        print(roll_string)
        dice_result = d20.roll(f"{roll_string}{ParseModifiers(attack_modifier)}")
        print(dice_result)
        goal_value = Target_Model.ac_total

        try:
            goal_string: str = f"{goal_value}{ParseModifiers(target_modifier)}"
            goal_result = d20.roll(goal_string)
        except Exception as e:
            logging.warning(f"auto: {e}")
            return "Error"

        success_string = PF2_eval_succss(dice_result, goal_result)

        attk_output_string = (
            f"{self.character.char_name} attacks"
            f" {target} {'' if target_modifier == '' else f'(AC {target_modifier})'} with their"
            f" {self.attack_name.title()}:\n{dice_result}\n{success_string}"
        )

        # heightening code
        if "heighten" in self.attack.keys():
            print("Heightening")
            print(self.character.character_model.level)
            print(self.attack["lvl"])
            if self.character.character_model.level > self.attack["lvl"]:
                heighten = floor(
                    (self.character.character_model.level - self.attack["lvl"]) / self.attack["heighten"]["interval"]
                )
            else:
                heighten = 0

            print(heighten)

            if heighten > 0:
                heighten_data = await automation_parse(self.attack["heighten"]["effect"], Target_Model)
                print(heighten_data)
        else:
            heighten = 0

        if success_string == "Critical Success":
            if "critical success" in self.attack["effect"].keys():
                data = await automation_parse(self.attack["effect"]["critical success"], Target_Model)
                print(data)
                if heighten > 0:
                    for x in range(0, heighten + 1):
                        for i in heighten_data["dmg"].keys():
                            print(i)
                            data["dmg"][i] = str(data["dmg"][i]) + f"+{heighten_data['dmg'][i]}"

                dmg_string, total_damage = await scripted_damage_roll_resists(
                    data, Target_Model, crit=True, flat_bonus=dmg_modifier, dmg_type_override=dmg_type_override
                )
            else:
                data = await automation_parse(self.attack["effect"]["success"], Target_Model)
                print(data)
                if heighten > 0:
                    for x in range(0, heighten + 1):
                        for i in heighten_data["dmg"].keys():
                            print(i)
                            data["dmg"][i] = str(data["dmg"][i]) + f"+{heighten_data['dmg'][i]}"

                dmg_string, total_damage = await scripted_damage_roll_resists(
                    data, Target_Model, crit=True, flat_bonus=dmg_modifier, dmg_type_override=dmg_type_override
                )

        elif success_string == "Success":
            data = await automation_parse(self.attack["effect"]["success"], Target_Model)
            print(data)
            if heighten > 0:
                for x in range(0, heighten):
                    for i in heighten_data["dmg"].keys():
                        print(i)
                        data["dmg"][i] = str(data["dmg"][i]) + f"+{heighten_data['dmg'][i]}"
            print(data)
            dmg_string, total_damage = await scripted_damage_roll_resists(
                data, Target_Model, crit=False, flat_bonus=dmg_modifier, dmg_type_override=dmg_type_override
            )

        else:
            dmg_string = None
            total_damage = 0

        return Attack_Data(dmg_string, total_damage, success_string, attk_output_string)


class Attack_Data:
    def __init__(self, dmg_string, total_damage, success_string, attack_output_string):
        self.dmg_string = dmg_string
        self.total_damage = total_damage
        self.success_string = success_string
        self.output = attack_output_string

    def __str__(self):
        return self.output

    def __int__(self):
        return self.total_damage

    def __float__(self):
        return self.total_damage


attack_grammer = """
start: phrase+

phrase: value+ break

value: roll_string WORD                                                -> damage_string
    | persist_dmg
    | WORD NUMBER?                                                     -> new_condition

persist_dmg : ("persistent dmg" | "pd") roll_string WORD* ["/" "dc" NUMBER save_string]

modifier: SIGNED_INT

quoted: SINGLE_QUOTED_STRING
    | DOUBLE_QUOTED_STRING

break: ","


roll_string: ROLL (POS_NEG ROLL)* [POS_NEG NUMBER]
!save_string: "reflex" | "fort" | "will" | "flat"

ROLL: NUMBER "d" NUMBER

POS_NEG : ("+" | "-")

DOUBLE_QUOTED_STRING  : /"[^"]*"/
SINGLE_QUOTED_STRING  : /'[^']*'/

SPECIFIER : "c" | "s" | "i" | "r" | "w"
VARIABLE : "+x" | "-x"


COMBO_WORD : WORD ("-" |"_") WORD
%import common.ESCAPED_STRING
%import common.WORD
%import common.SIGNED_INT
%import common.NUMBER
%import common.WS
%ignore WS
"""


async def automation_parse(data, target_model):
    processed_data = {}
    try:
        if data[-1:] != ",":
            data = data + ","

        tree = Lark(attack_grammer).parse(data)
        print(tree.pretty())
        processed_data = await parse_automation_tree(tree, processed_data, target_model)
    except Exception:
        processed_input = data.split(",")
        for item in processed_input:
            # try:
            if data[-1:] != ",":
                data = data + ","

            tree = Lark(attack_grammer).parse(data)
            print(tree.pretty())
            processed_data = await parse_automation_tree(tree, processed_data, target_model)
            # except Exception as e:
            #     logging.error(f"Bad input: {item}: {e}")

    return processed_data


async def parse_automation_tree(tree, data: dict, target_model):
    t = tree.iter_subtrees_topdown()
    for branch in t:
        if branch.data == "new_condition":
            # TODO Update syntax to allow duration and data etc in new conditions.
            #  This can then be put back into the condition parser
            new_con_name = ""
            num = 0
            for item in branch.children:
                if item.type == "WORD":
                    new_con_name = item.value
                elif item.type == "NUMBER":
                    num = item.value

            if new_con_name.title() in EPF_Conditions.keys():
                if new_con_name.title() not in await target_model.conditions():
                    await target_model.set_cc(new_con_name.title(), False, num, "Round", False)

                data["condition"] = new_con_name

        elif branch.data == "persist_dmg":
            temp = {}
            for item in branch.children:
                if type(item) == lark.Tree:
                    if item.data == "roll_string":
                        roll_string = ""
                        for sub in item.children:
                            if sub is not None:
                                roll_string = roll_string + sub.value

                        temp["roll_string"] = roll_string
                    elif item.data == "save_string":
                        for sub in item.children:
                            temp["save"] = sub.value
                elif type(item) == lark.Token:
                    if item.type == "WORD":
                        temp["dmg_type"] = item.value
                    elif item.type == "NUMBER":
                        temp["save_value"] = item.value
            data["pd"] = temp

        elif branch.data == "damage_string":
            if "dmg" not in data.keys():
                data["dmg"] = {}

            temp = {}
            for item in branch.children:
                # print(item)
                if type(item) == lark.Tree:
                    if item.data == "roll_string":
                        roll_string = ""
                        for sub in item.children:
                            if sub is not None:
                                roll_string = roll_string + sub.value

                        temp["roll_string"] = roll_string
                elif type(item) == lark.Token:
                    if item.type == "WORD":
                        temp["dmg_type"] = item.value

            if temp["dmg_type"] is not None and temp["roll_string"] is not None:
                data["dmg"][temp["dmg_type"]] = temp["roll_string"]

    return data


async def scripted_damage_roll_resists(data: dict, Target_Model, crit: bool, flat_bonus="", dmg_type_override=None):
    dmg_output = []
    total_damage = 0
    for x, key in enumerate(data["dmg"]):
        dmg_string = f"({data['dmg'][key]}{ParseModifiers(flat_bonus) if x == 0 else ''}){'*2' if crit else ''}"
        damage_roll = d20.roll(dmg_string)

        if dmg_type_override == "":
            dmg_type_override = None
        if dmg_type_override is not None:
            base_dmg_type = dmg_type_override
        else:
            base_dmg_type = key
        total_damage += await damage_calc_resist(damage_roll.total, base_dmg_type, Target_Model)
        dmg_output_string = f"{damage_roll}"
        output = {"dmg_output_string": dmg_output_string, "dmg_type": base_dmg_type}
        dmg_output.append(output)

    return dmg_output, total_damage

import datetime
import json
import logging
import os
import time

from . import utils

removed_items = ["component", "consumable", "ignore"]
categorized_items = ["early", "risky", "team"]

logger = logging.getLogger(__name__)


def _normalise_neutral_items(neutral_items: dict):
    neutral_items_by_tier = {}

    if not isinstance(neutral_items, dict):
        return neutral_items_by_tier

    for tier in range(1, 6):
        tier_key = f"tier_{tier}"
        tier_items = []
        for item in neutral_items.get(tier_key, []):
            if isinstance(item, dict):
                item = item.get("guide_name") or item.get("item")
            if item:
                tier_items.append(item)
        neutral_items_by_tier[tier] = tier_items

    return neutral_items_by_tier


def _write_item_block(file, block_name: str, items: list, indent=2):
    tabs = "\t" * indent
    file.write(f'{tabs}"{block_name}"\n{tabs}{{\n')
    for item in items:
        file.write(f'{tabs}\t"item"\t\t"{item}"\n')
    file.write(f"{tabs}}}\n")


def _neutral_item_block_name(tier: int) -> str:
    return f"NEUTRAL TIER {tier}"


def compile_scrape_to_guide_vdf(hero_id: str, items_by_name: dict, heroes_map: dict, keep_starting_items=False):
    """Compiles a json file in `data` directory into the Valve Data File (VDF) format in `itembuilds` directory.

    Args:
        hero_id (str): Hero's id.
        keep_starting_items (int, optional): Removes `starting items` category & injects impactful progression items into `early game` category. Defaults to 0.
    """
    removed_item_flags = removed_items.copy()
    if not keep_starting_items:
        removed_item_flags.append("start")
    with open(f"{os.path.join(utils.data_directory, hero_id)}.json") as f:
        hero_data = json.load(f)
    neutral_items = _normalise_neutral_items(hero_data.get(utils.neutral_items_key, {}))
    ability_upgrades = hero_data.get(utils.ability_upgrades_key, [])

    hero_info = heroes_map.get(hero_id, {})
    localized_name = hero_info.get("localized_name", "")
    guide_name = hero_info.get("guide_name")
    if not guide_name:
        return
    hero_name = guide_name.removeprefix("default_")
    author = utils.project_name
    title = f"{utils.project_name_shorthand} {localized_name} {datetime.date.today().isoformat()}"
    hero_stages = []
    for stage in hero_data:
        if stage == utils.neutral_items_key:
            continue
        hero_stage = []
        for item in hero_data[stage]:
            hero_stage.append(item)
        hero_stages.append(hero_stage)

    hero_stages = utils.remove_repeated_elements(hero_stages)
    modified_hero_stages = []
    team_category = []
    risky_category = []
    early_category = []
    for stage in hero_stages:
        modified_hero_stage = []
        for item in stage:
            if items_by_name.get(item, {}).get("cost", 0) > 0:
                item_flags = items_by_name.get(item, {}).get("flag", "")
                if item_flags not in removed_item_flags and "recipe" not in item:
                    if item_flags == "team":
                        team_category.append(item)
                    elif item_flags == "risky":
                        risky_category.append(item)
                    elif item_flags == "early":
                        if not keep_starting_items:
                            early_category.append(item)
                        else:
                            modified_hero_stage.append(item)
                    else:
                        modified_hero_stage.append(item)
        modified_hero_stage = sorted(
            modified_hero_stage,
            key=lambda item: items_by_name.get(item, {}).get("cost", 0),
        )
        modified_hero_stages.append(modified_hero_stage)
    while len(modified_hero_stages) < 4:
        logger.warning("Hero %s has fewer shop item stages than expected.", hero_id)
        modified_hero_stages.append([])
    team_category = sorted(
        team_category,
        key=lambda item: items_by_name.get(item, {}).get("cost", 0),
    )
    risky_category = sorted(
        risky_category,
        key=lambda item: items_by_name.get(item, {}).get("cost", 0),
    )
    early_category = sorted(
        early_category,
        key=lambda item: items_by_name.get(item, {}).get("cost", 0),
    )

    timestamp = 1779000000
    hex_timestamp = hex(timestamp)[2:].upper()
    time_updated_str = f"0x00000000{hex_timestamp}"

    with open(os.path.join(utils.itembuilds_directory, f"{hero_name}_{timestamp}.build"), "w", newline="") as file:
        file.write('"guidedata"\n{\n')
        file.write(f'\t"Hero"\t\t"{hero_name}"\n')
        file.write(f'\t"Title"\t\t"{title}"\n')
        file.write('\t"Role"\t\t"#DOTA_HeroGuide_Role_Core"\n')
        file.write('\t"GameplayVersion"\t\t"7.41c"\n')
        file.write('\t"Overview"\t\t""\n')
        file.write('\t"GuideRevision"\t\t"1"\n')
        file.write('\t"AssociatedWorkshopItemID"\t\t"0x0000000000000000"\n')
        file.write('\t"OriginalCreatorID"\t\t"0x0000000000000000"\n')
        file.write('\t"GuideFormatVersion"\t\t"2"\n')
        file.write(f'\t"TimeUpdated"\t\t"{time_updated_str}"\n')
        file.write('\t"TimePublished"\t\t"0x0000000000000000"\n')
        file.write('\t"ItemBuild"\n\t{\n')
        file.write('\t\t"Items"\n\t\t{\n')
        _write_item_block(file, "#DOTA_Item_Build_Starting_Items", modified_hero_stages[0], indent=3)
        _write_item_block(file, "#DOTA_Item_Build_Early_Game", early_category + modified_hero_stages[1], indent=3)
        _write_item_block(file, "#DOTA_Item_Build_Mid_Items", modified_hero_stages[2], indent=3)
        _write_item_block(file, "#DOTA_Item_Build_Late_Items", modified_hero_stages[3], indent=3)
        if team_category != []:
            _write_item_block(file, "TEAM UTILITIES", team_category, indent=3)
        if risky_category != []:
            _write_item_block(file, "RISKY", risky_category, indent=3)
        for tier, items in neutral_items.items():
            _write_item_block(file, _neutral_item_block_name(tier), items, indent=3)
        file.write("\t\t}\n")
        file.write('\t\t"ItemTooltips"\n\t\t{\n\t\t}\n')
        file.write("\t}\n")
        file.write('\t"AbilityBuild"\n\t{\n')
        file.write('\t\t"AbilityOrder"\n\t\t{\n')
        for i, ability in enumerate(ability_upgrades, start=1):
            if ability:
                file.write(f'\t\t\t"{i}"\t\t"{ability}"\n')
        file.write('\t\t}\n')
        file.write('\t\t"AbilityTooltips"\n\t\t{\n\t\t}\n')
        file.write("\t}\n")
        file.write("}\n")

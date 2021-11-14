
import zipfile, yaml, io, json, os, sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

from pathlib import Path
from List.configDict import itemType, locationCategory,locationType
from Module.RandomizerSettings import RandomizerSettings
from Module.hints import Hints
from Module.newRandomize import Randomizer
from Class.itemClass import ItemEncoder
from Class.modYml import modYml
from Module.randomBGM import RandomBGM
from Module.randomCmdMenu import RandomCmdMenu
from Module.spoilerLog import generateSpoilerLog


def noop(self, *args, **kw):
    pass

class SeedZip():
    def __init__(self,settings: RandomizerSettings, randomizer: Randomizer, hints, cosmetics_data):
        self.formattedTrsr = {}
        self.formattedLvup = {"Sora":{}}
        self.formattedBons = {}
        self.formattedFmlv = {}
        self.formattedItem = {"Stats":[]}
        self.formattedPlrp = []

        self.assignTreasures(randomizer)
        self.assignLevels(randomizer)
        self.assignSoraBonuses(randomizer)
        self.assignDonaldBonuses(randomizer)
        self.assignGoofyBonuses(randomizer)
        self.assignFormLevels(randomizer)
        self.assignWeaponStats(randomizer)
        self.assignStartingItems(settings, randomizer)
        self.createZip(settings, randomizer, hints, cosmetics_data)

    def createZip(self, settings, randomizer, hints, cosmetics_data):
        mod = modYml.getDefaultMod()
        sys = modYml.getSysYAML(settings.seedHashIcons)

        data = io.BytesIO()
        with zipfile.ZipFile(data,"w") as outZip:
            yaml.emitter.Emitter.process_tag = noop


            #TODO This may need adjusting for the exe, since the "static" version doesn't work for whatever reason
            path_to_static = Path("../static")
            # if not path_to_static.exists():
            #     path_to_static = Path("../static")

            if locationType.Puzzle not in settings.disabledLocations:
                mod["assets"] += [modYml.getPuzzleMod()]
                assignedPuzzles = self.getAssignmentSubsetFromType(randomizer.assignedItems,[locationType.Puzzle])
                with open(resource_path(path_to_static/Path("jiminy.bar")),"rb") as puzzleBar:
                    binaryContent = bytearray(puzzleBar.read())
                    for puzz in assignedPuzzles:
                        byte0 = 24420+puzz.location.LocationId*16
                        byte1 = 24420+puzz.location.LocationId*16+1
                        item = puzz.item.Id
                        
                        # for byte1, find the most significant bits from the item Id
                        itemByte1 = item>>8
                        # for byte0, isolate the least significant bits from the item Id
                        itemByte0 = item & 0x00FF
                        binaryContent[byte0] = itemByte0
                        binaryContent[byte1] = itemByte1
                    outZip.writestr("modified_jiminy.bar",binaryContent)

            outZip.writestr("TrsrList.yml", yaml.dump(self.formattedTrsr, line_break="\r\n"))
            outZip.writestr("BonsList.yml", yaml.dump(self.formattedBons, line_break="\r\n"))
            outZip.writestr("LvupList.yml", yaml.dump(self.formattedLvup, line_break="\r\n"))
            outZip.writestr("FmlvList.yml", yaml.dump(self.formattedFmlv, line_break="\r\n"))
            outZip.writestr("ItemList.yml", yaml.dump(self.formattedItem, line_break="\r\n"))
            outZip.writestr("PlrpList.yml", yaml.dump(self.formattedPlrp, line_break="\r\n"))
            outZip.writestr("sys.yml", yaml.dump(sys, line_break="\r\n"))
            outZip.writestr("jm.yml", yaml.dump(modYml.getJMYAML(), line_break="\r\n"))

            if hints is not None:
                Hints.writeHints(hints, settings.random_seed, outZip)

            cmdMenuChoice = cosmetics_data["cmdMenuChoice"]
            platform = cosmetics_data["platform"]
            randomBGMOptions = cosmetics_data["randomBGM"]

            enemySpoilers = None
            if not settings.enemy_options["boss"] == "Disabled" or not settings.enemy_options["enemy"] == "Disabled" or settings.enemy_options["remove_damage_cap"]:
                if platform == "PC":
                    settings.enemy_options["memory_expansion"] = True
                else:
                    settings.enemy_options["memory_expansion"] = False
                if settings.enemy_options.get("boss", False) or settings.enemy_options.get("enemy", False) or settings.enemy_options.get("remove_damage_cap", False):
                    from khbr.randomizer import Randomizer as khbr
                    enemySpoilers = khbr().generateToZip("kh2", settings.enemy_options, mod, outZip)

            if settings.spoiler_log:
                mod["title"] += " w/ Spoiler"
                with open(resource_path(Path("../static/spoilerlog.html"))) as spoiler_site:
                    html_template = spoiler_site.read().replace("SPOILER_JSON_FROM_SEED",json.dumps(generateSpoilerLog(randomizer.assignedItems), indent=4, cls=ItemEncoder))
                    outZip.writestr("spoilerlog.html",html_template)
                if enemySpoilers:
                    outZip.writestr("enemyspoilers.txt", enemySpoilers)


            mod["assets"] += RandomCmdMenu.randomizeCmdMenus(cmdMenuChoice, outZip, platform)
            mod["assets"] += RandomBGM.randomizeBGM(randomBGMOptions, platform)

            outZip.write(resource_path(path_to_static/Path("icon.png")), "icon.png")
            outZip.writestr("mod.yml", yaml.dump(mod, line_break="\r\n"))
            outZip.close()
        data.seek(0)
        self.outputZip = data

    def assignStartingItems(self, settings, randomizer):
        def padItems(itemList):
            while(len(itemList)<32):
                itemList.append(0)

        donaldStartingItems = [1+0x8000,3+0x8000]+[l.item.Id for l in self.getAssignmentSubsetFromType(randomizer.assignedDonaldItems,[locationType.Free])]
        padItems(donaldStartingItems)
        self.formattedPlrp.append({
            "Character": 2, # Donald Starting Items
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": 0 if settings.no_ap else 50,
            "ArmorSlotMax": 1,
            "AccessorySlotMax": 2,
            "ItemSlotMax": 2,
            "Items": donaldStartingItems,
            "Padding": [0] * 52
        })

        goofyStartingItems = [1+0x8000,1+0x8000,1+0x8000,]+[l.item.Id for l in self.getAssignmentSubsetFromType(randomizer.assignedGoofyItems,[locationType.Free])]
        padItems(goofyStartingItems)
        self.formattedPlrp.append({
            "Character": 3, # Goofy Starting Items
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": 0 if settings.no_ap else 50,
            "ArmorSlotMax": 2,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 3,
            "Items": goofyStartingItems,
            "Padding": [0] * 52
        })

        soraStartingItems = [l.item.Id for l in self.getAssignmentSubsetFromType(randomizer.assignedItems,[locationType.Critical])] + settings.startingItems
        padItems(soraStartingItems)
        self.formattedPlrp.append({
            "Character": 1, # Sora Starting Items (Non Crit)
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": 0 if settings.no_ap else 50,
            "ArmorSlotMax": 2,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 3,
            "Items": soraStartingItems[7:],
            "Padding": [0] * 52
        })
        self.formattedPlrp.append({
            "Character": 1, # Sora Starting Items (Crit)
            "Id": 7, # crit difficulty
            "Hp": 20,
            "Mp": 100,
            "Ap": 0 if settings.no_ap else 50,
            "ArmorSlotMax": 2,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 3,
            "Items": soraStartingItems[:7],
            "Padding": [0] * 52
        })
        self.formattedPlrp.append({
            "Character": 135, # Lion Dash on Lion Sora
            "Id": 0,
            "Hp": 0,
            "Mp": 0,
            "Ap": 0,
            "ArmorSlotMax": 0,
            "AccessorySlotMax": 0,
            "ItemSlotMax": 0,
            "Items": [32930, 32930, 32931, 32931, 33288, 33289, 33290, 33294],
            "Padding": [0] * 52
        })


    def assignWeaponStats(self, randomizer):
        weapons = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.WEAPONSLOT]) + \
            self.getAssignmentSubset(randomizer.assignedDonaldItems,[locationCategory.WEAPONSLOT]) + \
            self.getAssignmentSubset(randomizer.assignedGoofyItems,[locationCategory.WEAPONSLOT])
        
        for weapon in weapons:
            if "Struggle" in weapon.location.Description:
                continue
            weaponStats = [stat for stat in randomizer.weaponStats if stat.location==weapon.location][0]
            self.formattedItem["Stats"].append({
                "Id": weapon.location.LocationId,
                "Attack": weaponStats.strength,
                "Magic": weaponStats.magic,
                "Defense": 0,
                "Ability": weapon.item.Id,
                "AbilityPoints": 0,
                "Unknown08": 100,
                "FireResistance": 100,
                "IceResistance": 100,
                "LightningResistance": 100,
                "DarkResistance": 100,
                "Unknown0d": 100,
                "GeneralResistance": 100,
                "Unknown": 0
            })




    def assignFormLevels(self, randomizer):
        formDict = {0:"Summon", 1:"Valor",2:"Wisdom",3:"Limit",4:"Master",5:"Final"}
        for index,levelType in enumerate([locationCategory.SUMMONLEVEL,locationCategory.VALORLEVEL,locationCategory.WISDOMLEVEL,locationCategory.LIMITLEVEL,locationCategory.MASTERLEVEL,locationCategory.FINALLEVEL]):
            levels = self.getAssignmentSubset(randomizer.assignedItems,[levelType])
            formName = formDict[index]
            self.formattedFmlv[formName] = []
            for lvl in levels:
                formExp = [l for l in randomizer.formLevelExp if l == lvl.location][0]
                self.formattedFmlv[formName].append({
                    "Ability": lvl.item.Id,
                    "Experience": formExp.experience,
                    "FormId": index,
                    "FormLevel": lvl.location.LocationId,
                    "GrowthAbilityLevel": 0,
                })

    def assignGoofyBonuses(self, randomizer):
        goofyBonuses = self.getAssignmentSubset(randomizer.assignedGoofyItems,[locationCategory.DOUBLEBONUS,locationCategory.HYBRIDBONUS,locationCategory.ITEMBONUS,locationCategory.STATBONUS])
        for bon in goofyBonuses:
            if not bon.location.LocationId in self.formattedBons.keys():
                self.formattedBons[bon.location.LocationId] = {}
            charId = 3 # Goofy id
            charName = "Goofy"
            item1 = 0
            item2 = 0
            item1 = bon.item.Id
            if bon.item2 is not None:
                item2 = bon.item2.Id
            self.formattedBons[bon.location.LocationId][charName] = {
                "RewardId": bon.location.LocationId,
                "CharacterId": charId,
                "HpIncrease": 0,
                "MpIncrease": 0,
                "DriveGaugeUpgrade": 0,
                "ItemSlotUpgrade": 0,
                "AccessorySlotUpgrade": 0,
                "ArmorSlotUpgrade": 0,
                "BonusItem1": item1,
                "BonusItem2": item2,
                "Padding": 0
            }

    def assignDonaldBonuses(self, randomizer):
        donaldBonuses = self.getAssignmentSubset(randomizer.assignedDonaldItems,[locationCategory.DOUBLEBONUS,locationCategory.HYBRIDBONUS,locationCategory.ITEMBONUS,locationCategory.STATBONUS])
        for bon in donaldBonuses:
            if not bon.location.LocationId in self.formattedBons.keys():
                self.formattedBons[bon.location.LocationId] = {}
            charId = 2 # Donald id
            charName = "Donald"
            item1 = 0
            item2 = 0
            item1 = bon.item.Id
            if bon.item2 is not None:
                item2 = bon.item2.Id
            self.formattedBons[bon.location.LocationId][charName] = {
                "RewardId": bon.location.LocationId,
                "CharacterId": charId,
                "HpIncrease": 0,
                "MpIncrease": 0,
                "DriveGaugeUpgrade": 0,
                "ItemSlotUpgrade": 0,
                "AccessorySlotUpgrade": 0,
                "ArmorSlotUpgrade": 0,
                "BonusItem1": item1,
                "BonusItem2": item2,
                "Padding": 0
            }

    def assignSoraBonuses(self, randomizer):
        soraBonuses = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.DOUBLEBONUS,locationCategory.HYBRIDBONUS,locationCategory.ITEMBONUS,locationCategory.STATBONUS])
        for bon in soraBonuses:
            if not bon.location.LocationId in self.formattedBons.keys():
                self.formattedBons[bon.location.LocationId] = {}
            charId = 1 # Sora id
            charName = "Sora"
            if locationType.STT in bon.location.LocationTypes:
                charId = 14 # roxas id
                charName = "Roxas"

            #determine if assigned item is a stat bonus, and if so, use the bonuses native stat update
            hpIncrease = 0
            mpIncrease = 0
            driveIncrease = 0
            itemIncrease = 0
            accessoryIncrease = 0
            armorIncrease = 0
            item1 = 0
            item2 = 0
            if bon.item.ItemType == itemType.STAT:
                if bon.item.Id == 470: # HP increase
                    hpIncrease+=5
                if bon.item.Id == 471: # MP increase
                    mpIncrease+=10
                if bon.item.Id == 472: # Drive increase
                    driveIncrease+=1
                if bon.item.Id == 473: # Armor increase
                    armorIncrease+=1
                if bon.item.Id == 474: # Accessory increase
                    accessoryIncrease+=1
                if bon.item.Id == 463: # Item increase
                    itemIncrease+=1
            else:
                item1 = bon.item.Id
            if bon.item2 is not None and bon.item2.ItemType==itemType.STAT:
                if bon.item2.Id == 470: # HP increase
                    hpIncrease+=5
                if bon.item2.Id == 471: # MP increase
                    mpIncrease+=10
                if bon.item2.Id == 472: # Drive increase
                    driveIncrease+=1
                if bon.item2.Id == 473: # Armor increase
                    armorIncrease+=1
                if bon.item2.Id == 474: # Accessory increase
                    accessoryIncrease+=1
                if bon.item2.Id == 463: # Item increase
                    itemIncrease+=1
            elif bon.item2 is not None:
                item2 = bon.item2.Id


            self.formattedBons[bon.location.LocationId][charName] = {
                "RewardId": bon.location.LocationId,
                "CharacterId": charId,
                "HpIncrease": hpIncrease,
                "MpIncrease": mpIncrease,
                "DriveGaugeUpgrade": driveIncrease,
                "ItemSlotUpgrade": itemIncrease,
                "AccessorySlotUpgrade": accessoryIncrease,
                "ArmorSlotUpgrade": armorIncrease,
                "BonusItem1": item1,
                "BonusItem2": item2,
                "Padding": 0
            }



    def assignLevels(self, randomizer):
        levels = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.LEVEL])

        for lvup in levels:
            levelStats = [lv for lv in randomizer.levelStats if lv.location==lvup.location][0]
            if lvup.item is None:
                item_id = 0
            else:
                item_id = lvup.item.Id
            self.formattedLvup["Sora"][lvup.location.LocationId] = {
                "Exp": levelStats.experience,
                "Strength": levelStats.strength,
                "Magic": levelStats.magic,
                "Defense": levelStats.defense,
                "Ap": levelStats.ap,
                "SwordAbility": item_id,
                "ShieldAbility": item_id,
                "StaffAbility": item_id,
                "Padding": 0,
                "Character": "Sora",
                "Level": lvup.location.LocationId
            }



    def assignTreasures(self, randomizer):
        treasures = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.POPUP,locationCategory.CHEST])
        treasures = [trsr for trsr in treasures if locationType.Puzzle not in trsr.location.LocationTypes]

        for trsr in treasures:
            self.formattedTrsr[trsr.location.LocationId] = {"ItemId":trsr.item.Id}
    
    def getAssignmentSubset(self,assigned,categories : list[locationCategory]):
        return [assignment for assignment in assigned if any(item is assignment.location.LocationCategory for item in categories)]

    def getAssignmentSubsetFromType(self,assigned,types):
        return [assignment for assignment in assigned if any(item in assignment.location.LocationTypes for item in types)]
from pbge import Singleton
import color
import jobs
import tags
import random
import personality

FR_ENEMY = "ENEMY"

class Faction(Singleton):
    name = "Faction"
    factags = ()
    mecha_colors = (color.AceScarlet, color.CometRed, color.HotPink, color.Black, color.LunarGrey)
    CAREERS = {
        tags.Trooper: ("Mecha Pilot",),
        tags.Commander: ("Commander",),
        tags.Support: ("Mecha Pilot",),
    }
    LOCATIONS = ()
    NAME_PATTERNS = ("the {number} {noun}","the {adjective} {noun}")
    NAME_PAT_WITH_CITY = ("the {number} {noun} of {city}",)
    ADJECTIVES = ("Whatever",)
    NOUNS = ("Circle",)
    uniform_colors = (None,None,None,None,None)
    @classmethod
    def get_faction_tag(cls):
        return cls
    @classmethod
    def choose_job(cls,role):
        candidates = cls.CAREERS.get(role)
        if candidates:
            job = jobs.ALL_JOBS[random.choice(candidates)]
        else:
            job = jobs.ALL_JOBS["Mecha Pilot"]
        return job
    @classmethod
    def choose_location(cls):
        if cls.LOCATIONS:
            return random.choice(cls.LOCATIONS)
    ORDINALS = ("1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th","11th","12th","13th")
    @classmethod
    def get_circle_name(cls,city=None):
        sub_dic = {
            "number": random.choice(cls.ORDINALS),
            "adjective": random.choice(cls.ADJECTIVES),
            "noun": random.choice(cls.NOUNS)
        }
        candidates = list(cls.NAME_PATTERNS)
        if city:
            candidates += list(cls.NAME_PAT_WITH_CITY)
            sub_dic["city"] = str(city)
        return random.choice(candidates).format(**sub_dic)


class AegisOverlord(Faction):
    name = "Aegis Overlord Luna"
    factags = (tags.Politician, tags.Military)
    mecha_colors = (color.LunarGrey, color.AegisCrimson, color.LemonYellow, color.CeramicColor, color.LunarGrey)
    CAREERS = {
        tags.Trooper: ("Mecha Pilot",),
        tags.Commander: ("Commander",),
        tags.Support: ("Mecha Pilot",),
    }
    LOCATIONS = (personality.Luna,)
    ADJECTIVES = ("Expedition","Strike Force")
    NOUNS = ("Aegis","Lunar")
    uniform_colors = (color.LunarGrey,None,None,None,color.AegisCrimson)


class BladesOfCrihna(Faction):
    name = "the Blades of Crihna"
    factags = (tags.Criminal,)
    mecha_colors = (color.HeavyPurple, color.SeaGreen, color.PirateSunrise, color.Black, color.StarViolet)
    LOCATIONS = (personality.L5DustyRing,)
    CAREERS = {
        tags.Trooper: ("Pirate","Thief"),
        tags.Commander: ("Pirate Captain",),
        tags.Support: ("Mecha Pilot",),
    }
    ADJECTIVES = ("Pirate",)
    NOUNS = ("Blades","Fleet")
    uniform_colors = (color.HeavyPurple,None,None,None,color.SeaGreen)


class BoneDevils(Faction):
    name = "the Bone Devil Gang"
    factags = (tags.Criminal, tags.Military)
    mecha_colors = (color.Black, color.Cream, color.BrightRed, color.Avocado, color.Terracotta)
    CAREERS = {
        tags.Trooper: ("Bandit","Thief"),
        tags.Commander: ("Commander","Scavenger"),
        tags.Support: ("Mecha Pilot",),
    }
    LOCATIONS = (personality.DeadZone,)
    ADJECTIVES = ("Bone Devil",)
    NOUNS = ("Gang",)
    uniform_colors = (color.Black,None,None,color.BrightRed,color.Terracotta)

class TerranFederation(Faction):
    name = "the Terran Federation"
    factags = (tags.Politician,)
    mecha_colors = (color.ArmyDrab, color.Olive, color.ElectricYellow, color.GullGrey, color.Terracotta)
    CAREERS = {
        tags.Trooper: ("Mecha Pilot",),
        tags.Commander: ("Commander",),
        tags.Support: ("Mecha Pilot",),
    }
    LOCATIONS = (personality.GreenZone,)
    ADJECTIVES = ("Terran",)
    NOUNS = ("Council",)
    uniform_colors = (color.Turquoise,None,None,None,None)


class TerranDefenseForce(Faction):
    name = "the Terran Defense Force"
    factags = (tags.Military,)
    mecha_colors = (color.ArmyDrab, color.Olive, color.ElectricYellow, color.GullGrey, color.Terracotta)
    CAREERS = {
        tags.Trooper: ("Mecha Pilot",),
        tags.Commander: ("Commander",),
        tags.Support: ("Mecha Pilot",),
    }
    LOCATIONS = (personality.GreenZone,)
    ADJECTIVES = ("Terran",)
    NOUNS = ("Defense Team","Militia")
    uniform_colors = (color.GriffinGreen,None,None,None,color.Khaki)


class Circle(object):
    def __init__(self, parent_faction=None, mecha_colors=None, name="", faction_reactions=None, careers=None, locations=(), uniform_colors=None, active=True):
        if parent_faction and not name:
            name = parent_faction.get_circle_name()
        else:
            name = Faction.get_circle_name()
        self.name = name
        self.parent_faction = parent_faction
        if parent_faction and not mecha_colors:
            mecha_colors = parent_faction.mecha_colors
        self.mecha_colors = mecha_colors or color.random_mecha_colors()
        if parent_faction and not uniform_colors:
            uniform_colors = parent_faction.uniform_colors
        self.uniform_colors = uniform_colors or (None,None,None,None,None)
        self.faction_reactions = dict()
        if faction_reactions:
            self.faction_reactions.update(faction_reactions)
        self.careers = dict()
        if careers:
            self.careers.update(careers)
        self.locations = list(locations)
        if self.parent_faction:
            self.locations += self.parent_faction.LOCATIONS
        self.active = active

    def get_faction_tag(self):
        if self.parent_faction:
            return self.parent_faction
        else:
            return self

    def choose_job(self,role):
        candidates = self.careers.get(role)
        job = jobs.ALL_JOBS["Mecha Pilot"]
        if candidates:
            job = jobs.ALL_JOBS[random.choice(candidates)]
        elif self.parent_faction:
            job = self.parent_faction.choose_job(role)
        return job

    def choose_location(self):
        if self.locations:
            return random.choice(self.locations)

    def __str__(self):
        return self.name

class FactionRelations(object):
    def __init__(self,allies=(),enemies=()):
        self.allies = list(allies)
        self.enemies = list(enemies)


DEFAULT_FACTION_DICT_NT158 = {
    AegisOverlord: FactionRelations(
        allies = (),
        enemies = (TerranFederation,BladesOfCrihna)
    ),
    BladesOfCrihna: FactionRelations(
        allies = (),
        enemies = (AegisOverlord,)
    ),
    BoneDevils: FactionRelations(
        allies = (),
        enemies = (TerranDefenseForce,)
    ),
    TerranFederation: FactionRelations(
        allies = (TerranDefenseForce,),
        enemies= (AegisOverlord,)
    ),
    TerranDefenseForce: FactionRelations(
        allies= (TerranFederation,),
        enemies= (AegisOverlord,BoneDevils)
    )
}


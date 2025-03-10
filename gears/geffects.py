import pbge
from pbge import effects
from pbge.scenes import animobs,movement,pfov
import random
import materials
import damage
import stats
from enchantments import Enchantment,END_COMBAT
import math

#  *************************
#  ***   Utility  Junk   ***
#  *************************

class InvoLibraryShelf( object ):
    def __init__(self,source,invo_list):
        self.source = source
        self.invo_list = invo_list
    def has_at_least_one_working_invo(self,chara,in_combat=True):
        has_one = False
        for invo in self.invo_list:
            if invo.can_be_invoked(chara,in_combat):
                has_one = True
                break
        return has_one
    def get_first_working_invo(self,chara,in_combat=True):
        for invo in self.invo_list:
            if invo.can_be_invoked(chara,in_combat):
                return invo
    def get_average_thrill_power(self,chara,in_combat=True):
        thrills = list()
        for invo in self.invo_list:
            if invo.can_be_invoked(chara,in_combat):
                thrills.append(invo.data.thrill_power)
        if thrills:
            return sum(thrills)/len(thrills)
        else:
            return 0
    def __str__(self):
        return self.source.name


class AttackData( object ):
    # The data class passed to an attack invocation. Mostly just
    # contains the UI stuff.
    # thrill_power is a rough measurement of how exciting this attack is;
    #  used to determine what attacks to prioritize.
    def __init__(self,attack_icon,active_frame,inactive_frame=None,disabled_frame=None,thrill_power=1):
        self.attack_icon = attack_icon
        self.active_frame = active_frame
        if inactive_frame is not None:
            self.inactive_frame = inactive_frame
        else:
            self.inactive_frame = active_frame + 1
        if disabled_frame is not None:
            self.disabled_frame = disabled_frame
        else:
            self.disabled_frame = active_frame + 2
        self.thrill_power = thrill_power


class DashTarget( object ):
    """You can charge and attack someone."""
    AUTOMATIC = False
    MOVE_AND_FIRE = False
    def __init__( self, model, delay_from=0 ):
        self.model = model
        self.delay_from = delay_from
    def get_area( self, camp, origin, target ):
        tiles = set()
        tiles.add( target )
        return tiles
    def get_targets( self, camp, origin ):
        return DashReach( camp, origin[0], origin[1], self.model ).tiles
    def get_delay_point( self, origin, target ):
        if self.delay_from < 0:
            return origin
        elif self.delay_from > 0:
            return target
    def get_reach( self ):
        return self.model.get_current_speed() // 10 + 1
    def get_firing_points(self,camp,desired_target):
        return {self.model.pos}
    def get_potential_targets(self,camp,pc):
        mytiles = DashReach( camp, pc.pos[0], pc.pos[1], self.model ).tiles
        return [pc for pc in camp.scene.get_operational_actors() if pc.pos in mytiles]


class DashReach( pfov.PointOfView ):
    # Return the attackable tiles for a dash attack.
    def __init__(self, camp, x0, y0, model ):
        self.x = x0
        self.y = y0
        self.model = model
        self.scene = camp.scene
        self.blocked_tiles = camp.scene.get_blocked_tiles()
        self.radius = model.get_current_speed() // 10 + 1
        self.tiles = set()
        self.vision_type = model.mmode
        self.nav = pbge.scenes.pathfinding.NavigationGuide(camp.scene,model.pos,model.get_current_speed(),model.mmode,self.blocked_tiles)
        pfov.fieldOfView( x0 , y0 , camp.scene.width , camp.scene.height , self.radius , self )

    def TileBlocked( self , x , y ):
        if (x,y) in self.blocked_tiles:
            return True
        elif self.scene.on_the_map( x , y ):
            return self.scene.tile_blocks_movement(x,y,self.vision_type)
        else:
            return True

    def VisitTile( self , x , y ):
        dist = round( math.sqrt( ( x-self.x )**2 + ( y-self.y )**2 ))
        intline = animobs.get_line(self.model.pos[0],self.model.pos[1],x,y)

        if dist <= self.radius and dist > 1 and intline[-2] in self.nav.cost_to_tile:
            self.tiles.add( ( x , y ) )



# Defense constants
DODGE = 'DODGE'
PARRY = 'PARRY'
BLOCK = 'BLOCK'
INTERCEPT = 'INTERCEPT'

#  ***************************
#  ***   Movement  Modes   ***
#  ***************************

class Skimming( movement.MoveMode ):
    NAME = 'skim'
    altitude = 1

class Rolling( movement.MoveMode ):
    NAME = 'roll'

class SpaceFlight( movement.MoveMode ):
    NAME = 'space flight'

MOVEMODE_LIST = (movement.Walking,movement.Flying,Skimming,Rolling,SpaceFlight)

#  *******************
#  ***   AnimObs   ***
#  *******************

class SmallBoom( animobs.AnimOb ):
    SPRITE_NAME = 'anim_smallboom.png'
    SPRITE_OFF = ((0,0),(-7,0),(-3,6),(3,6),(7,0),(3,-6),(-3,-6))
    def __init__(self, sprite=0, pos=(0,0), loop=0, delay=1, y_off=0 ):
        super(SmallBoom, self).__init__(sprite_name=self.SPRITE_NAME,pos=pos,start_frame=0,end_frame=7,loop=loop,ticks_per_frame=1, delay=delay)
        self.x_off,self.y_off = self.SPRITE_OFF[sprite]
        self.y_off += y_off

class NoDamageBoom( SmallBoom ):
    SPRITE_NAME = 'anim_nodamage.png'

class BigBoom( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_bigboom.png"
    DEFAULT_END_FRAME = 7

class SuperBoom( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_frogatto_nuke.png"
    DEFAULT_END_FRAME = 9

class SmokePoof( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_smokepoof.png"
    DEFAULT_END_FRAME = 7

class DustCloud( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_dustcloud.png"
    DEFAULT_END_FRAME = 7

class BurnAnim( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_burning.png"
    DEFAULT_END_FRAME = 7

class Fireball( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_fireball.png"
    DEFAULT_END_FRAME = 7

class RepairAnim( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_repair.png"
    DEFAULT_END_FRAME = 7
    DEFAULT_LOOP = 4

class MedicineAnim( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_medicine.png"
    DEFAULT_END_FRAME = 7
    DEFAULT_LOOP = 4


class BiotechnologyAnim( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = "anim_biotechnology.png"
    DEFAULT_END_FRAME = 7
    DEFAULT_LOOP = 4


class SearchAnim( animobs.AnimOb ):
    DEFAULT_SPRITE_NAME = 'anim_scouting_search.png'
    DEFAULT_END_FRAME = 7


class MissAnim( animobs.Caption ):
    DEFAULT_TEXT = 'Miss!'


class BlockAnim( animobs.Caption ):
    DEFAULT_TEXT = 'Block!'


class ParryAnim( animobs.Caption ):
    DEFAULT_TEXT = 'Parry!'


class InterceptAnim( animobs.Caption ):
    DEFAULT_TEXT = 'Intercept!'


class FailAnim( animobs.Caption ):
    DEFAULT_TEXT = 'Fail!'


class SearchTextAnim( animobs.Caption ):
    DEFAULT_TEXT = 'Search!'


class BigBullet( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_bigbullet.png"


class GunBeam( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_gunbeam.png"


class SmallBeam( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_smallbeam.png"

class Missile1( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_missile1.png"
    DEFAULT_SPEED = 0.3

class Missile2( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_missile2.png"
    DEFAULT_SPEED = 0.3

class Missile3( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_missile3.png"
    DEFAULT_SPEED = 0.3

class Missile4( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_missile4.png"
    DEFAULT_SPEED = 0.3

class Missile5( animobs.ShotAnim ):
    DEFAULT_SPRITE_NAME = "anim_s_missile5.png"
    DEFAULT_SPEED = 0.3

class ClusterShot( animobs.ShotAnim ):
    # This shotanim is a container which holds a bunch of other shot anims.
    # It's used when a shot consists of more than one anim, for example
    # a large volley of missiles or a particularly long beam blast.
    def __init__( self, start_pos=(0,0), end_pos=(0,0), x_off=0, y_off=0, delay=0, child_classes=() ):
        self.x_off = x_off
        self.y_off = y_off
        self.needs_deletion = False
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.child_classes = child_classes or self.DEFAULT_CHILD_CLASSES
        self.children = list()
        self.delay = delay
    DEFAULT_CHILD_CLASSES = []
    def update( self, view ):
        if self.delay > 0:
            self.delay += -1
        else:
            self.needs_deletion = True
            delay = 0
            original_children = self.children
            self.children = list()
            for cc in self.child_classes:
                self.children.append( cc( start_pos=self.start_pos, end_pos=self.end_pos,
                  x_off=self.x_off, y_off=self.y_off, delay=delay ))
                delay += 1
            self.children[0].children += original_children

class MissileFactory( object ):
    # Used to create custom missile salvos.
    def __init__(self, num_missiles):
        self.num_missiles = min(num_missiles,40)
    MISSILE_ANIMS = (Missile1,Missile2,Missile3,Missile4,Missile5)
    def __call__(self,start_pos,end_pos,delay=0):
        # Return as many missiles as requested.
        fives,leftover = divmod(self.num_missiles,5)
        my_anim = list()
        if fives > 0:
            my_anim += [Missile5,] * fives
        if leftover > 0:
            my_anim.append( self.MISSILE_ANIMS[leftover-1] )
        return ClusterShot(start_pos=start_pos,end_pos=end_pos,delay=delay,child_classes=my_anim)

class BulletFactory( object ):
    # Used to create custom missile salvos.
    def __init__(self, num_bullets, proto_bullet):
        self.num_bullets = num_bullets
        self.proto_bullet = proto_bullet
    def __call__(self,start_pos,end_pos,delay=0):
        # Return as many missiles as requested.
        my_anim = [self.proto_bullet,] * self.num_bullets
        return ClusterShot(start_pos=start_pos,end_pos=end_pos,delay=delay,child_classes=my_anim)

class OriginSpotShotFactory( object ):
    # Instead of a shot anim, this factory generates a spot anim.
    def __init__(self, proto_spot):
        self.proto_spot = proto_spot
    def __call__(self,start_pos,end_pos,delay=0):
        # Return the spot anim.
        return self.proto_spot(pos=start_pos,delay=delay)

class AnimBox( animobs.AnimOb ):
    # This anim does nothing but release other anims into the wild.
    def __init__( self, child_anims, delay=0 ):
        """
        :type child_anims: list
        :type delay: int
        """
        self.child_anims = child_anims
        self.children = list()
        self.delay = delay
        self.needs_deletion = False
    def update( self, view ):
        if self.delay > 0:
            self.delay += -1
        else:
            self.needs_deletion = True
            original_children = self.children
            self.children = list(self.child_anims)
            self.children[0].children += original_children

class DashFactory( object ):
    # Instead of a shot anim, this factory generates a dash anim.
    def __init__(self, dasher):
        self.dasher = dasher
    def __call__(self,start_pos,end_pos,delay=0):
        # Return the spot anim.
        mydash = animobs.Dash(self.dasher,end_pos=end_pos,delay=delay)
        mydust = DustCloud(pos=self.dasher.pos,delay=2)
        return AnimBox([mydash,mydust])


#  *******************
#  ***   Effects   ***
#  *******************

class AttackRoll( effects.NoEffect ):
    """ One actor is gonna attack another actor.
        This may be opposed by a succession of defensive rolls.
        If a defensive roll beats the attack roll, its children get returned.
        Otherwise, the penetration score is recorded in the fx_record and
        the children of this effect get returned.
    """
    def __init__(self, att_stat, att_skill, children=(), anim=None, accuracy=0, penetration=0, modifiers=(), defenses=() ):
        self.att_stat = att_stat
        self.att_skill = att_skill
        self.children = list(children)
        self.anim = anim
        self.accuracy = accuracy
        self.penetration = penetration
        self.modifiers = modifiers
        self.defenses = defenses

    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        if originator:
            att_bonus = originator.get_skill_score(self.att_stat,self.att_skill)
        else:
            att_bonus = random.randint(1,100)
        att_roll = random.randint(1,100)

        for m in self.modifiers:
            att_bonus += m.calc_modifier(camp,originator,pos)

        targets = camp.scene.get_operational_actors(pos)
        next_fx = []
        for target in targets:
            hi_def_roll = 50
            for defense in self.defenses.values():
                if defense.can_attempt(originator,target):
                    next_fx,def_roll = defense.make_roll(self,originator,target,att_bonus,att_roll,fx_record)
                    hi_def_roll = max(def_roll,hi_def_roll)
                    if next_fx:
                        break
            penetration = att_roll + att_bonus + self.penetration - hi_def_roll
            if hasattr(target,'ench_list'):
                penetration += target.ench_list.get_funval(target,'get_penetration_bonus')
            fx_record['penetration'] = penetration

            if camp.fight:
                camp.fight.cstat[target].attacks_this_round += 1

        return next_fx or self.children

    def get_odds( self, camp, originator, target ):
        # Return the percent chance that this attack will hit and the list of
        # modifiers in (value,name) form.
        modifiers = list()
        if originator:
            att_bonus = originator.get_skill_score(self.att_stat,self.att_skill)
        else:
            att_bonus = 50
        for m in self.modifiers:
            mval = m.calc_modifier(camp,originator,target.pos)
            att_bonus += mval
            if mval != 0:
                modifiers.append((mval,m.name))
        odds = 1.0
        for defense in self.defenses.values():
            if defense.can_attempt(originator,target):
                odds *= defense.get_odds(self,originator,target,att_bonus)
        return odds,modifiers


class MultiAttackRoll( effects.NoEffect ):
    """ One actor is gonna attack another actor.
        This may be opposed by a succession of defensive rolls.
        If a defensive roll beats the attack roll, its children get returned.
        Otherwise, the penetration score is recorded in the fx_record and
        the children of this effect get returned.
    """
    def __init__(self, att_stat, att_skill, num_attacks=2, children=(), anim=None, accuracy=0, penetration=0, modifiers=(), defenses=() ):
        self.att_stat = att_stat
        self.att_skill = att_skill
        self.num_attacks = num_attacks
        if not children:
            children = list()
        self.children = children
        self.anim = anim
        self.accuracy = accuracy
        self.penetration = penetration
        self.modifiers = modifiers
        self.defenses = defenses

    def get_multi_bonus( self ):
        # Launching multiple attacks results in a bonus to hit. Of course,
        # not all of these attacks are likely to hit.
        return min(self.num_attacks,10) * 2

    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        if originator:
            att_bonus = originator.get_skill_score(self.att_stat,self.att_skill) + self.get_multi_bonus()
        else:
            att_bonus = random.randint(1,100)
        att_roll = random.randint(1,100)

        for m in self.modifiers:
            att_bonus += m.calc_modifier(camp,originator,pos)

        targets = camp.scene.get_operational_actors(pos)
        next_fx = []
        for target in targets:
            hi_def_roll = 50
            failed = False
            for defense in self.defenses.values():
                if defense.can_attempt(originator,target):
                    next_fx,def_roll = defense.make_roll(self,originator,target,att_bonus,att_roll,fx_record)
                    hi_def_roll = max(def_roll,hi_def_roll)
                    if next_fx:
                        failed = True
                        break
            penetration = att_roll + att_bonus + self.penetration - hi_def_roll - self.get_multi_bonus()
            if hasattr(target,'ench_list'):
                penetration += target.ench_list.get_funval(target,'get_penetration_bonus')
            fx_record['penetration'] = penetration

            if not failed:
                if self.num_attacks <= 10:
                    num_hits = max(int(min( min( att_roll + att_bonus - hi_def_roll, 45 ) // 5 + 1, self.num_attacks )),1)
                else:
                    num_hits = max(int(max((min( att_roll + att_bonus - hi_def_roll, 50 ) * self.num_attacks)//50,1)),1)
                fx_record['number_of_hits'] = num_hits
                anims.append( animobs.Caption('x{}'.format(num_hits),pos=pos,delay=delay,y_off=camp.scene.model_altitude(target,pos[0],pos[1])-15) )

            if camp.fight:
                camp.fight.cstat[target].attacks_this_round += 1

        return next_fx or self.children

    def get_odds( self, camp, originator, target ):
        # Return the percent chance that this attack will hit and the modifiers.
        modifiers = list()
        modifiers.append((self.get_multi_bonus(),'Multi-attack'))
        if originator:
            att_bonus = originator.get_skill_score(self.att_stat,self.att_skill)+ self.get_multi_bonus()
        else:
            att_bonus = 50+ self.get_multi_bonus()
        for m in self.modifiers:
            mval = m.calc_modifier(camp,originator,target.pos)
            att_bonus += mval
            if mval != 0:
                modifiers.append((mval,m.name))
        odds = 1.0
        for defense in self.defenses.values():
            if defense.can_attempt(originator,target):
                odds *= defense.get_odds(self,originator,target,att_bonus)
        return odds,modifiers


class OpposedSkillRoll( effects.NoEffect ):
    """ Two actors make a skill roll. One will succeed, one will fail.
    """
    def __init__(self, att_stat, att_skill, def_stat, def_skill, on_success=(), on_failure=(), on_no_target=(), anim=None, roll_mod=0, min_chance=5, max_chance=95 ):
        self.att_stat = att_stat
        self.att_skill = att_skill
        self.def_stat = def_stat
        self.def_skill = def_skill
        if not on_success:
            on_success = list()
        self.on_success = on_success
        if not on_failure:
            on_failure = list()
        self.on_failure = on_failure
        if not on_no_target:
            on_no_target = list()
        self.on_no_target = on_no_target
        self.anim = anim
        self.roll_mod = roll_mod
        self.min_chance = min_chance
        self.max_chance = max_chance

    def _calc_percent(self, camp, originator, target):
        if originator:
            percent = originator.get_skill_score(self.att_stat,self.att_skill) + self.roll_mod
        else:
            percent = self.roll_mod
        if target:
            percent -= target.get_skill_score(self.def_stat,self.def_skill)
        return max(min(percent,self.max_chance),self.min_chance)

    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        target = camp.scene.get_main_actor(pos)
        if target:
            odds = self._calc_percent(camp,originator,target)
            if random.randint(1,100) <= odds:
                return self.on_success
            else:
                return self.on_failure
        else:
            return self.on_no_target

    def get_odds( self, camp, originator, target ):
        # Return the percent chance that this attack will hit and the list of
        # modifiers in (value,name) form.
        modifiers = [(self.roll_mod,'Base Modifier')]
        return self._calc_percent(camp,originator,target)/100.0,modifiers


class CheckConditions( effects.NoEffect ):
    """ This tile will be checked for something.
        conditions is a list of conditions in the same format as the aitargeter conditions;
        each condition is a callable that takes (camp,originator,target)
    """
    def __init__(self, conditions, on_success=(), on_failure=(), anim=None ):
        self.conditions = conditions
        if not on_success:
            on_success = list()
        self.on_success = on_success
        if not on_failure:
            on_failure = list()
        self.on_failure = on_failure
        self.anim = anim

    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        target = camp.scene.get_main_actor(pos)
        if all(con(camp, originator, target) for con in self.conditions):
            return self.on_success
        else:
            return self.on_failure


class StealthSkillRoll( effects.NoEffect ):
    """ The originator makes a skill roll against the highest enemy in range.
    """
    def __init__(self, att_stat=None, att_skill=None, def_stat=None, def_skill=None, on_success=(), on_failure=(), radius=15, anim=None, roll_mod=50, min_chance=5, max_chance=95 ):
        self.att_stat = att_stat or stats.Speed
        self.att_skill = att_skill or stats.Stealth
        self.def_stat = def_stat or stats.Perception
        self.def_skill = def_skill or stats.Scouting
        if not on_success:
            on_success = list()
        self.on_success = on_success
        if not on_failure:
            on_failure = list()
        self.on_failure = on_failure
        self.anim = anim
        self.roll_mod = roll_mod
        self.min_chance = min_chance
        self.max_chance = max_chance
        self.radius = radius

    def _calc_percent(self, camp, originator, pos):
        if originator:
            percent = originator.get_skill_score(self.att_stat,self.att_skill) + self.roll_mod
        else:
            percent = self.roll_mod
        observation_area = pfov.PointOfView( camp.scene, pos[0], pos[1], self.radius ).tiles
        enemy_skills = [npc.get_skill_score(self.def_stat,self.def_skill) for npc in camp.scene.get_operational_actors() if camp.scene.are_hostile(originator,npc) and npc.pos in observation_area]
        if enemy_skills:
            percent -= max(enemy_skills)
        return max(min(percent,self.max_chance),self.min_chance)

    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        odds = self._calc_percent(camp,originator,pos)
        if random.randint(1,100) <= odds:
            return self.on_success
        else:
            return self.on_failure


class DoDamage( effects.NoEffect ):
    """ Whatever is in this tile is going to take damage.
    """
    def __init__(self, damage_n, damage_d, children=(), anim=None, scale=None, hot_knife=False, scatter=False ):
        if not children:
            children = list()
        self.damage_n = damage_n
        self.damage_d = damage_d
        self.children = children
        self.anim = anim
        self.scale = scale
        self.hot_knife = hot_knife
        self.scatter = scatter
    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        targets = camp.scene.get_operational_actors(pos)
        penetration = fx_record.get("penetration",random.randint(1,100))
        damage_percent = fx_record.get("damage_percent",100)
        number_of_hits = fx_record.get("number_of_hits",1)
        for target in targets:
            scale = self.scale or target.scale

            if self.scatter:
                num_packets = sum( sum(random.randint(1,self.damage_d) for n in range(self.damage_n)) for t in range(number_of_hits))
                num_packets = max(int(num_packets * damage_percent //100), 1)
                hits = [scale.scale_health(1, materials.Metal )] * num_packets
            else:
                hits = [max(int(scale.scale_health(
                  sum(random.randint(1,self.damage_d) for n in range(self.damage_n)),
                  materials.Metal) * damage_percent // 100),1) for t in range(number_of_hits)]
            mydamage = damage.Damage( camp, hits,
                  penetration, target, anims, hot_knife=self.hot_knife )
            # Hidden targets struck by an attack get revealed.
            myanim = animobs.RevealModel( target,delay=delay)
            anims.append(myanim)
        return self.children

class DoHealing( effects.NoEffect ):
    """ Whatever is in this tile is going to get healed. Maybe.
    """
    def __init__(self, damage_n, damage_d, children=(), anim=None, scale=None, repair_type=materials.RT_REPAIR ):
        if not children:
            children = list()
        self.damage_n = damage_n
        self.damage_d = damage_d
        self.children = children
        self.anim = anim
        self.scale = scale
        self.repair_type = repair_type
    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        targets = camp.scene.get_operational_actors(pos)
        for target in targets:
            scale = self.scale or target.scale
            damaged_parts = [part for part in target.get_all_parts() if hasattr(part,"hp_damage") and part.hp_damage > 0 and part.material.repair_type == self.repair_type]
            hp_to_restore = max(scale.scale_health(
                  sum(random.randint(1,self.damage_d) for n in range(self.damage_n)),
                  materials.Metal)//2,1)
            hp_restored = 0
            while damaged_parts and hp_restored < hp_to_restore:
                part = random.choice(damaged_parts)
                part.hp_damage -= 1
                hp_restored += 1
                if part.hp_damage < 1:
                    damaged_parts.remove(part)
            myanim = animobs.Caption( str(hp_restored),
                pos=target.pos, delay=delay,
                y_off=-camp.scene.model_altitude(target,*target.pos))
            anims.append( myanim )

            if hasattr(target, "ench_list"):
                target.ench_list.tidy(self.repair_type)

        return self.children


class SetHidden( effects.NoEffect ):
    """An effect that hides a model."""
    def handle_effect( self, camp, fx_record, originator, pos, anims, delay=0 ):
        """Do whatever is required of effect; return list of child effects."""
        targets = camp.scene.get_operational_actors(pos)
        for target in targets:
            myanim = animobs.HideModel( target,delay=delay)
            anims.append(myanim)
        return self.children


class SetVisible( effects.NoEffect ):
    """An effect that reveals a model."""
    def handle_effect( self, camp, fx_record, originator, pos, anims, delay=0 ):
        """Do whatever is required of effect; return list of child effects."""
        targets = camp.scene.get_operational_actors(pos)
        for target in targets:
            myanim = animobs.RevealModel( target,delay=delay)
            anims.append(myanim)
        return self.children


class AddEnchantment( effects.NoEffect ):
    """ Apply an enchantment to the actor in this tile.
    """
    def __init__(self, enchant_type, enchant_params={}, dur_n=None, dur_d=None, children=(), anim=None ):
        self.enchant_type = enchant_type
        self.enchant_params = enchant_params
        self.dur_n = dur_n
        self.dur_d = dur_d
        self.children = list(children)
        self.anim = anim
    def handle_effect(self, camp, fx_record, originator, pos, anims, delay=0 ):
        target = camp.scene.get_main_actor(pos)
        if target and hasattr(target,'ench_list'):
            params = self.enchant_params.copy()
            if self.dur_n and self.dur_d:
                params['duration'] = sum(random.randint(1, self.dur_d) for n in range(self.dur_n))
            target.ench_list.add_enchantment(self.enchant_type,params)
        return self.children


#  ***************************
#  ***   Roll  Modifiers   ***
#  ***************************
#
# Modular roll modifiers.

class RangeModifier( object ):
    name = 'Range'
    def __init__(self,range_step):
        self.range_step = range_step
    def calc_modifier( self, camp, attacker, pos ):
        my_range = camp.scene.distance(attacker.pos,pos)
        my_mod = ((my_range - 1)//self.range_step) * -10
        if my_range < (self.range_step-3):
            my_mod += (self.range_step-3-my_range) * -5
        return my_mod


class CoverModifier( object ):
    name = 'Cover'
    def __init__(self,vision_type=movement.Vision):
        self.vision_type = vision_type
    def calc_modifier( self, camp, attacker, pos ):
        my_mod = -camp.scene.get_cover(attacker.pos[0],attacker.pos[1],pos[0],pos[1])
        return my_mod


class SpeedModifier( object ):
    name = 'Target Movement'
    IMMOBILE_MODIFIER = 25
    MOD_PER_TILE = -3
    def calc_modifier( self, camp, attacker, pos ):
        targets = camp.scene.get_operational_actors(pos)
        my_mod = 0
        for t in targets:
            if hasattr(t,"get_current_speed") and t.get_current_speed() < 1:
                my_mod += self.IMMOBILE_MODIFIER
            elif camp.fight:
                my_mod += camp.fight.cstat[t].moves_this_round * self.MOD_PER_TILE
        return my_mod


class SensorModifier( object ):
    name = 'Sensor Range'
    PENALTY = -5
    def calc_modifier( self, camp, attacker, pos ):
        my_range = camp.scene.distance(attacker.pos,pos)
        my_sensor = attacker.get_sensor_range(camp.scene.scale)
        if my_range > my_sensor:
            return (my_range - my_sensor)*self.PENALTY
        else:
            return 0


class OverwhelmModifier( object ):
    # Every time you are attacked, the next attack gets a bonus to hit.
    name = 'Overwhelmed'
    MOD_PER_ATTACK = 3
    def calc_modifier( self, camp, attacker, pos ):
        my_mod = 0
        if camp.fight:
            targets = camp.scene.get_operational_actors(pos)
            for t in targets:
                my_mod += camp.fight.cstat[t].attacks_this_round * self.MOD_PER_ATTACK
        return my_mod


class GenericBonus(object):
    def __init__(self,name,bonus):
        self.name = name
        self.bonus = bonus
    def calc_modifier( self, camp, attacker, pos ):
        return self.bonus


class ModuleBonus(object):
    def __init__(self,wmodule):
        self.name = '{} Mod'.format(wmodule)
        self.wmodule = wmodule
    def calc_modifier( self, camp, attacker, pos ):
        if self.wmodule:
            it = self.wmodule.form.AIM_BONUS
            for i in self.wmodule.inv_com:
                if hasattr(i,"get_aim_bonus"):
                    it += i.get_aim_bonus()
            return it
        else:
            return 0


class SneakAttackBonus(object):
    name = 'Sneak Attack'
    BONUS = 20
    def calc_modifier( self, camp, attacker, pos ):
        if attacker and attacker.hidden:
            return self.BONUS
        else:
            return 0


class HiddenModifier(object):
    name = 'Hidden'
    BONUS = -25
    def calc_modifier( self, camp, attacker, pos ):
        target = camp.scene.get_main_actor(pos)
        if target and target.hidden:
            return self.BONUS
        else:
            return 0


#  **************************
#  ***   Defense  Rolls   ***
#  **************************
#
# Each defense roll takes the attack roll effect, the attacker, defender,
# attack bonus, and attack roll.
# It returns the roll result fx (None if the roll was unsuccessful)
# and the defense target (def roll + def bonus), which is used to calculate
# penetration if the attack hits.

class DodgeRoll( object ):
    def make_roll( self, atroller, attacker, defender, att_bonus, att_roll, fx_record ):
        # If the attack roll + attack bonus + accuracy is higher than the
        # defender's defense bonus + maneuverability + 20, or if the attack roll
        # is greater than 95, the attack hits.
        def_target = defender.get_dodge_score() + 50

        if att_roll > 95:
            # A roll greater than 95 always hits.
            return (None,def_target)
        elif att_roll <= 5:
            # A roll of 5 or less always misses.
            return (self.CHILDREN, def_target)
        elif (att_roll + att_bonus + atroller.accuracy) > (def_target + defender.calc_mobility()):
            return (None,def_target)
        else:
            return (self.CHILDREN, def_target)

    def can_attempt( self, attacker, defender ):
        return True

    def get_odds( self, atroller, attacker, defender, att_bonus ):
        # Return the odds as a float.
        def_target = defender.get_dodge_score()
        # The chance to hit is clamped between 5% and 95%.
        percent = min(max(50 + (att_bonus + atroller.accuracy) - (def_target + defender.calc_mobility()),5),95)
        return float(percent)/100

    CHILDREN = (effects.NoEffect(anim=MissAnim),)


class ReflexSaveRoll( object ):
    # Taking the name from d20... Unlike a regular dodge roll, a reflex save
    # can't entirely avoid an attack, but it can reduce the damage done.
    def make_roll( self, atroller, attacker, defender, att_bonus, att_roll, fx_record ):
        # If the attack roll + attack bonus + accuracy is higher than the
        # defender's defense bonus + maneuverability + 20, or if the attack roll
        # is greater than 95, the attack hits.
        def_target = defender.get_dodge_score() + random.randint(1,100)
        diff = (def_target + defender.calc_mobility()) - (att_roll + att_bonus + atroller.accuracy)
        if diff >= 0:
            # Record a damage reduction.
            fx_record['damage_percent'] = max( 75- diff, 25 )
        return (None,def_target)

    def can_attempt( self, attacker, defender ):
        return True

    def get_odds( self, atroller, attacker, defender, att_bonus ):
        return 1.0


class BlockRoll( object ):
    def __init__(self,weapon_to_block):
        self.weapon_to_block = weapon_to_block
    def make_roll( self, atroller, attacker, defender, att_bonus, att_roll, fx_record ):
        # First, locate the defender's shield.
        shield = self.get_shield(defender)
        if shield:
            def_roll = random.randint(1,100)
            def_bonus = shield.get_block_bonus() + defender.get_skill_score(stats.Speed,shield.scale.MELEE_SKILL)

            if def_roll > 95:
                # A roll greater than 95 always defends.
                shield.pay_for_block(defender,self.weapon_to_block)
                return (self.CHILDREN,def_roll + def_bonus)
            elif def_roll <= 5:
                # A roll of 5 or less always fails.
                return (None, def_roll + def_bonus)
            elif (att_roll + att_bonus + atroller.accuracy) > (def_roll + def_bonus):
                return (None,def_roll + def_bonus)
            else:
                shield.pay_for_block(defender,self.weapon_to_block)
                return (self.CHILDREN, def_roll + def_bonus)
        else:
            return (None,0)
    def get_shield( self, defender ):
        shields = [part for part in defender.descendants() if hasattr(part,'get_block_bonus') and part.is_operational()]
        if shields:
            return max( shields, key = lambda s: s.get_block_bonus() )
    def can_attempt( self, attacker, defender ):
        return self.get_shield(defender) and (defender.get_current_stamina() > 0)

    def get_odds( self, atroller, attacker, defender, att_bonus ):
        # Return the odds as a float.
        shield = self.get_shield(defender)
        if shield:
            def_target = shield.get_block_bonus() + defender.get_skill_score(stats.Speed,shield.scale.MELEE_SKILL)
            # The chance to hit is clamped between 5% and 95%.
            percent = min(max(50 + (att_bonus + atroller.accuracy) - def_target,5),95)
            return float(percent)/100
        else:
            return 1.0
    CHILDREN = (effects.NoEffect(anim=BlockAnim),)


class ParryRoll( object ):
    def __init__(self,weapon_to_parry):
        self.weapon_to_parry = weapon_to_parry
    def make_roll( self, atroller, attacker, defender, att_bonus, att_roll, fx_record ):
        # First, locate the defender's parrier.
        parrier = self.get_parrier(defender)
        if parrier:
            def_roll = random.randint(1,100)
            def_bonus = parrier.get_parry_bonus() + defender.get_skill_score(stats.Speed,parrier.scale.MELEE_SKILL)

            if def_roll > 95:
                # A roll greater than 95 always defends.
                parrier.pay_for_parry(defender,self.weapon_to_parry)
                return (self.CHILDREN,def_roll + def_bonus)
            elif def_roll <= 5:
                # A roll of 5 or less always fails.
                return (None, def_roll + def_bonus)
            elif (att_roll + att_bonus + atroller.accuracy) > (def_roll + def_bonus):
                return (None,def_roll + def_bonus)
            else:
                parrier.pay_for_parry(defender,self.weapon_to_parry)
                return (self.CHILDREN, def_roll + def_bonus)
        else:
            return (None,0)
    def get_parrier( self, defender ):
        parriers = [part for part in defender.descendants() if hasattr(part,'can_parry') and part.can_parry() and part.is_operational()]
        if parriers:
            return max( parriers, key = lambda s: s.get_parry_bonus() )
    def can_attempt( self, attacker, defender ):
        return self.get_parrier(defender) and (defender.get_current_stamina() > 0)

    def get_odds( self, atroller, attacker, defender, att_bonus ):
        # Return the odds as a float.
        parrier = self.get_parrier(defender)
        if parrier:
            def_target = parrier.get_parry_bonus() + defender.get_skill_score(stats.Speed,parrier.scale.MELEE_SKILL)
            # The chance to hit is clamped between 5% and 95%.
            percent = min(max(50 + (att_bonus + atroller.accuracy) - def_target,5),95)
            return float(percent)/100
        else:
            return 1.0
    CHILDREN = (effects.NoEffect(anim=ParryAnim),)


class InterceptRoll( object ):
    def __init__(self,weapon_to_intercept):
        self.weapon_to_intercept = weapon_to_intercept
    def make_roll( self, atroller, attacker, defender, att_bonus, att_roll, fx_record ):
        # First, locate the defender's interceptor.
        interceptor = self.get_interceptor(defender)
        if interceptor:
            def_roll = random.randint(1,100)
            def_bonus = interceptor.get_intercept_bonus() + defender.get_skill_score(stats.Speed,interceptor.scale.RANGED_SKILL)

            if def_roll > 95:
                # A roll greater than 95 always defends.
                interceptor.pay_for_intercept(defender,self.weapon_to_intercept)
                return (self.CHILDREN,def_roll + def_bonus)
            elif def_roll <= 5:
                # A roll of 5 or less always fails.
                return (None, def_roll + def_bonus)
            elif (att_roll + att_bonus + atroller.accuracy) > (def_roll + def_bonus):
                return (None,def_roll + def_bonus)
            else:
                interceptor.pay_for_intercept(defender,self.weapon_to_intercept)
                return (self.CHILDREN, def_roll + def_bonus)
        else:
            return (None,0)
    def get_interceptor( self, defender ):
        interceptors = [part for part in defender.descendants() if hasattr(part,'can_intercept') and part.can_intercept() and part.is_operational()]
        if interceptors:
            return max( interceptors, key = lambda s: s.get_intercept_bonus() )
    def can_attempt( self, attacker, defender ):
        return self.get_interceptor(defender) and (defender.get_current_stamina() > 0)

    def get_odds( self, atroller, attacker, defender, att_bonus ):
        # Return the odds as a float.
        interceptor = self.get_interceptor(defender)
        if interceptor:
            def_target = interceptor.get_intercept_bonus() + defender.get_skill_score(stats.Speed,interceptor.scale.RANGED_SKILL)
            # The chance to hit is clamped between 5% and 95%.
            percent = min(max(50 + (att_bonus + atroller.accuracy) - def_target,5),95)
            return float(percent)/100
        else:
            return 1.0
    CHILDREN = (effects.NoEffect(anim=InterceptAnim),)


# ECMRoll

#  *****************
#  ***   PRICE   ***
#  *****************

class AmmoPrice(object):
    def __init__( self, ammo_source, ammo_amount ):
        self.ammo_source = ammo_source
        self.ammo_amount = ammo_amount

    def pay( self, chara ):
        self.ammo_source.spent += self.ammo_amount

    def can_pay( self, chara ):
        return self.ammo_source.quantity >= (self.ammo_source.spent + self.ammo_amount)


class PowerPrice(object):
    def __init__( self, power_amount ):
        self.power_amount = power_amount

    def pay( self, chara ):
        chara.consume_power(self.power_amount)

    def can_pay( self, chara ):
        cp,mp = chara.get_current_and_max_power()
        return cp >= self.power_amount


class MentalPrice(object):
    def __init__( self, amount ):
        self.amount = amount

    def pay( self, chara ):
        chara.spend_mental(self.amount)

    def can_pay( self, chara ):
        return chara.get_current_mental() >= self.amount


class RevealPositionPrice(object):
    def __init__( self, weapon_flash ):
        self.weapon_flash = weapon_flash

    def pay( self, chara ):
        stealth_skill = min(chara.get_skill_score(stats.Ego,stats.Stealth) - self.weapon_flash * 25, 75)
        if random.randint(1,100) > stealth_skill:
            chara.hidden = False

    def can_pay( self, chara ):
        return True


#  ************************
#  ***   ENCHANTMENTS   ***
#  ************************
# Existing funval types:
#   get_mobility_bonus
#   get_penetration_bonus


class Burning(Enchantment):
    name = 'Burning'
    DEFAULT_DURATION = 3
    def update(self,camp,owner):
        burn = effects.Invocation(
            name = 'Burn',
            fx= DoDamage(2,4,scale=owner.scale,scatter=True,
                         anim=BurnAnim,),
            area=pbge.scenes.targetarea.SingleTarget(),)
        burn.invoke(camp, None, [owner.pos,], pbge.my_state.view.anim_list)
        pbge.my_state.view.handle_anim_sequence()


class HaywireStatus(Enchantment):
    name = 'Haywire'
    # The only top 10 status effect from Prince Edward Island
    DEFAULT_DURATION = 3
    DEFAULT_DISPEL = (END_COMBAT,materials.RT_REPAIR)
    ALT_AI = 'HaywireAI'


class SensorLock(Enchantment):
    name = 'Sensor Lock'
    DEFAULT_DISPEL = (END_COMBAT,)
    DEFAULT_DURATION = 2
    def get_mobility_bonus(self,owner):
        return -25


class Prescience(Enchantment):
    # +2 bonus to dodge skills while active.
    name = 'Prescience'
    DEFAULT_DISPEL = (END_COMBAT,)
    DEFAULT_DURATION = 3
    def get_stat(self,stat):
        if stat in (stats.MechaPiloting,stats.Dodge):
            return 2
        else:
            return 0

class WeakPoint(Enchantment):
    name = 'Weak Point'
    DEFAULT_DISPEL = (END_COMBAT,)
    def get_penetration_bonus(self,owner):
        return 20


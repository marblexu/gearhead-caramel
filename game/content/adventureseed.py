import pbge
from game.content import GHNarrativeRequest, PLOT_LIST
from pbge.plots import Adventure
import gears
import pygame


class AdventureSeed(Adventure):
    def __init__(self, camp, name, adv_type, adv_return, pstate=None, auto_set_rank=True, restore_at_end=True,
                 display_results_at_end=True):
        # adv_return is a (Destination,Entrance) tuple.
        super(AdventureSeed, self).__init__(name=name, world=None)
        self.pstate = pstate or pbge.plots.PlotState(adv=self,rank=camp.pc.renown)
        self.pstate.adv = self
        self.pstate.elements["ADVENTURE_RETURN"] = adv_return
        self.adv_type = adv_type
        self.auto_set_rank = auto_set_rank
        self.restore_at_end = restore_at_end
        self.started = False
        self.display_results_at_end = display_results_at_end

        # Auto-apply rewards when the mission ends.
        self.rewards = list()
        # Rewards can add (type,value) tuples to the results list.
        self.results = list()

        # Create a list in which to store the objectives. We'll use this to determine if the mission is
        # finished or failed or whatnot. Or we can just ignore it, It all depends on what kind of adventure this is.
        self.objectives = list()

    def __call__(self, camp):
        """

        :type camp: gears.GearHeadCampaign
        """
        if self.auto_set_rank:
            self.pstate.rank = camp.pc.renown
        nart = GHNarrativeRequest(camp, self.pstate, self.adv_type, PLOT_LIST)
        if nart.story:
            nart.build()
            self.started = True
            camp.check_trigger("UPDATE")
        else:
            for e in nart.errors:
                print e

    def get_completion(self):
        # Return the percent completion of this mission. Due to optional objectives and whatnot, this may fall
        # outside of the 0..100 range.
        awarded = sum([o.awarded_points for o in self.objectives if not o.failed])
        total = max(sum([o.mo_points for o in self.objectives if not o.optional]),1)
        return (awarded * 100)//total
    def is_won(self):
        return self.get_completion() > 50
    def get_grade(self):
        c = self.get_completion()
        if c < 0:
            return "F-"
        elif c <= 50:
            return "F"
        elif c <= 60:
            return "D"
        elif c <= 70:
            return "C"
        elif c <= 80:
            return "B"
        elif c <= 90:
            return "A"
        elif c <= 100:
            return "A+"
        else:
            return "S"
    def is_completed(self):
        return all([(o.optional or o.awarded_points > 0 or o.failed) for o in self.objectives])

    def restore_party(self, camp):
        """
        Restore the party to health, removing the charge from their credits.
        :type camp: gears.GearHeadCampaign
        """
        # Sort any incapacitated members first.
        camp.bring_out_your_dead()

        # Next, restore the party.
        repair_total = 0
        for pc in camp.party + camp.incapacitated_party:
            rcdict = pc.get_repair_cost()
            pc.wipe_damage()
            repair_total += sum([v for k,v in rcdict.iteritems()])
            if hasattr(pc, "mp_spent"):
                pc.mp_spent = 0
            if hasattr(pc, "sp_spent"):
                pc.sp_spent = 0

            for part in pc.descendants():
                if hasattr(part,"get_reload_cost"):
                    repair_total += part.get_reload_cost()
                    part.spent = 0
        camp.credits -= repair_total
        self.results.append(("Repair/Reload","-${:,}".format(repair_total)))

    def end_adventure(self,camp):
        for rfun in self.rewards:
            rfun(camp,self)
        if self.restore_at_end:
            self.restore_party(camp)

        if self.display_results_at_end:
            if self.is_won():
                mydisplay = CombatResultsDisplay(title="Victory: {}".format(self.get_grade()), mission_seed=self,
                                                 width=400)
            else:
                mydisplay = CombatResultsDisplay(title="Failure: {}".format(self.get_grade()),
                                                 title_color=pygame.color.Color(250, 50, 0), mission_seed=self,
                                                 width=400)
            pbge.alert_display(mydisplay.show)

        super(AdventureSeed,self).end_adventure(camp)

#   **********************
#   ***  INFO DISPLAY  ***
#   **********************

class ObjectivesInfo(object):
    PADDING = 5
    RED = pygame.Color(255,50,0)
    def __init__(self,mission_seed,font=None,width=300,**kwargs):
        self.mission_seed = mission_seed
        self.width = width
        self.font = font or pbge.BIGFONT
        self.images = dict()
        self.update()
    def update(self):
        self.images = dict()
        for o in self.mission_seed.objectives:
            if not o.secret:
                self.images[o] = pbge.render_text(self.font,self.get_objective_text(o),self.width,self.get_objective_color(o),justify=0)
        self.height = sum(i.get_height() for i in self.images.values()) + self.PADDING * (len(self.images.values())-1)

    def get_objective_text(self,obj):
        if obj.awarded_points == 0 and not obj.failed:
            return '- {} (INCOMPLETE)'.format(obj.name)
        elif obj.awarded_points < obj.mo_points//2 or obj.failed:
            return '- {} (FAILED)'.format(obj.name)
        else:
            return '- {} (COMPLETE)'.format(obj.name)

    def get_objective_color(self,obj):
        if obj.failed:
            return self.RED
        elif obj.optional:
            return pbge.INFO_GREEN
        else:
            return pbge.TEXT_COLOR
    def render(self,x,y):
        mydest = pygame.Rect(x, y, self.width, self.height)
        for obj,img in self.images.items():
            pbge.my_state.screen.blit(img, mydest)
            mydest.y += img.get_height() + self.PADDING

class ResultsInfo(object):
    def __init__(self,mission_seed,font=None,width=300,**kwargs):
        self.mission_seed = mission_seed
        self.width = width
        self.font = font or pbge.BIGFONT
        self.image = None
        self.update()
    def update(self):
        self.image = pbge.render_text(pbge.BIGFONT,'\n '.join(['{}: {}'.format(*rew) for rew in self.mission_seed.results]),self.width,justify=0,color=pbge.INFO_HILIGHT)
        self.height = self.image.get_height()
    def render(self,x,y):
        pbge.my_state.screen.blit(self.image,pygame.Rect(x,y,self.width,self.height))


class CombatMissionDisplay(gears.info.InfoPanel):
    DEFAULT_BLOCKS = (gears.info.TitleBlock,ObjectivesInfo)
    def show(self):
        w,h = self.get_dimensions()
        mydest = pbge.frects.Frect(-w//2,-h//2,w,h).get_rect()
        self.render(mydest.x,mydest.y)

class CombatResultsDisplay(CombatMissionDisplay):
    DEFAULT_BLOCKS = (gears.info.TitleBlock,ObjectivesInfo,ResultsInfo)


#   ********************
#   ***  OBJECTIVES  ***
#   ********************

class MissionObjective(object):
    """
    An optional objectives record for missions to use.
    """
    def __init__(self,name,mo_points,optional=False,secret=False):
        self.name = name
        self.mo_points = mo_points
        self.awarded_points = 0
        self.optional = optional
        self.failed = False
        self.secret = secret
    def win(self,completion=100):
        self.awarded_points = max(( self.mo_points * completion ) // 100,1)


#   *****************
#   ***  REWARDS  ***
#   *****************

class CashReward(object):
    def __init__(self,rank=None,size=100):
        self.rank = rank
        self.size = size
    def __call__(self,camp,adv):
        """

        :type camp: gears.GearHeadCampaign
        :type adv: AdventureSeed
        """
        # Only give a cash reward if the adventure is won.
        if adv.is_won():
            rank = self.rank or adv.pstate.rank
            cash = gears.selector.calc_threat_points(rank,self.size)//5
            camp.credits += cash
            adv.results.append(("Pay","+${:,}".format(cash)))

class RenownReward(object):
    def __init__(self,rank=None):
        self.rank = rank
    def __call__(self,camp,adv):
        """

        :type camp: gears.GearHeadCampaign
        :type adv: AdventureSeed
        """
        comp = adv.get_completion()
        rank = self.rank or adv.pstate.rank
        original_renown = camp.renown
        if comp > 100:
            # The party did very well; jump to this renown if much lower.
            camp.renown = max(rank+1,camp.renown+1)
        elif comp > 70 and camp.renown <= (rank+10):
            camp.renown += 1
        elif comp < 60:
            # Super loss.
            camp.renown = min(camp.renown - 5, int(camp.renown * 0.75))

        if camp.renown != original_renown:
            adv.results.append(("Renown","{:+}".format(camp.renown - original_renown)))

class ExperienceReward(object):
    def __init__(self,size=100):
        self.size = size
    def __call__(self,camp,adv):
        """

        :type camp: gears.GearHeadCampaign
        :type adv: AdventureSeed
        """
        # Only give a cash reward if the adventure is won.
        if adv.is_won():
            xp = max(self.size,adv.get_completion())
        else:
            xp = self.size//2

        camp.dole_xp(xp)

        adv.results.append(("Experience","+{:,}".format(xp)))


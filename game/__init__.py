import exploration
import combat
import teams
import content
import ghdialogue
import configedit
import invoker
import cosplay
import chargen
import services
import fieldhq
from game.fieldhq import backpack


def start_campaign(pc_egg,adv_type="SCENARIO_DEADZONEDRIFTER"):
    camp = content.narrative_convenience_function(pc_egg,adv_type=adv_type)
    if camp:
        camp.place_party()
        camp.save()
        camp.play()



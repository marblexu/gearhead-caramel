
# Constants for dialogue contexts.

HELLO = "HELLO"                 # HELLO = NPC says hello. Usually the first offer in a peaceful conversation.
ASK_FOR_ITEM = "ASK_FOR_ITEM"   # ASK_FOR_ITEM: The NPC gives the PC an item, or at least replies to the request.
                                #       The data property should contain "item"
INFO = "INFO"                   # INFO: The NPC gives the PC some information.
                                #       The data property should contain "subject"
REVEAL = "REVEAL"               # The NPC receives information from the PC.
                                #       The data property should contain "reveal"
MISSION = "MISSION"             # MISSION: A mission is described or offered.
PROPOSAL = "PROPOSAL"           # The NPC will try to make a deal with the PC.
                                # The data property should contain "subject"
PROBLEM ="PROBLEM"              # A problem is described.
ACCEPT = "ACCEPT"               # The PC has accepted the mission or proposal; the NPC responds.
DENY = "DENY"                   # The PC has refused the mission or proposal; the NPC responds.
ARREST = "ARREST"               # The PC attempts to arrest the NPC; the NPC responds.
GOODBYE = "GOODBYE"             # The NPC says goodbye to the PC.
JOIN = "JOIN"                   # The NPC will join the party
PERSONAL = "PERSONAL"           # The NPC gives some personal information
ATTACK  = "ATTACK"              # The greeting from a hostile NPC
CHALLENGE = "CHALLENGE"         # The reply from a hostile (or now hostile) NPC when challenged by the PC
COMBAT_INFO= "COMBAT_INFO"      # The NPC gives the PC some information during combat.
                                # The data property should contain "subject"
MERCY = "MERCY"                 # This hostile NPC is being allowed to flee the battle
RETREAT = "RETREAT"             # This hostile NPC is retreating from the battle
WITHDRAW = "WITHDRAW"           # The NPC responds to the PC withdrawing from battle
CHAT = "CHAT"                   # The NPC will relay some bit of local news
OPEN_SHOP = "OPEN_SHOP"         # The NPC will show the PC what they have for sale.



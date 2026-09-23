from strawberry.tools import merge_types

from .subscribe_palworld import SubscribePalworldType
from .subscribe_steam import SubscribeSteamType

SubscribeSchema = merge_types(
    name="SubscribeSchema",
    types=(
        SubscribeSteamType,
        SubscribePalworldType,
    ),
)

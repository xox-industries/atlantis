from strawberry.tools import merge_types

from src.route.query.display_palworld import DisplayPalworldType
from src.route.query.display_steam import DisplaySteamType

QuerySchema = merge_types(
    name="QuerySchema",
    types=(
        DisplayPalworldType,
        DisplaySteamType,
    ),
)

from strawberry.tools import merge_types

from src.route.query.display_minecraft_java_edition import (
    DisplayMinecraftJavaEditionType,
)
from src.route.query.display_palworld import DisplayPalworldType
from src.route.query.display_steam import DisplaySteamType
from src.route.query.display_terraria import DisplayTerrariaType
from src.route.query.display_tmodloader import DisplayTModLoaderType
from src.route.query.display_valheim import DisplayValheimType

QuerySchema = merge_types(
    name="QuerySchema",
    types=(
        DisplayMinecraftJavaEditionType,
        DisplayPalworldType,
        DisplaySteamType,
        DisplayTerrariaType,
        DisplayTModLoaderType,
        DisplayValheimType,
    ),
)

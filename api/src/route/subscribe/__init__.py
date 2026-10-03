from strawberry.tools import merge_types

from .subscribe_minecraft_java_edition import SubscribeMinecraftJavaEditionType
from .subscribe_palworld import SubscribePalworldType
from .subscribe_steam import SubscribeSteamType
from .subscribe_terraria import SubscribeTerrariaType
from .subscribe_tmodloader import SubscribeTModLoaderType

SubscribeSchema = merge_types(
    name="SubscribeSchema",
    types=(
        SubscribeMinecraftJavaEditionType,
        SubscribePalworldType,
        SubscribeSteamType,
        SubscribeTerrariaType,
        SubscribeTModLoaderType,
    ),
)

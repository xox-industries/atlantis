from strawberry.tools import merge_types

from .minecraft_java_edition import MutationMinecraftJavaEditionType
from .palworld import MutationPalworldType
from .steam import MutationSteamType
from .terraria import MutationTerrariaType
from .tmodloader import MutationTModLoaderType
from .valheim import MutationValheimType

MutationSchema = merge_types(
    name="MutationSchema",
    types=(
        MutationMinecraftJavaEditionType,
        MutationPalworldType,
        MutationSteamType,
        MutationTerrariaType,
        MutationTModLoaderType,
        MutationValheimType,
    ),
)

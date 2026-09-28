from strawberry.tools import merge_types

from .minecraft_java_edition import MutationMinecraftJavaEditionType
from .palworld import MutationPalworldType
from .steam import MutationSteamType

MutationSchema = merge_types(
    name="MutationSchema",
    types=(
        MutationMinecraftJavaEditionType,
        MutationPalworldType,
        MutationSteamType,
    ),
)

from strawberry.tools import merge_types

from .palworld import MutationPalworldType
from .steam import MutationSteamType

MutationSchema = merge_types(
    name="MutationSchema",
    types=(
        MutationPalworldType,
        MutationSteamType,
    ),
)

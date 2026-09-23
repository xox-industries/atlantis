from strawberry.tools import merge_types

from .palworld import MutationPalworldType

MutationSchema = merge_types(
    name="MutationSchema",
    types=(MutationPalworldType,),
)

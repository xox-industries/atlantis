from strawberry.tools import merge_types

from src.route.query.display_palworld import DisplayPalworldType

QuerySchema = merge_types(
    name="QuerySchema",
    types=(DisplayPalworldType,),
)

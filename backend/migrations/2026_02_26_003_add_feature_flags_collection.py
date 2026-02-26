"""Create feature_flags collection and index."""


async def up(db):
    await db.feature_flags.create_index(
        [("feature_key", 1)], unique=True, background=True
    )
    return "feature_flags index created"


async def down(db):
    pass

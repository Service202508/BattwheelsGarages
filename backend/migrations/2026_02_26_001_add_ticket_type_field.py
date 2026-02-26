"""Add ticket_type field to existing tickets."""


async def up(db):
    result = await db.tickets.update_many(
        {"ticket_type": {"$exists": False}},
        {"$set": {"ticket_type": "onsite"}}
    )
    await db.tickets.create_index(
        [("organization_id", 1), ("ticket_type", 1)],
        background=True
    )
    return f"Updated {result.modified_count} tickets, index created"


async def down(db):
    pass

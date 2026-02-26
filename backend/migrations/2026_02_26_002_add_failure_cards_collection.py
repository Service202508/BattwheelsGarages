"""Create failure_cards collection and indexes."""


async def up(db):
    # Create indexes for failure_cards
    await db.failure_cards.create_index(
        [("organization_id", 1), ("ticket_id", 1)],
        unique=True, background=True
    )
    await db.failure_cards.create_index(
        [("organization_id", 1), ("vehicle_make", 1), ("fault_category", 1)],
        background=True
    )
    await db.failure_cards.create_index(
        [("organization_id", 1), ("created_at", -1)],
        background=True
    )
    await db.failure_cards.create_index(
        [("card_id", 1)], unique=True, background=True
    )
    
    # Create efi_platform_patterns indexes
    await db.efi_platform_patterns.create_index(
        [("vehicle_make", 1), ("vehicle_model", 1), ("fault_category", 1)],
        background=True
    )
    await db.efi_platform_patterns.create_index(
        [("pattern_id", 1)], unique=True, background=True
    )
    
    return "failure_cards and efi_platform_patterns indexes created"


async def down(db):
    pass

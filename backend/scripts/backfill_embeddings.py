"""
Backfill missing embeddings for EVFI failure cards.

Queries all failure_cards where embedding_vector is null/missing,
generates embeddings using EFIEmbeddingManager, and updates each card.
"""

import asyncio
import os
import sys

# Load environment
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone


async def backfill():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    from services.efi_embedding_service import EFIEmbeddingManager
    svc = EFIEmbeddingManager(db)

    # Find cards without embeddings
    query = {"$or": [
        {"embedding_vector": {"$exists": False}},
        {"embedding_vector": None},
    ]}
    total = await db.failure_cards.count_documents(query)
    print(f"Cards without embeddings: {total}")

    if total == 0:
        print("Nothing to backfill.")
        return

    succeeded = 0
    failed = 0
    cursor = db.failure_cards.find(query, {"_id": 0})

    async for card in cursor:
        card_id = card.get("card_id", "?")
        card_text = " ".join(filter(None, [
            card.get("issue_title", ""),
            card.get("issue_description", ""),
            card.get("root_cause", ""),
            card.get("fault_category", ""),
        ])).strip()

        if not card_text:
            failed += 1
            continue

        try:
            result = await svc.generate_complaint_embedding(card_text)
            if result and result.get("embedding"):
                await db.failure_cards.update_one(
                    {"card_id": card_id},
                    {"$set": {
                        "embedding_vector": result["embedding"],
                        "subsystem_category": result.get("classified_subsystem"),
                        "embedding_generated_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )
                succeeded += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            if (succeeded + failed) % 50 == 0:
                print(f"  Error on {card_id}: {e}")

        processed = succeeded + failed
        if processed % 50 == 0:
            print(f"  Progress: {processed}/{total} (ok={succeeded}, err={failed})")

    print(f"\nDone. Succeeded: {succeeded}, Failed: {failed}, Total: {total}")
    client.close()


if __name__ == "__main__":
    asyncio.run(backfill())

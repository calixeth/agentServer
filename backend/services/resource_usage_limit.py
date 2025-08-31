from common.error import raise_error
from infra.db import resource_limits_col, resource_usage_col


async def check_limit_and_record(client: str, resource: str):
    doc = await resource_limits_col.find_one({"resource": resource})
    if not doc:
        limit = 4
    else:
        limit = doc["limit"]

    usage = await resource_usage_col.find_one_and_update(
        {"client": client, "resource": resource},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )

    if "limit" in usage:
        limit = usage["limit"]

    count = usage["count"] + 1 if usage else 1

    if count > limit:
        raise_error(f"{client} exceeded limit for {resource} ({limit})")

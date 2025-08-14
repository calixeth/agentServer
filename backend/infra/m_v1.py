import asyncio

from infra.db import aigc_task_col


async def m_v1():
    cursor = aigc_task_col.find({})
    async for doc in cursor:
        print(doc)

        if 'cover' not in doc or doc['cover'] is None:
            await aigc_task_col.delete_one({'_id': doc['_id']})


asyncio.run(m_v1())

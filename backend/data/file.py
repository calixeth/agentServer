import base64
import logging
import os
import uuid

import aioboto3
import aiohttp

from config import SETTINGS


async def img_url_to_base64(image_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            response.raise_for_status()
            content = await response.read()
            encoded_data = base64.b64encode(content).decode("utf-8")
            return "data:image/png;base64," + encoded_data


async def download_and_upload_image(url, bucket_name):
    file_name = f"{uuid.uuid4()}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()

                with open(file_name, 'wb') as f:
                    f.write(content)

                session = aioboto3.Session()
                async with session.client(
                        "s3",
                        region_name="ap-southeast-2",
                        aws_access_key_id=SETTINGS.AWS_ACCESS_KEY,
                        aws_secret_access_key=SETTINGS.AWS_SECRET_KEY,
                ) as s3:
                    await s3.put_object(
                        Bucket=bucket_name,
                        Key=file_name,
                        Body=content,
                        ACL="public-read",
                        ContentType=response.headers.get("Content-Type", "application/octet-stream")
                    )
                fileurl = f"https://{bucket_name}.s3.ap-southeast-2.amazonaws.com/{file_name}"
                return fileurl

    except Exception as e:
        logging.error(f"download_and_upload_image {e}", exc_info=True)
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
    return ""

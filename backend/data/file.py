import base64
import logging
import os
import uuid

import aioboto3
import aiohttp
from fastapi import UploadFile

from config import SETTINGS
from data.db import file_col
from entities.bo import FileBO

bucket_name = "deepweb3"


async def img_url_to_base64(image_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            response.raise_for_status()
            content = await response.read()
            encoded_data = base64.b64encode(content).decode("utf-8")
            return "data:image/png;base64," + encoded_data


async def download_and_upload_image(url):
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


async def s3_upload_file(file: UploadFile) -> FileBO:
    """
    Upload file to S3 storage
    """
    file_uuid = str(uuid.uuid4())
    file_content = file.file.read()
    file_size = len(file_content)

    # Get content type, if file object doesn't provide it, guess from filename
    content_type = file.content_type
    if not content_type:
        content_type = _guess_content_type(file.filename)

    session = aioboto3.Session()
    async with session.client(
            "s3",
            region_name="ap-southeast-2",
            aws_access_key_id=SETTINGS.AWS_ACCESS_KEY,
            aws_secret_access_key=SETTINGS.AWS_SECRET_KEY,
    ) as s3:
        await s3.put_object(
            Bucket=bucket_name,
            Key=file_uuid,
            Body=file_content,
            ACL="public-read",
            ContentType=content_type
        )

    logging.info(f"File uploaded to S3: {file_uuid}, size: {file_size}, type: {content_type}")

    bo = FileBO(
        url=f"https://{bucket_name}.s3.ap-southeast-2.amazonaws.com/{file_uuid}"
    )

    file_col.insert_one(bo.model_dump())

    return bo


def _guess_content_type(filename: str) -> str:
    """
    Guess content type based on filename
    """
    import mimetypes
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'

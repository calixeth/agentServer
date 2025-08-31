import base64
import logging
import os
import uuid

import aioboto3
import aiohttp
from fastapi import UploadFile
from openai.types import Image

from config import SETTINGS
from entities.bo import FileBO
from infra.db import file_col

bucket_name = "web3ai"


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


async def upload_audio_file(audio_data: bytes, file_extension: str) -> str | None:
    """
    Upload audio file data to S3 storage
    
    Args:
        audio_data: Audio data as bytes
        file_extension: File extension (e.g., 'mp3', 'opus', 'aac', 'flac')
        
    Returns:
        Audio file URL if successful, None if failed
    """
    try:
        if not file_extension:
            file_extension = "mp3"
        file_uuid = str(uuid.uuid4())
        file_key = f"{file_uuid}.{file_extension}"

        # Determine content type based on file extension
        content_type_map = {
            'mp3': 'audio/mpeg',
            'opus': 'audio/opus',
            'aac': 'audio/aac',
            'flac': 'audio/flac',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg'
        }

        content_type = content_type_map.get(file_extension.lower(), 'audio/mpeg')

        session = aioboto3.Session()
        async with session.client(
                "s3",
                region_name="ap-southeast-2",
                aws_access_key_id=SETTINGS.AWS_ACCESS_KEY,
                aws_secret_access_key=SETTINGS.AWS_SECRET_KEY,
        ) as s3:
            await s3.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=audio_data,
                ACL="public-read",
                ContentType=content_type
            )

        audio_url = f"https://{bucket_name}.s3.ap-southeast-2.amazonaws.com/{file_key}"

        logging.info(f"Audio file uploaded to S3: {file_key}, size: {len(audio_data)} bytes, type: {content_type}")

        return audio_url

    except Exception as e:
        logging.error(f"Error uploading audio file: {e}", exc_info=True)
        return None


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


async def s3_upload_openai_img(img: Image) -> str | None:
    """
    Upload file to S3 storage
    """
    try:
        image_bytes = base64.b64decode(img.b64_json)
        file_uuid = str(uuid.uuid4())
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
                Body=image_bytes,
                ACL="public-read",
                ContentType='image/png'
            )

        url = f"https://{bucket_name}.s3.ap-southeast-2.amazonaws.com/{file_uuid}"

        return url
    except Exception as e:
        return None


def _guess_content_type(filename: str) -> str:
    """
    Guess content type based on filename
    """
    import mimetypes
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'

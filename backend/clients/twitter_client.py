import logging
from typing import Optional

import aiohttp

from config import SETTINGS

logger = logging.getLogger('twitter_client')

host = f"https://{SETTINGS.TWITTER241_HOST}"

headers = {
    f"x-{SETTINGS.TWITTER241}-host": SETTINGS.TWITTER241_HOST,
    f"x-{SETTINGS.TWITTER241}-key": SETTINGS.TWITTER241_KEY
}


async def twitter_fetch_user(username: str):
    url = f"{host}/user?username={username}"
    logger.info(f"Fetching {url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()

    return None


async def twitter_fetch_tweet_details(pid: str):
    """
    Fetch tweet information by PID (tweet ID)
    
    Args:
        pid: Tweet ID to fetch
        
    Returns:
        Tweet data dictionary or None if failed
    """
    url = f"{host}/tweet-v2?pid={pid}"
    logger.info(f"Fetching tweet {pid} from {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched tweet {pid}")
                    return data
                else:
                    logger.error(f"Failed to fetch tweet {pid}, status: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching tweet {pid}: {e}", exc_info=True)
        return None


async def get_tweet_summary(pid: str) -> Optional[dict]:
    """
    Get a summary of tweet information by PID

    Args:
        pid: Tweet ID (PID)

    Returns:
        Dictionary with tweet summary, or None if failed
    """
    try:
        # Fetch tweet data
        tweet_data = await twitter_fetch_tweet_details(pid)
        if not tweet_data:
            return None

        # Extract content
        content = await extract_tweet_content(tweet_data)
        if not content:
            return None

        return {
            'pid': pid,
            'content': content,
            'raw_data': tweet_data
        }

    except Exception as e:
        logger.error(f"Error getting tweet summary: {e}", exc_info=True)
        return None


async def extract_tweet_content(tweet_data: dict) -> Optional[dict]:
    """
    Extract key tweet content from the raw Twitter API response
    Args:
        tweet_data: Raw tweet data from Twitter API
    Returns:
        Dictionary with extracted tweet content, or None if failed
    """
    try:
        if not tweet_data or 'result' not in tweet_data:
            return None

        tweet_result = tweet_data.get('result', {}).get('tweetResult', {}).get('result', {})
        if not tweet_result or tweet_result.get('__typename') != 'Tweet':
            return None

        return {
            'tweet_id': tweet_result.get('rest_id'),
            'full_text': tweet_result.get('legacy', {}).get('full_text'),
            'created_at': tweet_result.get('legacy', {}).get('created_at'),
            'user': {
                'screen_name': tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy',
                                                                                                          {}).get(
                    'screen_name'),
                'name': tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {}).get(
                    'name'),
                'profile_image_url': tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get(
                    'legacy', {}).get('profile_image_url_https')
            },
            'stats': {
                'favorite_count': tweet_result.get('legacy', {}).get('favorite_count'),
                'retweet_count': tweet_result.get('legacy', {}).get('retweet_count'),
                'reply_count': tweet_result.get('legacy', {}).get('reply_count'),
                'quote_count': tweet_result.get('legacy', {}).get('quote_count'),
                'view_count': tweet_result.get('views', {}).get('count')
            },
            'media': tweet_result.get('legacy', {}).get('extended_entities', {}).get('media', [])
        }
    except Exception as e:
        logger.error(f"Error extracting single tweet content: {e}", exc_info=True)
        return None

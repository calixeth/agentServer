import base64
import io
import logging
from typing import Optional, Dict, Any

import aiohttp
import openai

from config import SETTINGS


class TTSClient:
    """Text-to-Speech client using OpenAI's GPT-4o mini TTS model"""
    
    def __init__(self):
        self.client = openai.AsyncClient(
            api_key=SETTINGS.OPENAI_API_KEY,
        )
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        response_format: str = "mp3",
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Convert text to speech using OpenAI's TTS API
        
        Args:
            text: The text to convert to speech
            voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: The TTS model to use (tts-1, tts-1-hd)
            response_format: The audio format (mp3, opus, aac, flac)
            speed: The speed of the speech (0.25 to 4.0)
            
        Returns:
            Audio data as bytes, or None if failed
        """
        try:
            logging.info(f"Converting text to speech: {text[:50]}...")
            
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
                speed=speed
            )
            
            if response:
                audio_data = response.content
                logging.info(f"TTS conversion successful, audio size: {len(audio_data)} bytes")
                return audio_data
            else:
                logging.error("TTS conversion failed: no response")
                return None
                
        except Exception as e:
            logging.error(f"TTS conversion error: {e}", exc_info=True)
            return None
    
    async def text_to_speech_base64(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        response_format: str = "mp3",
        speed: float = 1.0
    ) -> Optional[str]:
        """
        Convert text to speech and return as base64 encoded string
        
        Args:
            text: The text to convert to speech
            voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: The TTS model to use (tts-1, tts-1-hd)
            response_format: The audio format (mp3, opus, aac, flac)
            speed: The speed of the speech (0.25 to 4.0)
            
        Returns:
            Base64 encoded audio data as string, or None if failed
        """
        try:
            audio_data = await self.text_to_speech(text, voice, model, response_format, speed)
            if audio_data:
                base64_audio = base64.b64encode(audio_data).decode('utf-8')
                logging.info(f"TTS base64 conversion successful")
                return base64_audio
            return None
        except Exception as e:
            logging.error(f"TTS base64 conversion error: {e}", exc_info=True)
            return None

    async def call_language_model(
        self,
        prompt: str,
        model: str = "gpt-4o",
        max_tokens: int = 10000,
        temperature: float = 0.7,
        system_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Call language model with prompt and optional parameters
        
        Args:
            prompt: The input prompt for the language model
            model: The language model to use (gpt-4o-mini, gpt-4o, gpt-3.5-turbo, etc.)
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 2.0)
            system_message: Optional system message to set context
            
        Returns:
            Generated text response, or None if failed
        """
        try:
            logging.info(f"Calling language model {model} with prompt: {prompt[:50]}...")
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response and response.choices:
                generated_text = response.choices[0].message.content
                logging.info(f"Language model response successful, length: {len(generated_text)}")
                return generated_text
            else:
                logging.error("Language model call failed: no response")
                return None
                
        except Exception as e:
            logging.error(f"Language model call error: {e}", exc_info=True)
            return None

    async def call_language_model_with_audio(
        self,
        prompt: str,
        audio_data: bytes,
        model: str = "gpt-4o",
        max_tokens: int = 10000,
        temperature: float = 0.7,
        system_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Call language model with prompt and audio input
        
        Args:
            prompt: The text prompt for the language model
            audio_data: Audio data as bytes
            model: The language model to use (gpt-4o-mini, gpt-4o, etc.)
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 2.0)
            system_message: Optional system message to set context
            
        Returns:
            Generated text response, or None if failed
        """
        try:
            logging.info(f"Calling language model {model} with audio input, prompt: {prompt[:50]}...")
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add audio message
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "audio",
                        "audio": {
                            "data": audio_base64,
                            "type": "audio/mpeg"  # Adjust based on your audio format
                        }
                    }
                ]
            })
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response and response.choices:
                generated_text = response.choices[0].message.content
                logging.info(f"Language model with audio response successful, length: {len(generated_text)}")
                return generated_text
            else:
                logging.error("Language model with audio call failed: no response")
                return None
                
        except Exception as e:
            logging.error(f"Language model with audio call error: {e}", exc_info=True)
            return None


# Global TTS client instance
tts_client = TTSClient()


async def text_to_speech_svc(
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
    response_format: str = "mp3",
    speed: float = 1.0
) -> Optional[bytes]:
    """
    Service function for text-to-speech conversion
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer)
        model: The TTS model to use (tts-1, tts-1-hd)
        response_format: The audio format (mp3, opus, aac, flac)
        speed: The speed of the speech (0.25 to 4.0)
        
    Returns:
        Audio data as bytes, or None if failed
    """
    return await tts_client.text_to_speech(text, voice, model, response_format, speed)


async def text_to_speech_base64_svc(
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
    response_format: str = "mp3",
    speed: float = 1.0
) -> Optional[str]:
    """
    Service function for text-to-speech conversion returning base64
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer)
        model: The TTS model to use (tts-1, tts-1-hd)
        response_format: The audio format (mp3, opus, aac, flac)
        speed: The speed of the speech (0.25 to 4.0)
        
    Returns:
        Base64 encoded audio data as string, or None if failed
    """
    return await tts_client.text_to_speech_base64(text, voice, model, response_format, speed)


async def call_model(
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: int = 15000,
    temperature: float = 0.7,
    system_message: Optional[str] = None
) -> Optional[str]:
    """
    Service function for language model calls
    
    Args:
        prompt: The input prompt for the language model
        model: The language model to use (gpt-4o-mini, gpt-4o, gpt-3.5-turbo, etc.)
        max_tokens: Maximum number of tokens to generate
        temperature: Controls randomness (0.0 to 2.0)
        system_message: Optional system message to set context
        
    Returns:
        Generated text response, or None if failed
    """
    return await tts_client.call_language_model(prompt, model, max_tokens, temperature, system_message)


async def call_model_with_audio(
    prompt: str,
    audio_data: bytes,
    model: str = "gpt-4o",
    max_tokens: int = 15000,
    temperature: float = 0.7,
    system_message: Optional[str] = None
) -> Optional[str]:
    """
    Service function for language model calls with audio input
    
    Args:
        prompt: The text prompt for the language model
        audio_data: Audio data as bytes
        model: The language model to use (gpt-4o-mini, gpt-4o, etc.)
        max_tokens: Maximum number of tokens to generate
        temperature: Controls randomness (0.0 to 2.0)
        system_message: Optional system message to set context
        
    Returns:
        Generated text response, or None if failed
    """
    return await tts_client.call_language_model_with_audio(prompt, audio_data, model, max_tokens, temperature, system_message) 
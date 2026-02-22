"""LLM service using NVIDIA API with Deepseek V3 model - Direct HTTP."""

import json
import logging
from typing import Optional

import requests

from src.core.config import (
    NVIDIA_API_KEY,
    NVIDIA_MODEL,
    NVIDIA_BASE_URL,
)

logger = logging.getLogger("llm")

REQUEST_TIMEOUT = 600  # seconds


class LLMService:
    """Service for interacting with NVIDIA LLM API via direct HTTP."""

    def __init__(self):
        """Initialize LLM service with NVIDIA API."""
        if not NVIDIA_API_KEY:
            logger.error("NVIDIA_API_KEY not set in environment variables")
            raise ValueError("NVIDIA_API_KEY not set in environment variables")

        logger.info(f"🔧 Initializing LLMService with NVIDIA model: {NVIDIA_MODEL}")
        
        self.api_key = NVIDIA_API_KEY
        self.model = NVIDIA_MODEL
        self.base_url = NVIDIA_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json",
        }
        
        logger.info("✓ LLMService initialized successfully with NVIDIA")

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """
        Generate text using NVIDIA's Deepseek model via direct HTTP.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            Generated text response
        """
        logger.debug(f"Generating text with LLM (model: {self.model}, max_tokens: {max_tokens})...")
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            url = f"{self.base_url}/chat/completions"
            logger.info(f"🔧 Calling NVIDIA API ({self.model})...")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"NVIDIA API error: {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                raise RuntimeError(f"NVIDIA API returned {response.status_code}: {response.text[:200]}")
            
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            logger.info(f"✅ LLM generation complete: {len(result) if result else 0} characters")
            return result if result else ""

        except requests.exceptions.Timeout as e:
            logger.error(f"LLM request timeout (>{REQUEST_TIMEOUT}s): {e}")
            raise RuntimeError(f"NVIDIA API timeout after {REQUEST_TIMEOUT} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request error: {e}")
            raise RuntimeError(f"Failed to call NVIDIA API: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise RuntimeError(f"Invalid response from NVIDIA API: {e}")
        except Exception as e:
            logger.error(f"LLM generation error: {type(e).__name__}: {e}")
            raise



# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

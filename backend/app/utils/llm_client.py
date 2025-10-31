"""LLM Client for interacting with OpenAI/Anthropic APIs."""

import logging
from typing import List, Dict, Any, Optional
import openai
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for LLM API interactions.

    Supports OpenAI and Anthropic models with structured output mode.
    """

    def __init__(self):
        """Initialize LLM client."""
        self.provider = settings.DEFAULT_LLM_PROVIDER.lower()

        if self.provider == "openai":
            self.openai_client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=httpx.Timeout(settings.LLM_TIMEOUT),
            )
        elif self.provider == "anthropic":
            # Initialize Anthropic client if needed
            pass

        logger.info(f"Initialized LLM client with provider: {self.provider}")

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate structured output using LLM.

        Uses JSON schema mode to ensure valid JSON responses.

        Args:
            system_prompt: System instructions
            user_prompt: User query
            schema: JSON schema for output structure
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature

        Returns:
            Parsed JSON response
        """
        try:
            model = model or settings.DEFAULT_MODEL

            if self.provider == "openai":
                return await self._openai_structured_output(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=schema,
                    model=model,
                    temperature=temperature,
                )
            elif self.provider == "anthropic":
                return await self._anthropic_structured_output(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=schema,
                    model=model,
                    temperature=temperature,
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        except Exception as e:
            logger.error(f"Error generating structured output: {str(e)}", exc_info=True)
            raise

    async def _openai_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        model: str,
        temperature: float,
    ) -> dict:
        """Generate structured output using OpenAI API."""
        try:
            logger.debug(f"Calling OpenAI {model} with structured output")

            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Empty response from OpenAI")

            # Parse JSON
            import json

            result = json.loads(content)

            logger.debug(f"OpenAI response parsed successfully")

            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise

    async def _anthropic_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        model: str,
        temperature: float,
    ) -> dict:
        """Generate structured output using Anthropic API."""
        # Implement Anthropic-specific logic if needed
        raise NotImplementedError("Anthropic provider not yet implemented")

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for text list.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors
        """
        try:
            model = model or settings.EMBEDDING_MODEL

            if self.provider == "openai":
                return await self._openai_embeddings(texts, model)
            else:
                raise ValueError(
                    f"Embeddings not supported for provider: {self.provider}"
                )

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
            raise

    async def _openai_embeddings(
        self, texts: List[str], model: str
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        try:
            # Process in batches if needed (OpenAI limit is typically 2048 texts)
            batch_size = 500
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]

                logger.debug(f"Generating embeddings for batch of {len(batch)} texts")

                response = await self.openai_client.embeddings.create(
                    model=model, input=batch
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            logger.debug(f"Generated {len(all_embeddings)} embeddings")

            return all_embeddings

        except Exception as e:
            logger.error(f"OpenAI embeddings error: {str(e)}", exc_info=True)
            raise

    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate a simple text completion.

        Args:
            prompt: Input prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            model = model or settings.DEFAULT_MODEL

            if self.provider == "openai":
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return response.choices[0].message.content or ""

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}", exc_info=True)
            raise

"""LLM Client for interacting with OpenAI/Google Gemini APIs."""

import logging
from typing import List, Dict, Any, Optional
import openai
import httpx
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for LLM API interactions.

    Supports OpenAI (GPT) and Google Gemini models with structured output mode.
    """

    def __init__(self):
        """Initialize LLM client."""
        self.provider = settings.DEFAULT_LLM_PROVIDER.lower()

        if self.provider == "openai":
            self.openai_client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=httpx.Timeout(settings.LLM_TIMEOUT),
            )
        elif self.provider == "gemini":
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_client = genai

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
            elif self.provider == "gemini":
                return await self._gemini_structured_output(
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

    async def _gemini_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        model: str,
        temperature: float,
    ) -> dict:
        """Generate structured output using Google Gemini API."""
        try:
            logger.debug(f"Calling Gemini {model} with structured output")

            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nIMPORTANT: Respond with valid JSON only, no markdown formatting."

            gemini_model = self.gemini_client.GenerativeModel(model)
            
            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=8192,
            )

            # Generate response
            response = await gemini_model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
            )

            content = response.text

            if not content:
                raise ValueError("Empty response from Gemini")

            # Clean up markdown formatting if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parse JSON
            import json

            result = json.loads(content)

            logger.debug(f"Gemini response parsed successfully")

            return result

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            raise

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
            elif self.provider == "gemini":
                return await self._gemini_embeddings(texts, model)
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

    async def _gemini_embeddings(
        self, texts: List[str], model: str = "models/embedding-001"
    ) -> List[List[float]]:
        """Generate embeddings using Google Gemini API."""
        try:
            # Process in batches
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]

                logger.debug(f"Generating Gemini embeddings for batch of {len(batch)} texts")

                # Generate embeddings for each text in batch
                for text in batch:
                    result = self.gemini_client.embed_content(
                        model=model,
                        content=text,
                        task_type="retrieval_document",
                    )
                    all_embeddings.append(result['embedding'])

            logger.debug(f"Generated {len(all_embeddings)} Gemini embeddings")

            return all_embeddings

        except Exception as e:
            logger.error(f"Gemini embeddings error: {str(e)}", exc_info=True)
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

            elif self.provider == "gemini":
                gemini_model = self.gemini_client.GenerativeModel(model)
                generation_config = genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
                response = await gemini_model.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                )
                return response.text

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}", exc_info=True)
            raise

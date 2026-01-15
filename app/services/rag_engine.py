"""RAG (Retrieval-Augmented Generation) engine using OpenRouter/OpenAI API."""

import json
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import LLMError, RAGError
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGEngine:
    """Service for RAG pipeline with LLM."""

    def __init__(self):
        """Initialize RAG engine with OpenAI-compatible client for OpenRouter."""
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        self.model = settings.openrouter_model
        self.temperature = settings.temperature
        self.max_context_length = settings.max_context_length

    def _build_prompt(
        self, error_message: str, similar_logs: List[Dict[str, Any]], context: Optional[str] = None
    ) -> str:
        """
        Build RAG prompt with context from similar logs.

        Args:
            error_message: Current error message
            similar_logs: List of similar historical logs
            context: Additional context

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are an expert DevOps engineer analyzing application logs and errors.",
            "Your task is to provide root cause analysis and recommended fixes based on the current error and similar historical errors.",
            "",
            "CURRENT ERROR:",
            error_message,
            "",
        ]

        if similar_logs:
            prompt_parts.append("SIMILAR HISTORICAL ERRORS:")
            for i, log in enumerate(similar_logs[:5], 1):  # Top 5 similar logs
                similarity = log.get("similarity", 0.0)
                service = log.get("service_name", "unknown")
                level = log.get("error_level", "UNKNOWN")
                message = log.get("error_message", log.get("document", ""))
                prompt_parts.append(
                    f"{i}. [Similarity: {similarity:.2f}] [{service}] [{level}]: {message}"
                )
            prompt_parts.append("")

        if context:
            prompt_parts.append(f"ADDITIONAL CONTEXT: {context}")
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "Please provide:",
                "1. ROOT CAUSE: A brief explanation of the likely root cause",
                "2. RECOMMENDED FIX: Specific actionable steps to resolve the issue",
                "3. CONFIDENCE: A confidence score from 0.0 to 1.0",
                "",
                "Format your response as JSON with keys: 'root_cause', 'recommended_fix', 'confidence'",
            ]
        )

        return "\n".join(prompt_parts)

    async def generate_resolution(
        self,
        error_message: str,
        similar_logs: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate resolution using RAG.

        Args:
            error_message: Current error message
            similar_logs: List of similar historical logs
            context: Additional context

        Returns:
            Dictionary with root_cause, recommended_fix, and confidence
        """
        try:
            # Build prompt
            prompt = self._build_prompt(error_message, similar_logs, context)

            # Truncate if too long
            if len(prompt) > self.max_context_length:
                prompt = prompt[: self.max_context_length] + "...[truncated]"

            logger.info(f"Calling LLM with model: {self.model}")

            # Call LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert DevOps engineer specializing in log analysis and error resolution.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=1000,
                timeout=30.0,
            )

            # Extract response
            if not response.choices or not response.choices[0].message.content:
                raise RAGError("Empty response from LLM")

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                # Try to extract JSON if wrapped in markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                result = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract structured content manually
                logger.warning("Failed to parse JSON response, attempting manual extraction")
                result = self._parse_unstructured_response(content)

            # Validate and normalize result
            root_cause = result.get("root_cause", "Unable to determine root cause")
            recommended_fix = result.get("recommended_fix", "No specific fix recommended")
            confidence = float(result.get("confidence", 0.5))

            # Clamp confidence between 0 and 1
            confidence = max(0.0, min(1.0, confidence))

            return {
                "root_cause": root_cause,
                "recommended_fix": recommended_fix,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error generating resolution with RAG: {e}")
            if isinstance(e, RAGError):
                raise
            raise RAGError(f"Failed to generate resolution: {e}")

    def _parse_unstructured_response(self, content: str) -> Dict[str, Any]:
        """
        Parse unstructured LLM response.

        Args:
            content: Response content

        Returns:
            Dictionary with parsed fields
        """
        result: Dict[str, Any] = {
            "root_cause": "",
            "recommended_fix": "",
            "confidence": 0.5,
        }

        # Try to extract sections
        lines = content.split("\n")
        current_section = None

        for line in lines:
            line_lower = line.lower().strip()
            if "root cause" in line_lower:
                current_section = "root_cause"
                result["root_cause"] = line.split(":", 1)[-1].strip() if ":" in line else ""
            elif "fix" in line_lower or "solution" in line_lower:
                current_section = "recommended_fix"
                result["recommended_fix"] = line.split(":", 1)[-1].strip() if ":" in line else ""
            elif "confidence" in line_lower:
                try:
                    confidence_str = line.split(":")[-1].strip()
                    result["confidence"] = float(confidence_str)
                except (ValueError, IndexError):
                    pass
            elif current_section and line.strip():
                result[current_section] += " " + line.strip()

        # Fallback: use entire content if sections not found
        if not result["root_cause"] and not result["recommended_fix"]:
            parts = content.split("\n\n")
            if len(parts) >= 2:
                result["root_cause"] = parts[0].strip()
                result["recommended_fix"] = parts[1].strip()
            else:
                result["root_cause"] = content[:200]
                result["recommended_fix"] = content[200:400] if len(content) > 200 else ""

        return result


# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine

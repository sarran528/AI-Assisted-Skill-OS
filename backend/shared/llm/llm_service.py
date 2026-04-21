"""
LLM service - unified interface for OpenAI/Anthropic.
"""
import json
from typing import Optional, Any
from openai import OpenAI
from anthropic import Anthropic


class LLMService:
    """Unified LLM service for both OpenAI and Anthropic."""

    def __init__(self, provider: str = "openai", api_key: str = ""):
        self.provider = provider
        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            self.client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate_structured_response(
        self,
        prompt: str,
        schema: dict,
        temperature: float = 0.0,
    ) -> dict:
        """
        Generate a structured JSON response from LLM.
        
        Args:
            prompt: The input prompt
            schema: JSON schema for the response
            temperature: Temperature for sampling (0 = deterministic)
            
        Returns:
            Parsed JSON response matching schema
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a helpful assistant. Respond only with valid JSON matching this schema: {json.dumps(schema)}",
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                result = json.loads(response.choices[0].message.content)
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-opus",
                    temperature=temperature,
                    max_tokens=2048,
                    system=f"You are a helpful assistant. Respond only with valid JSON matching this schema: {json.dumps(schema)}",
                    messages=[{"role": "user", "content": prompt}],
                )
                result = json.loads(response.content[0].text)
            else:
                result = {}

            return result
        except (json.JSONDecodeError, Exception) as e:
            # Return conservative default on failure
            return {"error": str(e), "status": "failed"}

    def generate_explanation(
        self,
        prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate a free-form explanation text.
        
        Args:
            prompt: The input prompt
            temperature: Temperature for sampling
            
        Returns:
            Generated explanation text
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-opus",
                    temperature=temperature,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            else:
                return ""
        except Exception as e:
            return f"Error generating explanation: {str(e)}"

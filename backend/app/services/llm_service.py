import google.generativeai as genai
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from loguru import logger
import json


class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini client"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info(f"Initialized Gemini service with model: {settings.GEMINI_MODEL}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate text completion using Gemini
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system_instruction: System-level instruction
            
        Returns:
            Generated text response
        """
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature or settings.GEMINI_TEMPERATURE,
                max_output_tokens=max_tokens or settings.GEMINI_MAX_TOKENS
            )
            
            # Add system instruction if provided
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output
        
        Args:
            prompt: The input prompt
            schema: Expected JSON schema (optional)
            temperature: Lower temp for more consistent JSON
            
        Returns:
            Parsed JSON object
        """
        try:
            # Instruct model to return valid JSON
            json_prompt = f"{prompt}\n\nReturn ONLY valid JSON, no other text."
            
            if schema:
                json_prompt += f"\n\nExpected schema:\n{json.dumps(schema, indent=2)}"
            
            response = await self.generate_text(
                prompt=json_prompt,
                temperature=temperature
            )
            
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            parsed_json = json.loads(response_text.strip())
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini: {str(e)}")
            logger.error(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating JSON: {str(e)}")
            raise
    
    async def extract_from_document(
        self,
        document_path: str,
        extraction_prompt: str
    ) -> str:
        """
        Extract information from documents (PDF, DOCX, etc.)
        Gemini supports multimodal inputs
        
        Args:
            document_path: Path to document file
            extraction_prompt: What to extract
            
        Returns:
            Extracted information as text
        """
        try:
            # Upload file to Gemini
            uploaded_file = genai.upload_file(document_path)
            
            # Generate content with file
            response = self.model.generate_content([
                extraction_prompt,
                uploaded_file
            ])
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error extracting from document: {str(e)}")
            raise
    
    async def analyze_similarity(
        self,
        text1: str,
        text2: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze semantic similarity between two texts
        
        Args:
            text1: First text (e.g., job description)
            text2: Second text (e.g., resume)
            context: Additional context for comparison
            
        Returns:
            Similarity analysis with score and reasoning
        """
        prompt = f"""
Analyze the similarity between these two texts:

TEXT 1:
{text1}

TEXT 2:
{text2}

{f'CONTEXT: {context}' if context else ''}

Provide a similarity analysis in JSON format:
{{
    "similarity_score": <float 0-1>,
    "key_matches": [<list of matching concepts>],
    "key_differences": [<list of differences>],
    "reasoning": "<explanation>"
}}
"""
        
        return await self.generate_json(prompt)
    
    async def summarize(
        self,
        text: str,
        max_length: int = 200
    ) -> str:
        """
        Summarize long text
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        prompt = f"""
Summarize the following text in {max_length} words or less:

{text}

Summary:
"""
        return await self.generate_text(prompt, temperature=0.5)


# Singleton instance
gemini_service = GeminiService()
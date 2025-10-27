from typing import Any, Dict, Optional
from loguru import logger
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.config import settings

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel


class BaseAgent:
    """
    Base class for all agentic components.
    
    This class is simplified for LangChain. It no longer implements
    the Perceive-Think-Act loop directly, but instead provides
    shared resources like the LLM, DB session, and logging
    to agentic chains.
    """
    
    def __init__(self, name: str, db: Session):
        """
        Initialize base agent
        
        Args:
            name: Agent identifier
            db: Database session
        """
        self.name = name
        self.db = db
        self.state: Dict[str, Any] = {}
        
        # Initialize the LangChain LLM
        # This will be shared by all agents
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                convert_system_message_to_human=True # Helps with models that don't support system roles
            )
            logger.info(f"Initialized agent: {self.name} with LangChain model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
            raise
    
    def _log_audit(
        self,
        phase: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> None:
        """
        Log agent action to audit trail
        
        Args:
            phase: Which phase (e.g., perceive, think, act, or chain step)
            message: Description of action
            metadata: Additional context
            severity: Log severity level
        """
        try:
            audit_log = AuditLog(
                event_type=f"agent_{phase}",
                event_category="agent",
                severity=severity,
                agent_name=self.name,
                agent_action=phase,
                message=message,
                metadata=metadata or {}
            )
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"[{self.name}] {phase.upper()}: {message}")
            
        except Exception as e:
            logger.error(f"Failed to log audit: {str(e)}")

    # The execute, perceive, think, act, reflect, adapt, ask_llm,
    # and ask_llm_json methods have been removed.
    # The agent-specific classes will now implement their
    # logic directly, using LangChain chains.
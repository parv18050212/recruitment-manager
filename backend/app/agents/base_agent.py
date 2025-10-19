from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from loguru import logger
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.services.llm_service import gemini_service


class BaseAgent(ABC):
    """
    Base class for all agentic components
    Implements the Perceive → Think → Act → Reflect → Adapt loop
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
        self.llm = gemini_service
        self.state: Dict[str, Any] = {}
        logger.info(f"Initialized agent: {self.name}")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution loop implementing agentic cycle
        
        Args:
            context: Input context for the agent
            
        Returns:
            Results of agent execution
        """
        try:
            # 1. PERCEIVE - Gather and understand context
            perceived_data = await self.perceive(context)
            self._log_audit("perceive", "Perceived input context", perceived_data)
            
            # 2. THINK - Analyze and plan next actions
            action_plan = await self.think(perceived_data)
            self._log_audit("think", "Generated action plan", action_plan)
            
            # 3. ACT - Execute planned actions
            results = await self.act(action_plan)
            self._log_audit("act", "Executed actions", results)
            
            # 4. REFLECT - Evaluate outcomes
            reflection = await self.reflect(results)
            self._log_audit("reflect", "Reflected on results", reflection)
            
            # 5. ADAPT - Update state based on learnings
            await self.adapt(reflection)
            
            return {
                "success": True,
                "agent": self.name,
                "results": results,
                "reflection": reflection,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {str(e)}")
            self._log_audit("error", f"Execution failed: {str(e)}", {"error": str(e)}, severity="error")
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @abstractmethod
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        PERCEIVE phase: Gather and understand input
        
        Args:
            context: Raw input context
            
        Returns:
            Structured perceived data
        """
        pass
    
    @abstractmethod
    async def think(self, perceived_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        THINK phase: Analyze data and plan actions
        
        Args:
            perceived_data: Output from perceive phase
            
        Returns:
            Action plan
        """
        pass
    
    @abstractmethod
    async def act(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        ACT phase: Execute planned actions
        
        Args:
            action_plan: Output from think phase
            
        Returns:
            Execution results
        """
        pass
    
    async def reflect(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        REFLECT phase: Evaluate outcomes (default implementation)
        
        Args:
            results: Output from act phase
            
        Returns:
            Reflection insights
        """
        return {
            "status": "completed",
            "learnings": [],
            "improvements": []
        }
    
    async def adapt(self, reflection: Dict[str, Any]) -> None:
        """
        ADAPT phase: Update internal state (default implementation)
        
        Args:
            reflection: Output from reflect phase
        """
        self.state["last_reflection"] = reflection
        self.state["last_execution"] = datetime.utcnow().isoformat()
    
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
            phase: Which phase (perceive, think, act, reflect, adapt)
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
    
    async def ask_llm(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Helper method to query LLM
        
        Args:
            prompt: Question/instruction for LLM
            system_instruction: System-level context
            temperature: Sampling temperature
            
        Returns:
            LLM response
        """
        return await self.llm.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature
        )
    
    async def ask_llm_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Helper method to get structured JSON from LLM
        
        Args:
            prompt: Question/instruction for LLM
            schema: Expected JSON structure
            
        Returns:
            Parsed JSON response
        """
        return await self.llm.generate_json(prompt=prompt, schema=schema)
"""
Base Agent class for PaperGuard multi-agent system.

Each agent has:
- Perception: Observes input
- Reasoning: Makes decisions
- Action: Executes tasks
- Memory: Maintains state
"""
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message passed between agents."""
    
    def __init__(
        self,
        sender: str,
        receiver: str,
        msg_type: str,
        content: Any,
        timestamp: Optional[datetime] = None
    ):
        self.sender = sender
        self.receiver = receiver
        self.msg_type = msg_type
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.id = f"{sender}-{receiver}-{self.timestamp.timestamp()}"
    
    def __repr__(self):
        return f"<AgentMessage from={self.sender} to={self.receiver} type={self.msg_type}>"


class BaseAgent(ABC):
    """Base class for all agents in PaperGuard."""
    
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.memory: List[Dict[str, Any]] = []
        self.message_queue: List[AgentMessage] = []
        self.state = "idle"
        
        logger.info(f"Agent initialized: {agent_id} ({role})")
    
    def perceive(self, observation: Any) -> Dict[str, Any]:
        """
        Perceive and process input from environment or other agents.
        
        Args:
            observation: Input data to process
            
        Returns:
            Processed observation
        """
        logger.debug(f"[{self.agent_id}] Perceiving: {type(observation)}")
        
        perceived = {
            "raw": observation,
            "timestamp": datetime.now(),
            "agent": self.agent_id
        }
        
        # Store in memory
        self.memory.append({
            "type": "perception",
            "data": perceived,
            "timestamp": datetime.now()
        })
        
        return perceived
    
    @abstractmethod
    def reason(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reason about the observation and decide on actions.
        
        Args:
            observation: Processed observation
            
        Returns:
            Decision/plan
        """
        pass
    
    @abstractmethod
    def act(self, decision: Dict[str, Any]) -> Any:
        """
        Execute action based on decision.
        
        Args:
            decision: Result from reasoning
            
        Returns:
            Action result
        """
        pass
    
    def run(self, input_data: Any) -> Any:
        """
        Main agent loop: Perceive -> Reason -> Act
        
        Args:
            input_data: Input to process
            
        Returns:
            Agent output
        """
        self.state = "running"
        
        try:
            # Perceive
            observation = self.perceive(input_data)
            
            # Reason
            decision = self.reason(observation)
            
            # Act
            result = self.act(decision)
            
            self.state = "idle"
            return result
            
        except Exception as e:
            self.state = "error"
            logger.error(f"[{self.agent_id}] Error: {e}")
            raise
    
    def send_message(self, receiver: str, msg_type: str, content: Any):
        """Send message to another agent."""
        msg = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            msg_type=msg_type,
            content=content
        )
        self.message_queue.append(msg)
        logger.debug(f"[{self.agent_id}] Sent message to {receiver}")
        return msg
    
    def receive_message(self, message: AgentMessage):
        """Receive message from another agent."""
        logger.debug(f"[{self.agent_id}] Received message from {message.sender}")
        self.memory.append({
            "type": "message_received",
            "data": message,
            "timestamp": datetime.now()
        })
    
    def get_memory(self, mem_type: Optional[str] = None) -> List[Dict]:
        """Retrieve memory, optionally filtered by type."""
        if mem_type:
            return [m for m in self.memory if m.get("type") == mem_type]
        return self.memory
    
    def clear_memory(self):
        """Clear agent memory."""
        self.memory = []
        logger.info(f"[{self.agent_id}] Memory cleared")
    
    def get_trace(self) -> List[Dict]:
        """Get verification trace for transparency."""
        return [
            {
                "agent": self.agent_id,
                "role": self.role,
                "timestamp": m["timestamp"].isoformat(),
                "type": m["type"],
                "data": str(m["data"])[:200]  # Truncate for display
            }
            for m in self.memory
        ]

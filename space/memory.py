"""
Session persistence and context window management for Space CLI.
"""
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class SessionManager:
    """Manage conversation sessions - save, load, and auto-save."""
    
    def __init__(self, sessions_dir: str = None):
        """Initialize session manager.
        
        Args:
            sessions_dir: Directory to store sessions. Defaults to ~/.space/sessions
        """
        if sessions_dir is None:
            sessions_dir = os.path.expanduser("~/.space/sessions")
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.last_save_time: float = 0
        self.auto_save_interval: int = 60  # seconds
    
    def new_session(self) -> str:
        """Create a new session and return its ID."""
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.current_session_id
    
    def save_session(self, messages: List[Dict[str, Any]], session_id: str = None) -> str:
        """Save conversation to JSON file.
        
        Args:
            messages: List of conversation messages
            session_id: Optional session ID (uses current if not provided)
            
        Returns:
            Path to saved session file
        """
        session_id = session_id or self.current_session_id or self.new_session()
        session_path = self.sessions_dir / f"{session_id}.json"
        
        session_data = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        
        with open(session_path, "w") as f:
            json.dump(session_data, f, indent=2, default=str)
        
        self.last_save_time = time.time()
        return str(session_path)
    
    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Load a previous session.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            List of messages from the session
        """
        session_path = self.sessions_dir / f"{session_id}.json"
        
        if not session_path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found")
        
        with open(session_path, "r") as f:
            session_data = json.load(f)
        
        self.current_session_id = session_id
        return session_data.get("messages", [])
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions.
        
        Returns:
            List of session metadata (id, created_at, message_count)
        """
        sessions = []
        for session_file in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data.get("id", session_file.stem),
                        "created_at": data.get("created_at", "Unknown"),
                        "message_count": data.get("message_count", 0)
                    })
            except:
                continue
        return sessions
    
    def should_auto_save(self) -> bool:
        """Check if enough time has passed for auto-save."""
        return time.time() - self.last_save_time >= self.auto_save_interval
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        session_path = self.sessions_dir / f"{session_id}.json"
        if session_path.exists():
            session_path.unlink()
            return True
        return False


class ContextWindow:
    """Manage context window size and token tracking."""
    
    # Approximate tokens per character (rough estimate for English text)
    CHARS_PER_TOKEN = 4
    
    def __init__(self, max_tokens: int = 8192):
        """Initialize context window manager.
        
        Args:
            max_tokens: Maximum tokens allowed in context
        """
        self.max_tokens = max_tokens
        self.total_tokens_used = 0
        self.request_count = 0
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Uses character-based estimation. For accurate counts,
        integrate with tiktoken or model-specific tokenizer.
        """
        return len(text) // self.CHARS_PER_TOKEN
    
    def count_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Count total tokens in message list."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.estimate_tokens(content)
            # Add overhead for role, tool_calls, etc.
            total += 10
        return total
    
    def track_usage(self, input_tokens: int, output_tokens: int):
        """Track token usage for a request."""
        self.total_tokens_used += input_tokens + output_tokens
        self.request_count += 1
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current token usage statistics."""
        return {
            "total_tokens": self.total_tokens_used,
            "request_count": self.request_count,
            "avg_tokens_per_request": (
                self.total_tokens_used // self.request_count 
                if self.request_count > 0 else 0
            )
        }
    
    def prune_context(
        self, 
        messages: List[Dict[str, Any]], 
        keep_system: bool = True,
        keep_recent: int = 10
    ) -> List[Dict[str, Any]]:
        """Prune old messages to fit within token limit.
        
        Args:
            messages: Full message list
            keep_system: Always keep system message
            keep_recent: Minimum recent messages to keep
            
        Returns:
            Pruned message list
        """
        if not messages:
            return messages
        
        current_tokens = self.count_message_tokens(messages)
        
        if current_tokens <= self.max_tokens:
            return messages
        
        # Separate system message if present
        system_msg = None
        other_msgs = []
        
        for msg in messages:
            if msg.get("role") == "system" and keep_system:
                system_msg = msg
            else:
                other_msgs.append(msg)
        
        # Keep only recent messages
        pruned = other_msgs[-keep_recent:] if len(other_msgs) > keep_recent else other_msgs
        
        # Add system message back
        if system_msg:
            pruned = [system_msg] + pruned
        
        return pruned
    
    def summarize_context(self, messages: List[Dict[str, Any]]) -> str:
        """Create a summary of old context for compression.
        
        This creates a structured summary that can be used as a 
        replacement for old messages.
        """
        summary_parts = []
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                # Truncate long user messages
                if len(content) > 200:
                    content = content[:200] + "..."
                summary_parts.append(f"User asked: {content}")
            
            elif role == "assistant":
                # Just note that assistant responded
                summary_parts.append("Assistant responded")
            
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                summary_parts.append(f"Tool '{tool_name}' was executed")
        
        return "Previous conversation summary:\n" + "\n".join(summary_parts[-10:])


class RetryHandler:
    """Handle retries with exponential backoff."""
    
    def __init__(
        self, 
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ):
        """Initialize retry handler.
        
        Args:
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (exponential backoff)."""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if we should retry based on attempt count and error type."""
        if attempt >= self.max_retries:
            return False
        
        # Retry on transient errors
        error_str = str(error).lower()
        transient_errors = [
            "timeout",
            "connection",
            "temporary",
            "rate limit",
            "unavailable",
            "overloaded"
        ]
        
        return any(err in error_str for err in transient_errors)
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if not self.should_retry(attempt, e):
                    raise
                
                delay = self.calculate_delay(attempt)
                time.sleep(delay)
        
        raise last_error

"""Service for chat functionality and AI interactions."""

import json
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.chat import ChatSession, ChatMessage, MessageRole, ConversationContext
from ..models.document import Document
from ..models.strategy import Strategy
from ..models.backtest import Backtest
from ..repositories.chat_repository import ChatRepository, ChatMessageRepository
from ..repositories.document_repository import DocumentRepository
from ..repositories.strategy_repository import StrategyRepository
from ..repositories.backtest_repository import BacktestRepository
from ..schemas.chat import ChatSessionCreate, ChatMessageCreate, ChatStreamChunk
from .llm_service import LLMService


logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations and AI interactions."""
    
    def __init__(
        self,
        chat_repo: ChatRepository,
        message_repo: ChatMessageRepository,
        llm_service: LLMService,
        document_repo: DocumentRepository,
        strategy_repo: StrategyRepository,
        backtest_repo: BacktestRepository
    ):
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.llm_service = llm_service
        self.document_repo = document_repo
        self.strategy_repo = strategy_repo
        self.backtest_repo = backtest_repo
    
    async def create_session(
        self,
        user_id: int,
        session_data: ChatSessionCreate
    ) -> ChatSession:
        """Create a new chat session."""
        logger.info(f"Creating chat session for user {user_id}: {session_data.title}")
        
        # Validate context if provided
        if session_data.context_id:
            await self._validate_context(
                user_id,
                session_data.context_type,
                session_data.context_id
            )
        
        session = await self.chat_repo.create_session(user_id, session_data)
        
        # Add initial system message with context
        system_prompt = await self._build_system_prompt(session)
        await self.message_repo.create_message(
            session_id=session.id,
            role=MessageRole.SYSTEM,
            content=system_prompt
        )
        
        return session
    
    async def send_message(
        self,
        session_id: int,
        user_id: int,
        message_data: ChatMessageCreate,
        stream: bool = False
    ) -> ChatMessage | AsyncGenerator[ChatStreamChunk, None]:
        """Send a message and get AI response."""
        # Verify session ownership
        session = await self.chat_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")
        
        # Save user message
        user_message = await self.message_repo.create_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=message_data.content,
            metadata=message_data.metadata
        )
        
        # Get conversation history
        messages = await self._build_conversation_history(session_id)
        
        if stream:
            return self._stream_response(session_id, messages)
        else:
            return await self._generate_response(session_id, messages)
    
    async def _generate_response(
        self,
        session_id: int,
        messages: List[Dict[str, str]]
    ) -> ChatMessage:
        """Generate a non-streaming AI response."""
        try:
            # Generate response
            response = await self.llm_service.generate(
                prompt=messages[-1]["content"],
                system_prompt=messages[0]["content"] if messages[0]["role"] == "system" else None,
                max_tokens=2000
            )
            
            # Extract token usage if available
            tokens_used = None
            if hasattr(response, "usage") and response.usage:
                tokens_used = response.usage.total_tokens
            
            # Save assistant message
            assistant_message = await self.message_repo.create_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response.content,
                tokens_used=tokens_used,
                model_name=self.llm_service.provider.model,
                metadata={"finish_reason": getattr(response, "stop_reason", None)}
            )
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            # Save error message
            error_message = await self.message_repo.create_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content="I apologize, but I encountered an error processing your request. Please try again.",
                metadata={"error": str(e)}
            )
            return error_message
    
    async def _stream_response(
        self,
        session_id: int,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Stream AI response chunks."""
        full_content = ""
        total_tokens = 0
        
        try:
            async for chunk in self.llm_service.stream_generate(
                prompt=messages[-1]["content"],
                system_prompt=messages[0]["content"] if messages[0]["role"] == "system" else None,
                max_tokens=2000
            ):
                full_content += chunk.content
                if hasattr(chunk, "usage") and chunk.usage:
                    total_tokens = chunk.usage.total_tokens
                
                yield ChatStreamChunk(
                    content=chunk.content,
                    is_final=False
                )
            
            # Save the complete message
            await self.message_repo.create_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=full_content,
                tokens_used=total_tokens if total_tokens > 0 else None,
                model_name=self.llm_service.provider.model
            )
            
            # Send final chunk
            yield ChatStreamChunk(
                content="",
                is_final=True,
                tokens_used=total_tokens if total_tokens > 0 else None
            )
            
        except Exception as e:
            logger.error(f"Error streaming AI response: {str(e)}")
            yield ChatStreamChunk(
                content="I apologize, but I encountered an error. Please try again.",
                is_final=True,
                metadata={"error": str(e)}
            )
    
    async def _build_system_prompt(self, session: ChatSession) -> str:
        """Build system prompt based on session context."""
        base_prompt = """You are an AI assistant specializing in quantitative finance and algorithmic trading strategies. 
You help users understand, develop, and refine trading strategies based on their documents and requirements.
Be concise, accurate, and provide actionable insights."""
        
        if session.context_type == ConversationContext.GENERAL:
            return base_prompt
        
        context_info = await self._get_context_info(
            session.user_id,
            session.context_type,
            session.context_id
        )
        
        if context_info:
            return f"{base_prompt}\n\nContext: {context_info}"
        
        return base_prompt
    
    async def _get_context_info(
        self,
        user_id: int,
        context_type: ConversationContext,
        context_id: int
    ) -> Optional[str]:
        """Get context information for the conversation."""
        try:
            if context_type == ConversationContext.DOCUMENT:
                document = await self.document_repo.get_user_document(context_id, user_id)
                if document:
                    return f"Document: {document.filename}\nContent: {document.extracted_text[:1000]}..."
            
            elif context_type == ConversationContext.STRATEGY:
                strategy = await self.strategy_repo.get_user_strategy(context_id, user_id)
                if strategy:
                    return f"Strategy: {strategy.name}\nDescription: {strategy.description}\nCode Preview: {strategy.code[:500]}..."
            
            elif context_type == ConversationContext.BACKTEST:
                backtest = await self.backtest_repo.get_by_id(context_id)
                if backtest and backtest.created_by_id == user_id:
                    return f"Backtest: {backtest.name}\nStrategy: {backtest.strategy.name}\nStatus: {backtest.status}"
            
        except Exception as e:
            logger.error(f"Error getting context info: {str(e)}")
        
        return None
    
    async def _validate_context(
        self,
        user_id: int,
        context_type: ConversationContext,
        context_id: int
    ) -> None:
        """Validate that the user has access to the context object."""
        if context_type == ConversationContext.DOCUMENT:
            document = await self.document_repo.get_user_document(context_id, user_id)
            if not document:
                raise ValueError("Document not found or access denied")
        
        elif context_type == ConversationContext.STRATEGY:
            strategy = await self.strategy_repo.get_user_strategy(context_id, user_id)
            if not strategy:
                raise ValueError("Strategy not found or access denied")
        
        elif context_type == ConversationContext.BACKTEST:
            backtest = await self.backtest_repo.get_by_id(context_id)
            if not backtest or backtest.created_by_id != user_id:
                raise ValueError("Backtest not found or access denied")
    
    async def _build_conversation_history(
        self,
        session_id: int,
        max_messages: int = 20
    ) -> List[Dict[str, str]]:
        """Build conversation history for LLM context."""
        messages = await self.message_repo.get_recent_messages(session_id, max_messages)
        
        history = []
        for message in messages:
            history.append({
                "role": message.role.value,
                "content": message.content
            })
        
        return history
    
    async def suggest_strategy_improvements(
        self,
        strategy_id: int,
        backtest_results: Dict[str, Any]
    ) -> str:
        """Suggest improvements for a strategy based on backtest results."""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError("Strategy not found")
        
        prompt = f"""Based on the following trading strategy and its backtest results, suggest specific improvements:

Strategy Name: {strategy.name}
Description: {strategy.description}
Code:
```python
{strategy.code}
```

Backtest Results:
- Total Return: {backtest_results.get('total_return', 'N/A')}%
- Sharpe Ratio: {backtest_results.get('sharpe_ratio', 'N/A')}
- Max Drawdown: {backtest_results.get('max_drawdown', 'N/A')}%
- Win Rate: {backtest_results.get('win_rate', 'N/A')}%

Please provide specific, actionable suggestions to improve the strategy's performance."""

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=1500
        )
        
        return response.content
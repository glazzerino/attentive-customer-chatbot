import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dotenv import dotenv_values
from app.models.tool import Tool


class LLMInterface(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, Any]], 
        context: str = "{}", 
        settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM
        
        Args:
            messages: List of message objects with role and content
            context: JSON string with context data
            settings: Optional dictionary with model settings
            
        Returns:
            Dictionary with response content and updated context
        """
        pass
    
    @abstractmethod
    async def execute_function_call(
        self, function_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a function call requested by the LLM
        
        Args:
            function_name: Name of the function to execute
            params: Parameters for the function
            
        Returns:
            Dictionary with result of the function execution
        """
        pass


class AnthropicClient(LLMInterface):
    """Implementation of LLMInterface for Anthropic Claude API"""
    
    def __init__(self):
        try:
            from anthropic import Anthropic
            self.anthropic = Anthropic
        except ImportError:
            raise ImportError("Please install the anthropic package: pip install anthropic")
            
        config = dotenv_values()
        self.api_key = config.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = self.anthropic(api_key=self.api_key)
        self.default_model = "claude-3-sonnet-20240229"
        self.default_max_tokens = 1000
    
    def _convert_messages_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert our internal message format to Anthropic's expected format"""
        anthropic_messages = []
        
        for msg in messages:
            # Handle content which could be string or dict with text/attachments
            content = msg["content"]
            role = "assistant" if msg["role"] == "assistant" else "user"
            
            anthropic_messages.append({
                "role": role,
                "content": content
            })
            
        return anthropic_messages
    
    def _prepare_tools_for_api(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert our Tool models to the format expected by Anthropic API"""
        api_tools = []
        
        for tool in tools:
            api_tool = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": tool.input_schema.type,
                    "properties": {},
                    "required": tool.required
                }
            }
            
            # Convert properties format
            for prop_name, prop_details in tool.input_schema.properties.items():
                api_tool["input_schema"]["properties"][prop_name] = {
                    "type": prop_details["type"].type,
                    "description": prop_details["type"].description
                }
            
            api_tools.append(api_tool)
            
        return api_tools

    async def generate_response(
        self, 
        messages: List[Dict[str, Any]], 
        context: str = "{}", 
        settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude
        
        Args:
            messages: List of message objects with role and content
            context: JSON string with context data
            settings: Optional settings dictionary with:
                - model: Model name to use (default: claude-3-sonnet-20240229)
                - max_tokens: Maximum tokens for response (default: 1000)
                - tools: List of Tool objects to make available
                - temperature: Sampling temperature (default: 0.7)
                - system_prompt: Optional system prompt to guide Claude
        
        Returns:
            Dictionary with response content and updated context
        """
        if not messages:
            return {
                "content": "I'm sorry, I couldn't understand your message.",
                "updated_context": json.loads(context) if context else {},
            }
        
        try:
            context_data = json.loads(context) if context else {}
        except json.JSONDecodeError:
            context_data = {}
        
        # Handle settings with defaults
        settings = settings or {}
        model = settings.get("model", self.default_model)
        max_tokens = settings.get("max_tokens", self.default_max_tokens)
        temperature = settings.get("temperature", 0.7)
        system_prompt = settings.get("system_prompt", "")
        tools = settings.get("tools", [])
        
        # Convert our message format to Anthropic's format
        anthropic_messages = self._convert_messages_format(messages)
        
        # Prepare API call parameters
        params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
            "temperature": temperature,
            "stream": False,  # Streaming not supported for WhatsApp
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt
            
        # Add tools if provided
        if tools:
            params["tools"] = self._prepare_tools_for_api(tools)
        
        try:
            # Make the API call
            response = self.client.messages.create(**params)
            
            # Extract tool calls if present
            tool_calls = []
            if hasattr(response, 'content') and isinstance(response.content, list):
                for content_block in response.content:
                    if content_block.type == 'tool_use':
                        tool_calls.append({
                            "name": content_block.name,
                            "parameters": content_block.input
                        })
            
            # Extract the text content
            text_content = ""
            if hasattr(response, 'content') and isinstance(response.content, list):
                for content_block in response.content:
                    if content_block.type == 'text':
                        text_content += content_block.text
            else:
                text_content = response.content
            
            return {
                "content": text_content,
                "updated_context": context_data,
                "tool_calls": tool_calls if tool_calls else None,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            # Log the error in a production environment
            print(f"Error calling Anthropic API: {str(e)}")
            return {
                "content": "I'm sorry, I encountered an error while processing your request.",
                "updated_context": context_data,
                "error": str(e)
            }

    async def execute_function_call(
        self, function_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function call requested by the LLM"""
        # This implementation should be provided by a service that knows how to execute specific tools
        return {"result": f"Function {function_name} not implemented yet"}


class MockLLMClient(LLMInterface):
    """Mock implementation of LLMInterface for testing and development"""
    
    async def generate_response(
        self, messages: List[Dict[str, Any]], context: str = "{}", settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate a mock response based on simple pattern matching"""
        try:
            context_data = json.loads(context) if context else {}
        except json.JSONDecodeError:
            context_data = {}

        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break

        if not last_user_message:
            return {
                "content": "I'm sorry, I couldn't understand your message.",
                "updated_context": context_data,
            }

        # Simple response logic for demonstration purposes
        if "hello" in last_user_message.lower() or "hi" in last_user_message.lower():
            return {
                "content": "Hello! Welcome to our WhatsApp shopping assistant. How can I help you today?",
                "updated_context": context_data,
            }
        elif (
            "product" in last_user_message.lower()
            or "shop" in last_user_message.lower()
        ):
            return {
                "content": "We have a variety of products available. What are you looking for today?",
                "updated_context": context_data,
            }
        elif "order" in last_user_message.lower():
            return {
                "content": "I can help you place an order. What would you like to purchase?",
                "updated_context": context_data,
            }
        else:
            return {
                "content": "I'm here to help you shop. You can ask about products, check your cart, or place an order.",
                "updated_context": context_data,
            }

    async def execute_function_call(
        self, function_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock execution of a function call"""
        return {"result": f"Mock execution of {function_name} with params {params}"}


# Factory function to create the appropriate LLM client
def create_llm_client(client_type: str = "anthropic") -> LLMInterface:
    """
    Factory function to create the appropriate LLM client
    
    Args:
        client_type: Type of LLM client to create (anthropic, mock)
        
    Returns:
        LLMInterface implementation
    """
    if client_type.lower() == "anthropic":
        return AnthropicClient()
    elif client_type.lower() == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"Unknown LLM client type: {client_type}")


# For backward compatibility - defaults to the mock client
LLMClient = MockLLMClient
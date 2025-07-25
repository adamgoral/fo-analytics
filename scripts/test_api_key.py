#!/usr/bin/env python3
"""
Test script to verify API key configuration
"""
import os
import sys
from pathlib import Path

# Add the backend src directory to Python path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from core.config import settings


def test_api_keys():
    """Test that API keys are properly configured"""
    print("Testing API Key Configuration")
    print("=" * 50)
    
    # Check Anthropic API Key
    if settings.anthropic_api_key:
        masked_key = settings.anthropic_api_key[:15] + "..." + settings.anthropic_api_key[-4:]
        print(f"✅ Anthropic API Key: {masked_key}")
    else:
        print("❌ Anthropic API Key: Not configured")
        print("   Please set ANTHROPIC_API_KEY in your .env file")
    
    # Check OpenAI API Key (optional)
    if settings.openai_api_key:
        masked_key = settings.openai_api_key[:7] + "..." + settings.openai_api_key[-4:]
        print(f"✅ OpenAI API Key: {masked_key}")
    else:
        print("ℹ️  OpenAI API Key: Not configured (optional)")
    
    # Check Google API Key (optional)
    if settings.google_api_key:
        masked_key = settings.google_api_key[:10] + "..." + settings.google_api_key[-4:]
        print(f"✅ Google API Key: {masked_key}")
    else:
        print("ℹ️  Google API Key: Not configured (optional)")
    
    print("\nLLM Configuration:")
    print(f"  Provider: {settings.llm_provider}")
    print(f"  Model: {settings.llm_model}")
    print(f"  Temperature: {settings.llm_temperature}")
    print(f"  Max Tokens: {settings.llm_max_tokens}")
    
    # Test that we can import the LLM service
    try:
        from services.llm.service import LLMService
        print("\n✅ LLM Service imports successfully")
        
        # Test initialization (but don't make actual API calls)
        if settings.anthropic_api_key and settings.llm_provider == "anthropic":
            service = LLMService()
            print("✅ LLM Service initialized successfully")
    except Exception as e:
        print(f"\n❌ Error importing/initializing LLM Service: {e}")
    
    print("\nEnvironment Variables Check:")
    print(f"  .env file exists: {Path('.env').exists()}")
    print(f"  Working directory: {os.getcwd()}")


if __name__ == "__main__":
    test_api_keys()
#!/usr/bin/env python3
"""
Test script to verify Google Gemini integration
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend src directory to Python path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

# Set environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from services.llm.service import LLMService
from core.config import settings


async def test_gemini():
    """Test Gemini API integration"""
    print("Testing Google Gemini Integration")
    print("=" * 50)
    
    # Check configuration
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"LLM Model: {settings.llm_model}")
    print(f"Google API Key: {'Configured' if settings.google_api_key else 'Not configured'}")
    
    if not settings.google_api_key:
        print("\n❌ Google API key not found. Please set GOOGLE_API_KEY in .env file")
        return
    
    if settings.llm_provider != "gemini":
        print(f"\n⚠️  LLM Provider is set to '{settings.llm_provider}', not 'gemini'")
        print("   Please set LLM_PROVIDER=gemini in .env file")
        return
    
    # Test the service
    try:
        print("\nInitializing LLM Service...")
        service = LLMService()
        print("✅ LLM Service initialized successfully")
        
        print("\nTesting simple generation...")
        result = await service.extract_strategy(
            "This is a test document. The investment strategy is to buy low and sell high."
        )
        
        print("✅ Generation successful!")
        print(f"\nExtracted strategies: {len(result.strategies)}")
        if result.strategies:
            print(f"First strategy: {result.strategies[0].name}")
            print(f"Description: {result.strategies[0].description[:100]}...")
        
        print(f"\nToken usage:")
        print(f"  Input tokens: {result.usage.get('input_tokens', 0)}")
        print(f"  Output tokens: {result.usage.get('output_tokens', 0)}")
        print(f"  Total tokens: {result.usage.get('total_tokens', 0)}")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_gemini())
#!/usr/bin/env python
"""
Test script for the document processing pipeline.

This script tests the complete flow:
1. Upload a document
2. Verify it's queued for processing
3. Monitor processing status
4. Retrieve extracted content

Usage:
    python scripts/test_document_pipeline.py
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
import structlog

# Configure logging
logger = structlog.get_logger()

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password123"
TEST_EMAIL = "test@example.com"


async def register_user(client: httpx.AsyncClient) -> Optional[str]:
    """Register a test user."""
    try:
        response = await client.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            }
        )
        if response.status_code == 201:
            logger.info("User registered successfully")
            return response.json()["access_token"]
        elif response.status_code == 400:
            # User might already exist, try to login
            logger.info("User already exists, attempting login")
            return await login_user(client)
        else:
            logger.error(f"Registration failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return None


async def login_user(client: httpx.AsyncClient) -> Optional[str]:
    """Login with test user."""
    try:
        response = await client.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
        )
        if response.status_code == 200:
            logger.info("Login successful")
            return response.json()["access_token"]
        else:
            logger.error(f"Login failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Login error: {e}")
        return None


async def create_test_document() -> Path:
    """Create a test document."""
    test_file = Path("/tmp/test_strategy.txt")
    test_content = """
Investment Strategy Document

Executive Summary:
This document outlines our comprehensive investment strategy for Q3 2025.

Strategy 1: Growth Equity Focus
- Target high-growth technology companies
- Focus on companies with 20%+ annual revenue growth
- Allocation: 40% of portfolio

Strategy 2: Fixed Income Diversification
- Invest in investment-grade corporate bonds
- Duration target: 3-5 years
- Allocation: 30% of portfolio

Strategy 3: Alternative Investments
- Include real estate investment trusts (REITs)
- Explore cryptocurrency exposure (5% max)
- Allocation: 20% of portfolio

Risk Management:
- Stop-loss orders at 10% drawdown
- Monthly portfolio rebalancing
- Quarterly performance reviews

Expected Returns:
- Target annual return: 12-15%
- Risk tolerance: Moderate
- Investment horizon: 5+ years
"""
    test_file.write_text(test_content)
    return test_file


async def upload_document(client: httpx.AsyncClient, token: str, file_path: Path) -> Optional[dict]:
    """Upload a document."""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/plain")}
            response = await client.post(
                f"{API_BASE_URL}/documents/upload",
                files=files,
                params={"document_type": "strategy_document"},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        if response.status_code == 201:
            logger.info("Document uploaded successfully")
            return response.json()
        else:
            logger.error(f"Upload failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return None


async def check_document_status(client: httpx.AsyncClient, token: str, document_id: int) -> Optional[dict]:
    """Check document processing status."""
    try:
        response = await client.get(
            f"{API_BASE_URL}/documents/{document_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Status check failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return None


async def get_document_content(client: httpx.AsyncClient, token: str, document_id: int) -> Optional[dict]:
    """Get extracted document content."""
    try:
        response = await client.get(
            f"{API_BASE_URL}/documents/{document_id}/content",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Content retrieval failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Content retrieval error: {e}")
        return None


async def main():
    """Run the document processing pipeline test."""
    logger.info("Starting document processing pipeline test")
    
    # Create test document
    test_file = await create_test_document()
    logger.info(f"Created test document: {test_file}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register/login
        token = await register_user(client)
        if not token:
            logger.error("Failed to authenticate")
            return
        
        # Upload document
        document = await upload_document(client, token, test_file)
        if not document:
            logger.error("Failed to upload document")
            return
        
        document_id = document["id"]
        logger.info(f"Document ID: {document_id}")
        
        # Monitor processing status
        max_attempts = 30  # 30 seconds timeout
        for attempt in range(max_attempts):
            status = await check_document_status(client, token, document_id)
            if not status:
                break
                
            logger.info(f"Status: {status['status']} (attempt {attempt + 1}/{max_attempts})")
            
            if status["status"] == "completed":
                logger.info("Document processing completed!")
                
                # Get extracted content
                content = await get_document_content(client, token, document_id)
                if content:
                    logger.info("=== Extracted Content ===")
                    logger.info(f"Text length: {len(content.get('content', ''))}")
                    
                    # Check if strategies were extracted
                    if "extracted_strategies" in status:
                        logger.info(f"Extracted strategies: {status['extracted_strategies']}")
                    
                    logger.info("=== Test Passed! ===")
                else:
                    logger.error("Failed to retrieve content")
                break
                
            elif status["status"] == "failed":
                logger.error(f"Processing failed: {status.get('processing_error', 'Unknown error')}")
                break
                
            # Wait before next check
            await asyncio.sleep(1)
        else:
            logger.error("Processing timeout - status did not change to completed")
    
    # Cleanup
    test_file.unlink()
    logger.info("Test completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
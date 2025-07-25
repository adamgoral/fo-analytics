# API Keys Setup Guide

## Overview

The Front Office Analytics platform uses AI services to extract investment strategies from documents. This guide explains how to set up the required API keys.

## Required API Keys

You need to configure at least one LLM provider. The platform supports:
- Google Gemini (recommended for cost-effectiveness)
- Anthropic Claude (best for complex analysis)
- OpenAI GPT-4 (widely used alternative)

### Google Gemini API Key (Recommended)

Google's Gemini models offer excellent performance at competitive pricing.

1. **Get an API Key**:
   - Go to https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the generated key

2. **Configure the Key**:
   - Copy `.env.example` to `.env` if you haven't already:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your API key:
     ```
     GOOGLE_API_KEY=your-google-api-key-here
     LLM_PROVIDER=gemini
     LLM_MODEL=gemini-pro
     ```

### Anthropic Claude API Key (Alternative)

Claude offers superior analysis capabilities for complex financial documents.

1. **Get an API Key**:
   - Sign up at https://console.anthropic.com/
   - Navigate to API Keys section
   - Create a new API key
   - Copy the key (it starts with `sk-ant-api03-`)

2. **Configure the Key**:
   - Edit `.env` and add your API key:
     ```
     ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
     LLM_PROVIDER=anthropic
     LLM_MODEL=claude-3-5-sonnet-20241022
     ```

3. **Verify Configuration**:
   - The worker service will use this key automatically
   - Check worker logs for successful initialization:
     ```bash
     docker-compose logs worker
     ```

### OpenAI GPT-4 API Key (Alternative)

OpenAI's GPT-4 models are widely used and well-documented.

1. **Get an API Key**:
   - Sign up at https://platform.openai.com/
   - Navigate to API Keys section
   - Create a new API key
   - Copy the key (it starts with `sk-`)

2. **Configure the Key**:
   - Edit `.env` and add your API key:
     ```
     OPENAI_API_KEY=sk-your-openai-key-here
     LLM_PROVIDER=openai
     LLM_MODEL=gpt-4-turbo-preview
     ```

## Docker Compose Configuration

If using Docker Compose, the environment variables are automatically loaded from `.env` file. No additional configuration needed.

## Kubernetes/Production Deployment

For production deployments:

1. **Use Kubernetes Secrets**:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: llm-api-keys
   type: Opaque
   data:
     ANTHROPIC_API_KEY: <base64-encoded-key>
   ```

2. **Reference in Deployment**:
   ```yaml
   env:
     - name: ANTHROPIC_API_KEY
       valueFrom:
         secretKeyRef:
           name: llm-api-keys
           key: ANTHROPIC_API_KEY
   ```

## Troubleshooting

### Worker Service Not Starting

If the worker service fails to start:

1. Check if API key is set:
   ```bash
   docker-compose exec worker printenv | grep ANTHROPIC_API_KEY
   ```

2. Check worker logs:
   ```bash
   docker-compose logs -f worker
   ```

3. Common issues:
   - API key not set in `.env`
   - Invalid API key format
   - API key expired or revoked

### Testing API Key

To test if your API key works:

1. Start the services:
   ```bash
   make dev
   ```

2. Upload a test document through the UI

3. Check worker logs for processing status:
   ```bash
   docker-compose logs -f worker
   ```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use different keys** for development and production
3. **Rotate keys regularly** (every 90 days recommended)
4. **Monitor usage** through provider dashboards
5. **Set spending limits** in provider consoles

## Cost Management

- Anthropic Claude API charges per token
- Monitor usage in the Anthropic console
- Consider implementing caching to reduce API calls
- Use the most cost-effective model for your needs

## Support

If you encounter issues:
1. Check the worker service logs
2. Verify API key format and validity
3. Ensure network connectivity to API endpoints
4. Contact support with error messages
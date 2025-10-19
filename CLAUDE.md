# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyChatGPT is a Python-based RAG (Retrieval-Augmented Generation) chatbot that combines document ingestion, vector search, and local LLM inference. The system allows users to upload documents, processes them into searchable chunks, and enables conversational interaction with the content using Ollama-hosted language models.

## Development Environment Setup

This project uses `uv` for Python package management and requires Python >=3.12.

**Initial setup:**
```bash
uv venv
source .venv/bin/activate
```

**Install dependencies:**
```bash
uv pip install markitdown sentence-transformers langchain-text-splitters chromadb gradio langchain-ollama ollama requests
pip install 'markitdown[pdf]'
```

Note: `markitdown[pdf]` requires separate installation with pip due to extra dependencies.

**Create required directories:**
```bash
mkdir -p documents processed_docs
```

## Architecture

The project follows a modular RAG pipeline architecture:

### Document Ingestion Pipeline (`src/injestion/`)
- **load_document.py**: Handles downloading and managing source documents
  - Uses `requests` to download files from URLs
  - Stores raw documents in `documents/` directory
  - Example implementation downloads "Think Python" guide for testing

### Data Flow
1. **Ingestion**: Documents downloaded to `documents/` folder
2. **Processing**: Documents converted to markdown using markitdown, then chunked using LangChain text splitters
3. **Embedding**: Text chunks converted to vectors using sentence-transformers
4. **Storage**: Vectors stored in ChromaDB for semantic search
5. **Retrieval**: User queries matched against vector store to find relevant chunks
6. **Generation**: Retrieved context fed to Ollama LLM for response generation
7. **Interface**: Gradio provides web-based chat UI

### Directory Structure
- `src/injestion/`: Document downloading and ingestion logic
- `documents/`: Raw source documents (PDFs, etc.)
- `processed_docs/`: Processed/chunked documents ready for embedding
- `test/`: Test files (currently empty)

## Running the Application

```bash
python main.py
```

**Current state**: The application is in early development. The main.py currently contains only a placeholder print statement. Document downloading functionality exists in `src/injestion/load_document.py`.

## Key Dependencies

- **markitdown[pdf]**: Converts documents (including PDFs) to markdown format
- **sentence-transformers**: Generates dense embeddings for semantic search
- **langchain-text-splitters**: Chunks documents for optimal RAG performance
- **chromadb**: Vector database for storing and querying embeddings
- **gradio**: Web UI framework for chat interface
- **langchain-ollama & ollama**: Integration with locally-hosted LLMs
- **requests**: HTTP library for downloading documents

## Development Notes

- The project uses `pyproject.toml` for package configuration
- Git repository is initialized (main branch)
- Virtual environment managed by uv at `.venv/`
- Code in `src/injestion/load_document.py` contains a duplicate `download_file` function definition that should be cleaned up
# Install project: 
```
mkdir MyChatGPT && cd MyChatGPT 
uv init
uv venv
source .venv/bin/activate
uv pip install markitdown[pdf] sentence-transformers langchain-text-splitters chromadb gradio langchain-ollama ollama
uv pip install sentence-transformers langchain-text-splitters chromadb gradio langchain-ollama ollama
pip install 'markitdown[pdf]'
```

#Setup GitHub
```
> /install-github-app 
╭─────────────────────────────────────────────────────────────────────────╮
│ ⚠ Setup Warnings                                                        │
│ We found some potential issues, but you can continue anyway             │
│                                                                         │
│ GitHub CLI not authenticated                                            │
│ GitHub CLI does not appear to be authenticated.                         │
│                                                                         │
│   • Run: gh auth login                                                  │
│   • Follow the prompts to authenticate with GitHub                      │
│   • Or set up authentication using environment variables or other       │
│   methods                                                               |               
--------------------------------------------------------------------------
```

# Create directories for storing documents
`mkdir processed_docs documents`

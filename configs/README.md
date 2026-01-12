# PWA-CLI Configuration Files

This directory contains configuration files for PWA-CLI. These files contain sensitive information (API keys, tokens) and should **NOT** be committed to Git.

## Setup Instructions

1. Copy the example files to create your actual configuration files:

```bash
cd configs/
cp OCR_API.yaml.example OCR_API.yaml
cp RAGFlow.yaml.example RAGFlow.yaml
cp llm_config.yaml.example llm_config.yaml
cp zotero_config.yaml.example zotero_config.yaml
```

2. Edit each file and fill in your actual credentials:

```bash
# Edit with your favorite editor
nano OCR_API.yaml
nano RAGFlow.yaml
nano llm_config.yaml
nano zotero_config.yaml
```

## Configuration Files

### OCR_API.yaml

Configuration for Mineru OCR API (used for full-text extraction).

**Required fields:**
- `token`: Your Mineru API token from https://open.pdf2file.com/

**How to get:**
1. Visit https://open.pdf2file.com/
2. Sign up for an account
3. Get your API token from the dashboard

---

### RAGFlow.yaml

Configuration for RAGFlow (used for statement verification).

**Required fields:**
- `api_key`: Your RAGFlow API key
- `base_url`: Your RAGFlow instance URL

**How to get:**
1. Deploy or access a RAGFlow instance
2. Get your API key from the dashboard

---

### llm_config.yaml

Configuration for Large Language Models.

**Required fields:**
- `openai.api_key`: Your OpenAI API key
- `openai.model`: Model to use (e.g., "gpt-4", "gpt-3.5-turbo")

**How to get:**
1. Visit https://platform.openai.com/
2. Sign up for an account
3. Generate an API key from the API keys page

**Alternative providers:**
- Anthropic Claude
- Azure OpenAI
- Local LLM (Ollama)

---

### zotero_config.yaml

Configuration for Zotero (used for reference management).

**Required fields:**
- `library_id`: Your Zotero library ID
- `library_type`: "user" or "group"
- `api_key`: Your Zotero API key

**How to get:**
1. Visit https://www.zotero.org/settings/keys
2. Create a new API key
3. Find your library ID in your Zotero account settings

---

## Security Notes

⚠️ **IMPORTANT**: Never commit actual configuration files to Git!

- ✅ `*.yaml.example` files are safe to commit (no sensitive data)
- ❌ `*.yaml` files should NEVER be committed (contain secrets)
- ✅ `.gitignore` is configured to ignore `*.yaml` files

## Troubleshooting

### Configuration file not found

If you see errors like "Configuration file not found", make sure you've:

1. Copied the example files to actual config files
2. Filled in your actual credentials
3. The files are in the correct location (`configs/` directory)

### Invalid credentials

If you see authentication errors:

1. Double-check your API keys/tokens
2. Make sure there are no extra spaces or quotes
3. Verify the keys are still valid (not expired or revoked)

### Permission errors

Make sure the configuration files have appropriate permissions:

```bash
chmod 600 configs/*.yaml
```

This ensures only you can read/write the files.

---

For more help, see the main documentation or open an issue on GitHub.

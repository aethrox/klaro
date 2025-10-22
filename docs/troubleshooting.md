# Klaro Troubleshooting Guide

This guide provides solutions to common issues encountered when installing, configuring, and running Klaro.

## Installation Issues

### Error: "Python version not supported"

**Error Message:**
```
ERROR: This package requires Python 3.11 or higher
```

**Cause:**
You're using an older version of Python that doesn't support the type hints and features used in Klaro.

**Solution:**
1. Check your Python version:
   ```bash
   python --version
   ```

2. Install Python 3.11 or higher from [python.org](https://python.org)

3. Recreate your virtual environment:
   ```bash
   python3.11 -m venv klaro-env
   source klaro-env/bin/activate  # or klaro-env\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

---

### Error: "pip install failed - no matching distribution"

**Error Message:**
```
ERROR: Could not find a version that satisfies the requirement langchain==X.Y.Z
```

**Cause:**
Package repository connectivity issues or outdated pip version.

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Retry installation
pip install -r requirements.txt

# If still failing, try with verbose output
pip install -r requirements.txt -v
```

---

## Configuration Issues

### Error: "OpenAI API key not found"

**Error Message:**
```
openai.error.AuthenticationError: No API key provided
```

**Cause:**
The `OPENAI_API_KEY` environment variable is not set or `.env` file is not loaded.

**Solution:**

1. **Verify `.env` file exists:**
   ```bash
   ls -la .env
   ```

2. **Check `.env` content:**
   ```bash
   cat .env
   ```
   Should contain:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```

3. **Test API key validity:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(f"API Key loaded: {os.getenv('OPENAI_API_KEY')[:10]}...")
   ```

4. **Common mistakes:**
   - Extra spaces: `OPENAI_API_KEY = sk-...` (should be `OPENAI_API_KEY=sk-...`)
   - Wrong quotes: `OPENAI_API_KEY='sk-...'` (should be no quotes)
   - Expired key: Get new key from https://platform.openai.com/api-keys

---

### Error: "Invalid API key format"

**Error Message:**
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Cause:**
API key is malformed or has been regenerated/deleted in OpenAI dashboard.

**Solution:**

1. **Verify key format** - Should start with `sk-proj-` (new format) or `sk-` (legacy):
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Generate new key:**
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the entire key (you won't be able to see it again!)
   - Update `.env` file

3. **Test with curl:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

---

## Runtime Issues

### Error: "ChromaDB initialization failed"

**Error Message:**
```
Error initializing knowledge base: [Errno 13] Permission denied: './klaro_db'
```

**Cause:**
Permission issues with the vector database directory or corrupted database files.

**Solution:**

1. **Delete and recreate database:**
   ```bash
   rm -rf ./klaro_db
   python main.py
   ```

2. **Check directory permissions:**
   ```bash
   ls -ld ./klaro_db
   chmod 755 ./klaro_db  # if needed
   ```

3. **Alternative: Use different directory:**
   Edit `tools.py` line 96:
   ```python
   VECTOR_DB_PATH = "/path/to/writable/directory/klaro_db"
   ```

---

### Error: "File read permission errors"

**Error Message:**
```
Error reading file: [Errno 13] Permission denied: '/path/to/file.py'
```

**Cause:**
Klaro doesn't have read permissions for the target project directory.

**Solution:**

1. **Check file permissions:**
   ```bash
   ls -l /path/to/file.py
   ```

2. **Grant read access:**
   ```bash
   chmod +r /path/to/file.py
   ```

3. **For entire directory:**
   ```bash
   chmod -R +r /path/to/project
   ```

4. **Run as appropriate user:**
   - Avoid running with `sudo` (security risk)
   - Ensure current user owns the project files

---

### Error: "Invalid code analysis - syntax error"

**Error Message:**
```
{"error": "Code parsing error (SyntaxError): invalid syntax"}
```

**Cause:**
The analyzed Python file contains syntax errors or uses unsupported Python version features.

**Solution:**

1. **Verify Python file syntax:**
   ```bash
   python -m py_compile /path/to/file.py
   ```

2. **Check Python version compatibility:**
   - Klaro uses Python 3.11+ AST parser
   - Older syntax (Python 2.x) will fail
   - Very new syntax (Python 3.13+) might fail

3. **Skip problematic files:**
   Add to `.gitignore` or GITIGNORE_CONTENT in `tools.py`:
   ```
   path/to/problematic_file.py
   ```

---

### Error: "Network errors in web_search"

**Error Message:**
```
Search result found for 'X': (Example Answer: The requested information is here.)
```

**Cause:**
`web_search` is currently a simulation (mock implementation).

**Solution:**

This is expected behavior. The `web_search` tool returns placeholder results. To integrate real search:

1. **Option A: DuckDuckGo (Free)**
   ```bash
   pip install duckduckgo-search
   ```
   Update `tools.py`:
   ```python
   from duckduckgo_search import DDGS

   def web_search(query: str) -> str:
       try:
           with DDGS() as ddgs:
               results = list(ddgs.text(query, max_results=3))
               return "\n".join([r['body'] for r in results])
       except Exception as e:
           return f"Search error: {e}"
   ```

2. **Option B: SerpAPI (Paid, Reliable)**
   - Sign up at https://serpapi.com
   - Install: `pip install google-search-results`
   - See SerpAPI documentation for integration

---

### Error: "Recursion limit exceeded"

**Error Message:**
```
RecursionError: Maximum recursion limit (50) reached
```

**Cause:**
Project is too large or complex for the default iteration limit, or agent is stuck in a loop.

**Solution:**

1. **Increase recursion limit:**
   ```bash
   export KLARO_RECURSION_LIMIT=100
   python main.py
   ```

   Or in `.env`:
   ```
   KLARO_RECURSION_LIMIT=100
   ```

2. **For very large projects (50+ files):**
   ```
   KLARO_RECURSION_LIMIT=200
   ```

3. **Check for infinite loops:**
   - Enable LangSmith tracing to debug:
     ```
     LANGSMITH_TRACING=true
     LANGSMITH_API_KEY=your-key
     ```
   - Check if agent is repeatedly calling the same tool with same parameters
   - This indicates a bug in the agent logic or prompts

---

### Error: "Memory issues with large codebases"

**Symptoms:**
- Process killed by OS
- Extremely slow execution
- `MemoryError` exceptions

**Cause:**
Large files or many files exceed available RAM.

**Solution:**

1. **Exclude large files** - Add to GITIGNORE_CONTENT in `tools.py`:
   ```python
   # Exclude large generated files
   dist/
   build/
   *.min.js
   *.bundle.js
   ```

2. **Process in batches** - Modify agent prompt to analyze fewer files per iteration

3. **Use lighter LLM model:**
   ```python
   LLM_MODEL = "gpt-4o-mini"  # Less memory usage than gpt-4o
   ```

4. **Increase system memory:**
   - Close other applications
   - Use a machine with more RAM
   - Consider cloud execution (AWS, GCP)

---

## LangSmith Tracing Issues

### Error: "LangSmith connection failed"

**Error Message:**
```
Warning: LangSmith tracing enabled but connection failed
```

**Cause:**
Invalid LangSmith API key or network connectivity issues.

**Solution:**

1. **Verify LangSmith setup:**
   ```bash
   echo $LANGSMITH_API_KEY
   echo $LANGSMITH_PROJECT
   ```

2. **Get LangSmith API key:**
   - Sign up at https://smith.langchain.com
   - Go to Settings → API Keys
   - Create new key

3. **Test connection:**
   ```python
   from langsmith import Client
   client = Client(api_key="your-key")
   print(client.list_projects())
   ```

4. **Disable if not needed:**
   ```
   LANGSMITH_TRACING=false
   ```

---

## Getting Additional Help

If your issue isn't covered here:

1. **Check GitHub Issues:** https://github.com/aethrox/klaro/issues
2. **Enable Debug Logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Provide Details When Reporting:**
   - Python version: `python --version`
   - Klaro version: `git rev-parse HEAD`
   - Error message (full traceback)
   - Steps to reproduce
   - Operating system

4. **Example Bug Report Template:**
   ```markdown
   **Environment:**
   - OS: Ubuntu 22.04
   - Python: 3.11.5
   - Klaro commit: abc123

   **Issue:**
   ChromaDB initialization fails with permission error

   **Steps to Reproduce:**
   1. Clone repository
   2. Run `python main.py`
   3. Error occurs

   **Error Output:**
   ```
   [paste full error here]
   ```
   ```

---

## Performance Optimization Tips

### Slow Execution

**Problem:** Agent takes too long to complete.

**Solutions:**

1. **Use faster model:**
   ```python
   LLM_MODEL = "gpt-4o-mini"  # 5-10x faster than gpt-4o
   ```

2. **Reduce file count:**
   - Add unnecessary directories to `.gitignore`
   - Focus on critical files only

3. **Disable LangSmith tracing:**
   ```
   LANGSMITH_TRACING=false
   ```

4. **Use SSD storage for ChromaDB:**
   - Move `./klaro_db` to SSD
   - Update `VECTOR_DB_PATH` in `tools.py`

---

### High API Costs

**Problem:** OpenAI API costs are too high.

**Solutions:**

1. **Use cost-effective model:**
   ```python
   LLM_MODEL = "gpt-4o-mini"  # ~$0.10-0.40 per run
   ```

2. **Cache results:**
   - Don't re-run on same project repeatedly
   - Save outputs for reuse

3. **Monitor usage:**
   - Check OpenAI dashboard: https://platform.openai.com/usage
   - Set usage limits to prevent surprises

4. **Alternative: Use local LLMs (Advanced):**
   - Install Ollama: https://ollama.ai
   - Use open-source models (llama2, mistral)
   - Requires more technical setup

---

## Debugging Checklist

Before reporting issues, try this checklist:

- [ ] Python version is 3.11 or higher
- [ ] Virtual environment is activated
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file exists with valid `OPENAI_API_KEY`
- [ ] API key tested with curl/manual request
- [ ] `./klaro_db` directory has write permissions
- [ ] Target project directory has read permissions
- [ ] Recursion limit appropriate for project size
- [ ] Latest code pulled: `git pull origin main`
- [ ] No proxy/firewall blocking OpenAI API

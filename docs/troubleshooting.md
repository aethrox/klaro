# Troubleshooting Guide

This guide provides solutions for common errors and issues you may encounter when using Klaro.

## Table of Contents
- [OpenAI API Key Errors](#openai-api-key-errors)
- [ChromaDB Initialization Failures](#chromadb-initialization-failures)
- [File Read Permission Errors](#file-read-permission-errors)
- [Invalid Code Analysis Errors](#invalid-code-analysis-errors)
- [Network Errors in web_search](#network-errors-in-web_search)
- [LangGraph Recursion Limit Exceeded](#langgraph-recursion-limit-exceeded)
- [Memory Issues with Large Codebases](#memory-issues-with-large-codebases)

---

## OpenAI API Key Errors

### Error 1: Missing API Key

**Error Message:**
```
openai.error.AuthenticationError: No API key provided.
```

**What Causes It:**
- `.env` file is missing or not loaded
- `OPENAI_API_KEY` environment variable is not set
- `.env` file is in the wrong directory

**How to Fix:**

1. **Verify `.env` file exists:**
   ```bash
   ls -la .env
   ```

2. **Check `.env` contents:**
   ```bash
   cat .env
   ```
   Should contain:
   ```
   OPENAI_API_KEY=sk-...
   ```

3. **Create `.env` from template:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your API key.

4. **Verify environment variable is loaded:**
   ```python
   # test_env.py
   import os
   from dotenv import load_dotenv

   load_dotenv()
   api_key = os.getenv("OPENAI_API_KEY")

   if api_key:
       print(f"✓ API key loaded: {api_key[:10]}...")
   else:
       print("✗ API key not found!")
   ```

**Example Solution:**
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env

# Test
python main.py
```

---

### Error 2: Invalid API Key

**Error Message:**
```
openai.error.AuthenticationError: Incorrect API key provided: sk-xxxxx
```

**What Causes It:**
- API key is malformed or incomplete
- API key has been revoked
- Copy-paste error (extra spaces, missing characters)

**How to Fix:**

1. **Validate API key format:**
   - Should start with `sk-`
   - Should be 51+ characters long
   - No spaces or newlines

2. **Test API key directly:**
   ```python
   # test_api_key.py
   import openai
   import os
   from dotenv import load_dotenv

   load_dotenv()
   openai.api_key = os.getenv("OPENAI_API_KEY")

   try:
       response = openai.models.list()
       print("✓ API key is valid!")
       print(f"Available models: {len(response.data)}")
   except openai.error.AuthenticationError as e:
       print(f"✗ API key is invalid: {e}")
   ```

3. **Generate new API key:**
   - Visit https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key immediately (it won't be shown again)
   - Update `.env` file

**Example Solution:**
```bash
# Remove old key and add new one
sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=sk-new-key-here/' .env

# Verify
python test_api_key.py
```

---

### Error 3: API Rate Limit Exceeded

**Error Message:**
```
openai.error.RateLimitError: Rate limit exceeded. Please try again later.
```

**What Causes It:**
- Too many requests in short time period
- Free tier quota exceeded
- Concurrent requests exceeding limit

**How to Fix:**

1. **Check API usage:**
   - Visit https://platform.openai.com/usage
   - Check current rate limits
   - Verify billing status

2. **Add retry logic:**
   ```python
   # Add to main.py
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=4, max=60)
   )
   def call_llm_with_retry():
       # Your LLM call here
       pass
   ```

3. **Reduce request frequency:**
   ```python
   import time

   # Add delay between tool calls
   time.sleep(1)  # Wait 1 second between requests
   ```

**Example Solution:**
```bash
# Wait 60 seconds and retry
sleep 60
python main.py
```

---

## ChromaDB Initialization Failures

### Error 1: Permission Denied

**Error Message:**
```
PermissionError: [Errno 13] Permission denied: './klaro_db'
```

**What Causes It:**
- No write permissions in current directory
- `klaro_db` directory owned by different user
- Running in read-only filesystem

**How to Fix:**

1. **Check directory permissions:**
   ```bash
   ls -ld klaro_db
   ```

2. **Fix permissions:**
   ```bash
   sudo chown -R $USER:$USER klaro_db
   chmod -R 755 klaro_db
   ```

3. **Use alternative location:**
   ```python
   # Edit tools.py
   KLARO_DB_PATH = os.path.expanduser("~/klaro_db")  # Use home directory
   ```

**Example Solution:**
```bash
# Remove and recreate
rm -rf klaro_db
python main.py  # Will recreate automatically
```

---

### Error 2: ChromaDB Lock Error

**Error Message:**
```
sqlite3.OperationalError: database is locked
```

**What Causes It:**
- Multiple Klaro instances running simultaneously
- Previous instance crashed without releasing lock
- Antivirus software scanning database

**How to Fix:**

1. **Check for running instances:**
   ```bash
   # Linux/Mac
   ps aux | grep main.py

   # Windows
   tasklist | findstr python
   ```

2. **Kill existing processes:**
   ```bash
   # Linux/Mac
   pkill -f main.py

   # Windows
   taskkill /F /IM python.exe
   ```

3. **Remove lock file:**
   ```bash
   rm klaro_db/*.lock
   ```

**Example Solution:**
```bash
# Complete cleanup
pkill -f main.py
rm -rf klaro_db
python main.py
```

---

### Error 3: ChromaDB Version Mismatch

**Error Message:**
```
ValueError: ChromaDB version mismatch. Expected 0.4.x, got 0.3.x
```

**What Causes It:**
- Old ChromaDB installation
- Cached database from older version
- Incompatible requirements.txt

**How to Fix:**

1. **Upgrade ChromaDB:**
   ```bash
   pip install --upgrade chromadb
   ```

2. **Clear old database:**
   ```bash
   rm -rf klaro_db
   ```

3. **Verify installation:**
   ```python
   import chromadb
   print(chromadb.__version__)  # Should be 0.4.x or higher
   ```

**Example Solution:**
```bash
pip install --upgrade chromadb
rm -rf klaro_db
python main.py
```

---

## File Read Permission Errors

### Error 1: Permission Denied Reading File

**Error Message:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file.py'
```

**What Causes It:**
- File has restrictive permissions (e.g., 600)
- File owned by different user
- File in protected system directory

**How to Fix:**

1. **Check file permissions:**
   ```bash
   ls -l /path/to/file.py
   ```

2. **Make file readable:**
   ```bash
   chmod +r /path/to/file.py
   ```

3. **Run with appropriate user:**
   ```bash
   sudo -u file-owner python main.py
   ```

**Example Solution:**
```bash
# Fix permissions for entire project
chmod -R +r /path/to/project
python main.py /path/to/project
```

---

### Error 2: File Not Found

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'main.py'
```

**What Causes It:**
- Wrong working directory
- File was moved or deleted
- Typo in file path

**How to Fix:**

1. **Verify current directory:**
   ```bash
   pwd
   ls -la
   ```

2. **Use absolute paths:**
   ```bash
   python main.py /absolute/path/to/project
   ```

3. **Check file exists:**
   ```bash
   find . -name "main.py"
   ```

**Example Solution:**
```bash
# Navigate to correct directory
cd /path/to/project
python /path/to/klaro/main.py .
```

---

### Error 3: Unicode Decode Error

**Error Message:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```

**What Causes It:**
- File is not UTF-8 encoded
- Binary file being read as text
- File contains invalid characters

**How to Fix:**

1. **Identify file encoding:**
   ```bash
   file /path/to/file.py
   chardet /path/to/file.py  # Install: pip install chardet
   ```

2. **Convert to UTF-8:**
   ```bash
   iconv -f ISO-8859-1 -t UTF-8 file.py > file_utf8.py
   ```

3. **Add fallback encoding in tools.py:**
   ```python
   # Modify read_file function
   try:
       with open(file_path, 'r', encoding='utf-8') as f:
           return f.read()
   except UnicodeDecodeError:
       with open(file_path, 'r', encoding='latin-1') as f:
           return f.read()
   ```

**Example Solution:**
```bash
# Convert all Python files to UTF-8
find . -name "*.py" -exec dos2unix {} \;
python main.py
```

---

## Invalid Code Analysis Errors

### Error 1: Syntax Error in Python File

**Error Message:**
```
SyntaxError: invalid syntax (file.py, line 42)
```

**What Causes It:**
- File contains Python 2 syntax (Python 3 project)
- Incomplete or malformed code
- Code under development with syntax errors

**How to Fix:**

1. **Validate syntax manually:**
   ```bash
   python -m py_compile /path/to/file.py
   ```

2. **Skip problematic files:**
   ```python
   # Add to tools.py analyze_code function
   try:
       tree = ast.parse(code_content)
   except SyntaxError as e:
       return json.dumps({
           "error": f"Syntax error: {str(e)}",
           "classes": [],
           "functions": []
       })
   ```

3. **Fix syntax errors:**
   ```bash
   # Use autopep8 to auto-fix
   pip install autopep8
   autopep8 --in-place --aggressive file.py
   ```

**Example Solution:**
```bash
# Check all Python files
find . -name "*.py" -exec python -m py_compile {} \;

# Fix auto-fixable issues
autopep8 --in-place --aggressive --recursive .
```

---

### Error 2: Empty or Invalid AST

**Error Message:**
```
ValueError: AST tree is empty or invalid
```

**What Causes It:**
- Empty Python file
- File contains only comments
- File is not actually Python code

**How to Fix:**

1. **Check file content:**
   ```bash
   cat file.py
   wc -l file.py
   ```

2. **Add validation in tools.py:**
   ```python
   def analyze_code(code_content: str):
       if not code_content or code_content.isspace():
           return json.dumps({
               "error": "Empty file",
               "classes": [],
               "functions": []
           })
       # Continue with analysis...
   ```

**Example Solution:**
```python
# Skip empty files in list_files output
# Klaro should handle gracefully
```

---

### Error 3: Module Import Errors During Analysis

**Error Message:**
```
ImportError: No module named 'custom_module'
```

**What Causes It:**
- Code analysis trying to execute imports
- Missing dependencies
- Relative imports not resolved

**How to Fix:**

1. **Install missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Use AST-only analysis (no execution):**
   ```python
   # AST parsing does not execute code
   # This error should not occur with pure AST analysis
   # If it does, check for eval() or exec() in tools.py
   ```

**Example Solution:**
```bash
# Ensure clean AST-only parsing
# Review tools.py analyze_code function
# Should ONLY use ast.parse(), not importlib or exec()
```

---

## Network Errors in web_search

### Error 1: Connection Timeout

**Error Message:**
```
requests.exceptions.ConnectTimeout: Connection to API timed out
```

**What Causes It:**
- Slow or unstable internet connection
- Firewall blocking requests
- API endpoint is down

**How to Fix:**

1. **Test internet connectivity:**
   ```bash
   ping google.com
   curl https://api.openai.com
   ```

2. **Increase timeout in tools.py:**
   ```python
   import requests

   def web_search(query: str):
       try:
           response = requests.get(
               url,
               timeout=30  # Increase from default
           )
       except requests.exceptions.Timeout:
           return "Search timed out. Please try again."
   ```

3. **Use proxy if needed:**
   ```bash
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=https://proxy.example.com:8080
   python main.py
   ```

**Example Solution:**
```bash
# Test network
ping -c 4 google.com

# If behind proxy
export HTTP_PROXY=http://proxy:8080
python main.py
```

---

### Error 2: DNS Resolution Failure

**Error Message:**
```
requests.exceptions.ConnectionError: Failed to resolve hostname
```

**What Causes It:**
- DNS server issues
- Incorrect hostname
- Network configuration problems

**How to Fix:**

1. **Test DNS:**
   ```bash
   nslookup api.openai.com
   dig api.openai.com
   ```

2. **Use alternative DNS:**
   ```bash
   # Linux/Mac: Edit /etc/resolv.conf
   nameserver 8.8.8.8
   nameserver 8.8.4.4
   ```

3. **Use IP address directly (if applicable):**
   ```python
   # Not recommended for APIs with SSL
   ```

**Example Solution:**
```bash
# Flush DNS cache
# Linux
sudo systemd-resolve --flush-caches

# Mac
sudo dscacheutil -flushcache

# Windows
ipconfig /flushdns
```

---

### Error 3: SSL Certificate Verification Failed

**Error Message:**
```
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**What Causes It:**
- Outdated CA certificates
- Corporate proxy with SSL inspection
- System time is incorrect

**How to Fix:**

1. **Update certificates:**
   ```bash
   # Linux
   sudo apt-get update && sudo apt-get install --reinstall ca-certificates

   # Mac
   pip install --upgrade certifi
   ```

2. **Check system time:**
   ```bash
   date
   # Ensure time is correct
   ```

3. **Temporary workaround (NOT recommended for production):**
   ```python
   # In tools.py (only for debugging)
   response = requests.get(url, verify=False)
   ```

**Example Solution:**
```bash
pip install --upgrade certifi
python main.py
```

---

## LangGraph Recursion Limit Exceeded

### Error 1: Maximum Iterations Reached

**Error Message:**
```
RecursionError: Maximum recursion depth exceeded (limit: 50)
```

**What Causes It:**
- Agent is stuck in a loop
- Complex project requires more iterations
- Agent keeps retrying failed operations

**How to Fix:**

1. **Increase recursion limit:**
   ```bash
   # Add to .env
   KLARO_RECURSION_LIMIT=100
   ```

2. **Check agent logs for loops:**
   ```
   Iteration 45: list_files
   Iteration 46: list_files  # Same action repeated!
   Iteration 47: list_files  # Agent is stuck
   ```

3. **Enable LangSmith tracing to debug:**
   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=your-key
   python main.py
   ```

4. **Simplify project structure:**
   ```bash
   # Analyze smaller subdirectories
   python main.py ./src
   ```

**Example Solution:**
```bash
# Increase limit
echo "KLARO_RECURSION_LIMIT=150" >> .env

# Or analyze in parts
python main.py ./src > src_docs.md
python main.py ./tests > tests_docs.md
```

---

### Error 2: Infinite Loop Detection

**Error Message:**
```
Warning: Detected repeated action. Possible infinite loop.
```

**What Causes It:**
- Agent keeps calling same tool with same parameters
- No progress towards "Final Answer"
- Bug in prompt or tool logic

**How to Fix:**

1. **Review LangSmith trace:**
   - Identify which tool is being repeated
   - Check tool output - is it helpful?
   - Verify agent is using tool results

2. **Improve tool descriptions in tools.py:**
   ```python
   @tool
   def list_files(directory: str) -> str:
       """
       List files in directory. **Call this only ONCE per directory.**
       Returns complete file tree structure.
       """
   ```

3. **Add loop detection in main.py:**
   ```python
   from collections import Counter

   def detect_loop(messages, window=5):
       recent_tools = [
           msg.tool_calls[0]['name']
           for msg in messages[-window:]
           if hasattr(msg, 'tool_calls') and msg.tool_calls
       ]
       if len(set(recent_tools)) == 1 and len(recent_tools) == window:
           raise ValueError("Loop detected: same tool called 5 times in a row")
   ```

**Example Solution:**
```python
# Add to main.py run_model function
if len(state['messages']) > 10:
    recent_actions = [m.tool_calls for m in state['messages'][-5:] if hasattr(m, 'tool_calls')]
    # Check for loops and break if detected
```

---

## Memory Issues with Large Codebases

### Error 1: Out of Memory

**Error Message:**
```
MemoryError: Unable to allocate memory
```

**What Causes It:**
- Processing very large files (>10MB)
- Too many files loaded simultaneously
- Large ChromaDB database in memory

**How to Fix:**

1. **Process in batches:**
   ```bash
   # Analyze subdirectories separately
   for dir in src tests docs; do
       python main.py ./$dir > ${dir}_docs.md
   done
   ```

2. **Exclude large files:**
   ```python
   # Add to tools.py list_files
   MAX_FILE_SIZE = 1_000_000  # 1MB

   if os.path.getsize(file_path) > MAX_FILE_SIZE:
       continue  # Skip large files
   ```

3. **Use streaming for ChromaDB:**
   ```python
   # In tools.py init_knowledge_base
   collection.add(
       documents=documents[:1000],  # Process in chunks
       # ...
   )
   ```

**Example Solution:**
```bash
# Analyze with memory limit (Linux)
ulimit -v 2000000  # 2GB limit
python main.py
```

---

### Error 2: ChromaDB Database Too Large

**Error Message:**
```
OSError: [Errno 28] No space left on device
```

**What Causes It:**
- ChromaDB database growing too large
- Many document chunks
- Disk space exhausted

**How to Fix:**

1. **Check database size:**
   ```bash
   du -sh klaro_db
   ```

2. **Clear and reinitialize:**
   ```bash
   rm -rf klaro_db
   python main.py
   ```

3. **Reduce chunk size:**
   ```python
   # In tools.py
   text_splitter = RecursiveCharacterTextSplitter(
       chunk_size=500,  # Reduce from 1000
       chunk_overlap=100  # Reduce from 200
   )
   ```

4. **Check disk space:**
   ```bash
   df -h
   ```

**Example Solution:**
```bash
# Free up space
rm -rf klaro_db
df -h  # Verify space available
python main.py
```

---

### Error 3: Token Limit Exceeded

**Error Message:**
```
openai.error.InvalidRequestError: This model's maximum context length is 16384 tokens
```

**What Causes It:**
- Prompt + messages exceed model context window
- Too many messages in conversation history
- Large file contents in context

**How to Fix:**

1. **Truncate message history:**
   ```python
   # In main.py
   def truncate_messages(messages, max_messages=20):
       if len(messages) > max_messages:
           # Keep system message + recent messages
           return [messages[0]] + messages[-max_messages:]
       return messages
   ```

2. **Use smaller model with larger context:**
   ```python
   # Change to gpt-4-turbo (128k context)
   LLM_MODEL = "gpt-4-turbo"
   ```

3. **Summarize previous context:**
   ```python
   # Add summarization step every N messages
   if len(messages) > 30:
       summary = llm.invoke("Summarize the analysis so far...")
       messages = [system_message, summary] + messages[-10:]
   ```

**Example Solution:**
```python
# Edit main.py
def run_model(state: AgentState):
    # Truncate old messages
    if len(state['messages']) > 25:
        state['messages'] = state['messages'][:1] + state['messages'][-24:]
    # Continue...
```

---

## General Troubleshooting Tips

### Enable Debug Logging

```python
# Add to main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Verify Environment

```bash
# Check Python version
python --version  # Should be 3.11+

# Check installed packages
pip list

# Check environment variables
env | grep -E '(OPENAI|LANGSMITH|KLARO)'
```

### Clean Installation

```bash
# Remove everything and start fresh
rm -rf klaro_db klaro-env
python -m venv klaro-env
source klaro-env/bin/activate  # On Windows: klaro-env\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python main.py
```

---

## Getting Help

If you encounter an error not listed here:

1. **Check GitHub Issues:** https://github.com/aethrox/klaro/issues
2. **Enable LangSmith Tracing:** See detailed execution logs
3. **Create Minimal Reproduction:**
   ```bash
   # Test on simple project first
   mkdir test_project
   echo "print('hello')" > test_project/main.py
   python main.py test_project
   ```
4. **Open GitHub Issue:** Include error message, trace, and environment details

---

## Related Documentation

- [Configuration Guide](./configuration.md) - Detailed configuration options
- [Usage Examples](./usage_examples.md) - Real-world usage scenarios
- [Main README](../README.md) - Project overview and quick start

# Code Interpreter SDK
E2B's [Code Interpreter SDK](https://github.com/e2b-dev/code-interpreter) allows you to add code interpreting capabilities to your AI apps.

The code interpreter runs inside the [E2B Sandbox](https://github.com/e2b-dev/e2b) - an open-source secure sandbox made for running untrusted AI-generated code and AI agents.
- ✅ Works with any LLM and AI framework
- ✅ Supports streaming content like charts and stdout, stderr
- ✅ Python & JS SDK
- ✅ Runs on serverless and edge functions
- ✅ Runs AI-generated code in secure sandboxed environments
- ✅ 100% open source (including [infrastructure](https://github.com/e2b-dev/infra))

Follow E2B on [X (Twitter)](https://twitter.com/e2b_dev).

## 🚀 Quickstart

### 1. Install SDK

JavaScript/TypeScript
```
npm i @e2b/code-interpreter
```

Python
```
pip install e2b_code_interpreter
```

### 2. Execute code with code interpreter inside sandbox

**JavaScript**
```ts
import { CodeInterpreter } from '@e2b/code-interpreter'

const sandbox = await CodeInterpreter.create()
await sandbox.notebook.execCell('x = 1')

const execution = await sandbox.notebook.execCell('x+=1; x')
console.log(execution.text)  // outputs 2

await sandbox.close()
```

**Python**
```py
from e2b_code_interpreter import CodeInterpreter

with CodeInterpreter() as sandbox:
    sandbox.notebook.exec_cell("x = 1")

    execution = sandbox.notebook.exec_cell("x+=1; x")
    print(execution.text)  # outputs 2
```

### 3. Hello World guide
Dive depeer and check out the [JavaScript](/hello-world/js) and [Python](/hello-world/py) the Hello World guides to learn how o connect code interpreter LLMs.


## 📖 Cookbook examples

**Hello World**
- [TypeScript](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/hello-world-js)
- [Python](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/hello-world-python)

**LLM Providers**
- 🪸 [Claude with code intepreter](https://github.com/e2b-dev/e2b-cookbook/blob/main/examples/claude-code-interpreter/claude_code_interpreter.ipynb)
- 🦙 [Llama 3 with code interpreter](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/llama-3-code-interpreter)
- [Mixtral with code interpreter and chat UI](https://github.com/e2b-dev/e2b-cookbook/tree/main/templates/mixtral-8x7b-code-interpreter-nextjs)

**AI Frameworks**
- 🦜⛓️ [LangChain with code interpreter](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/langchain-python)
- 🦜🕸️ [LangGraph with code interpreter](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/langgraph-python)
- [Autogen with secure sandboxed code interpreter](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/e2b_autogen)

## 💻 Supported languages for AI-code execution
- ✅ Python
- (soon) JavaScript/TypeScript 


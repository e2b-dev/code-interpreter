# Code Interpreter SDK
Built with [E2B](https://github.com/e2b-dev/e2b).


This Code Interpreter SDK allows you to run AI-generated Python code and each run share the context. That means that subsequent runs can reference to variables, definitions, etc from past code execution runs.
The code interpreter runs inside the [E2B Sandbox](https://github.com/e2b-dev/e2b) - an open-source secure micro VM made for running untrusted AI-generated code and AI agents.
- ✅ Works with any LLM and AI framework
- ✅ Supports streaming content like charts and stdout, stderr
- ✅ Python & JS SDK
- ✅ Runs on serverless and edge functions
- ✅ 100% open source (including [infrastructure](https://github.com/e2b-dev/infra))

Follow E2B on [X (Twitter)](https://twitter.com/e2b_dev)

<img width="1200" alt="Post-02" src="https://github.com/e2b-dev/code-interpreter/assets/5136688/2fa8c371-f03c-4186-b0b6-4151e68b0539">

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

## 🚀 Getting started with E2B

#### 1. Get API key
[Sign up](https://e2b.dev/docs/sign-in?view=sign-up) and [get your E2B API key](https://e2b.dev/docs/getting-started/api-key).

#### 2. Install code interpreter SDK
JavaScript
```js
npm i @e2b/code-interpreter
```

Python
```py
pip install e2b_code_interpreter
```

#### 3. Check out Hello World example
Check out the [TypeScript](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/hello-world-js) and [Python](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/hello-world-python) hello world examples.

#### 4. Explore documentation
Visit our docs at [e2b.dev/docs](https://e2b.dev/docs).


# Using custom sandbox with Code Interpreter SDK

If you want to customize the Code Interprerter sandbox (e.g.: add a preinstalled package) you can do that by using a [custom sandbox template](https://e2b.dev/docs/sandbox/templates/overview).


## Step-by-step guide
1. Create custom sandbox by following [this guide](https://e2b.dev/docs/guide/custom-sandbox)

2. Use prebuilt [E2B Code Interpreter image](https://hub.docker.com/r/e2bdev/code-interpreter) by replacing the `FROM` command in your `e2b.Dockerfile` with following

    ```Dockerfile
    FROM e2bdev/code-interpreter:latest
    ```

3. Copy [`start-up.sh`](./start-up.sh) to the same directory where's your `e2b.toml`

4. Run the following in the same directory where's your `e2b.toml`
    ```sh
    e2b template build -c "/home/user/.jupyter/start-up.sh"
    ```

5. Use your custom sandbox with Code Interpreter SDK

   **Python**
   ```python
   from e2b_code_interpreter import CodeInterpreter
   sandbox = CodeInterpreter(template="your-custom-sandbox-name")
   execution = sandbox.notebook.exec_cell("print('hello')")
   sandbox.close()

   # Or you can use `with` which handles closing the sandbox for you
   with CodeInterpreter(template="your-custom-sandbox-name") as sandbox:
       execution = sandbox.notebook.exec_cell("print('hello')")
   ```
   

   **JavaScript/TypeScript**
   ```js
   import { CodeInterpreter } from '@e2b/code-interpreter'
   const sandbox = await CodeInterpreter.create({ template: 'your-custom-sandbox-name' })
   const execution = await sandbox.notebook.execCell('print("hello")')
   await sandbox.close()
   ```

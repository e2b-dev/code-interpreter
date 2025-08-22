# Using custom sandbox with Code Interpreter SDK

If you want to customize the Code Interprerter sandbox (e.g.: add a preinstalled package) you can do that by using a [custom sandbox template](https://e2b.dev/docs/sandbox-template).


## Step-by-step guide
1. Create custom sandbox by following [this guide](https://e2b.dev/docs/sandbox-template)

2. Use prebuilt [E2B Code Interpreter image](https://hub.docker.com/r/e2bdev/code-interpreter) by replacing the `FROM` command in your `e2b.Dockerfile` with following

    ```Dockerfile
    FROM e2bdev/code-interpreter:latest
    ```

3. Copy [`start-up.sh`](./start-up.sh) to the same directory where's your `e2b.toml`

4. Run the following in the same directory where's your `e2b.toml`
    ```sh
    e2b template build -c "/root/.jupyter/start-up.sh"
    ```

5. Use your custom sandbox with Code Interpreter SDK

   **Python**
   ```python
   from e2b_code_interpreter import Sandbox
   sandbox = Sandbox.create(template="your-custom-sandbox-name")
   execution = sandbox.run_code("print('hello')")
   sandbox.kill()

   # Or you can use `with` which handles closing the sandbox for you
   with Sandbox.create(template="your-custom-sandbox-name") as sandbox:
       execution = sandbox.run_code("print('hello')")
   ```
   

   **JavaScript/TypeScript**

   ```js
   import {Sandbox} from '@e2b/code-interpreter'

const sandbox = await Sandbox.create({template: 'your-custom-sandbox-name'})
const execution = await sandbox.runCode('print("hello")')
await sandbox.kill()
   ```

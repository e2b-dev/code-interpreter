# E2B Code Interpreter — Go SDK

Go SDK for the [E2B](https://e2b.dev) Code Interpreter. It lets you run
AI-generated code inside secure, isolated E2B sandboxes and get back rich,
structured results (text, HTML, images, chart data, …).

This package mirrors the features of the official
[Python](../python) and [JavaScript](../js) SDKs.

## Install

```bash
go get github.com/e2b-dev/codeinterpreter-go
```

> **Go version**: 1.21+

## Get your API key

1. Sign up at [e2b.dev](https://e2b.dev).
2. Grab an API key from the [dashboard](https://e2b.dev/dashboard?tab=keys).
3. Export it:

```bash
export E2B_API_KEY=e2b_***
```

## Quick start

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    codeinterpreter "github.com/e2b-dev/codeinterpreter-go"
)

func main() {
    ctx := context.Background()

    sbx, err := codeinterpreter.Create(ctx, &codeinterpreter.SandboxOpts{
        Timeout: 60 * time.Second,
    })
    if err != nil { log.Fatal(err) }
    defer sbx.Kill(ctx)

    _, _ = sbx.RunCode(ctx, "x = 1", nil)

    exec, err := sbx.RunCode(ctx, "x += 1; x", nil)
    if err != nil { log.Fatal(err) }

    fmt.Println(exec.Text()) // "2"
}
```

## Features

The Go SDK exposes the same surface as the Python / JS SDKs:

### Sandbox lifecycle

| Function | Description |
|---|---|
| `Create(ctx, opts)` | Start a new sandbox. |
| `Connect(ctx, id, opts)` | Attach to a running sandbox. |
| `List(ctx, opts)` | List sandboxes for the API key. |
| `Sandbox.Kill(ctx)` | Terminate the sandbox. |
| `Sandbox.SetTimeout(ctx, d)` | Extend the sandbox lifetime. |
| `Sandbox.IsRunning(ctx)` | Health check. |
| `Sandbox.GetInfo(ctx)` | Metadata, start time, etc. |
| `Sandbox.GetHost(port)` | Hostname for a port exposed by the sandbox. |

### Code execution

| Function | Description |
|---|---|
| `Sandbox.RunCode(ctx, code, opts)` | Execute code (any supported language). |

`RunCodeOpts` lets you pass:

* `Language` — `"python"` / `"javascript"` / `"typescript"` / `"r"` / `"java"` / `"bash"` or any custom kernel id.
* `Context` — a pre-created `*Context` (mutually exclusive with `Language`).
* `Envs` — extra environment variables.
* `Timeout` / `RequestTimeout` — execution / request timeouts.
* `OnStdout`, `OnStderr`, `OnResult`, `OnError` — streaming callbacks.

### Code contexts (Jupyter kernels)

| Function | Description |
|---|---|
| `Sandbox.CreateCodeContext(ctx, opts)` | Create a fresh kernel. |
| `Sandbox.ListCodeContexts(ctx)` | List known kernels. |
| `Sandbox.RestartCodeContext(ctx, c)` | Restart a kernel (clears state). |
| `Sandbox.RemoveCodeContext(ctx, c)` | Terminate a kernel. |

### Result / Execution model

Every `RunCode` call returns an `*Execution`:

```go
type Execution struct {
    Results        []*Result
    Logs           Logs            // stdout / stderr lines
    Error          *ExecutionError // nil on success
    ExecutionCount int
}
```

Each `Result` may carry multiple representations of the same value: `Text`,
`HTML`, `Markdown`, `SVG`, `PNG`, `JPEG`, `PDF`, `LaTeX`, `JSON`, `JavaScript`,
`Data`, `Chart`, plus arbitrary `Extra` MIME types.

### Charts

`Result.Chart` is a `Chart` interface — type-assert it to inspect the
structured data:

```go
switch c := result.Chart.(type) {
case *codeinterpreter.LineChart:
    for _, series := range c.Points { ... }
case *codeinterpreter.BarChart:
    for _, bar := range c.Bars { ... }
case *codeinterpreter.PieChart:
    for _, slice := range c.Slices { ... }
case *codeinterpreter.BoxAndWhiskerChart:
    ...
case *codeinterpreter.ScatterChart:
    ...
case *codeinterpreter.SuperChart:
    for _, sub := range c.Charts { ... }
}
```

## Streaming output

```go
exec, err := sbx.RunCode(ctx, "for i in range(5): print(i)", &codeinterpreter.RunCodeOpts{
    OnStdout: func(msg codeinterpreter.OutputMessage) {
        fmt.Println(">", msg.Line)
    },
    OnResult: func(r *codeinterpreter.Result) {
        fmt.Println("got result with formats:", r.Formats())
    },
    OnError: func(e *codeinterpreter.ExecutionError) {
        fmt.Println("error:", e.Name, e.Value)
    },
})
```

## Error types

| Error | When |
|---|---|
| `*AuthenticationError` | Invalid / missing API key. |
| `*NotFoundError` | Resource (sandbox, context) not found. |
| `*TimeoutError` | Request or execution timed out. |
| `*RateLimitError` | Hit E2B rate limit. |
| `*InvalidArgumentError` | Bad arguments (e.g. both `Language` + `Context`). |
| `*SandboxError` | Generic error from the backend. |

Use Go's type assertion / `errors.As` to discriminate between them.

## Check docs

Visit the [E2B documentation](https://e2b.dev/docs) for more details.


package codeinterpreter_test

import (
	"context"
	"fmt"
	"time"

	codeinterpreter "github.com/e2b-dev/codeinterpreter"
)

// Example_create shows how to create a sandbox and run code. This is a
// documentation-only example; it requires the E2B_API_KEY env var to work
// against real infrastructure, so the helper below guards the call and simply
// returns without running if the key is missing.
func Example_create() {
	ctx := context.Background()

	sbx, err := codeinterpreter.Create(ctx, &codeinterpreter.SandboxOpts{
		Timeout: 60 * time.Second,
	})
	if err != nil {
		// No API key configured — skip the rest.
		return
	}
	defer sbx.Kill(ctx)

	if _, err := sbx.RunCode(ctx, "x = 1", nil); err != nil {
		return
	}
	exec, err := sbx.RunCode(ctx, "x += 1; x", nil)
	if err != nil {
		return
	}
	fmt.Println(exec.Text())
}

// Example_streaming demonstrates the streaming callbacks.
func Example_streaming() {
	ctx := context.Background()
	sbx, err := codeinterpreter.Create(ctx, nil)
	if err != nil {
		return
	}
	defer sbx.Kill(ctx)

	_, _ = sbx.RunCode(ctx, "print('hello')\nprint('world')", &codeinterpreter.RunCodeOpts{
		OnStdout: func(msg codeinterpreter.OutputMessage) {
			fmt.Printf("stdout: %s", msg.Line)
		},
		OnStderr: func(msg codeinterpreter.OutputMessage) {
			fmt.Printf("stderr: %s", msg.Line)
		},
	})
}

// Example_codeContext shows how to use multiple contexts (kernels).
func Example_codeContext() {
	ctx := context.Background()
	sbx, err := codeinterpreter.Create(ctx, nil)
	if err != nil {
		return
	}
	defer sbx.Kill(ctx)

	rctx, err := sbx.CreateCodeContext(ctx, &codeinterpreter.CreateCodeContextOpts{
		Language: codeinterpreter.LanguageR,
	})
	if err != nil {
		return
	}
	defer sbx.RemoveCodeContext(ctx, rctx)

	exec, err := sbx.RunCode(ctx, `x <- 1; x + 1`, &codeinterpreter.RunCodeOpts{
		Context: rctx,
	})
	if err != nil {
		return
	}
	fmt.Println(exec.Text())
}

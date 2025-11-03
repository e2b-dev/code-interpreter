from dotenv import load_dotenv
from e2b import Template
from template import make_template

load_dotenv()

Template.build(
    make_template(kernels=["python", "javascript"]),
    alias="code-interpreter-dev",
    cpu_count=1,
    memory_mb=1024,
    on_build_logs=lambda log_entry: print(log_entry),
)

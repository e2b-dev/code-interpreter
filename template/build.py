from dotenv import load_dotenv
from e2b_template import Template
from template import make_template

load_dotenv()

Template.build(
    make_template(),
    alias="code-interpreter",
    cpu_count=1,
    memory_mb=1024,
    on_build_logs=lambda log_entry: print(log_entry),
)

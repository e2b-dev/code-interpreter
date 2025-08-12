from dotenv import load_dotenv
from e2b_template import Template

load_dotenv()

template = Template(file_context_path="./")
with open("Dockerfile", "r") as f:
    dockerfile = f.read()
    template = template.from_dockerfile(dockerfile)

Template.build(
    template,
    alias="code-interpreter-from-dockerfile",
    cpu_count=1,
    memory_mb=1024,
    on_build_logs=lambda log_entry: print(log_entry),
)

from dotenv import load_dotenv
from e2b import Template, default_build_logger
from template import make_template
from uuid import uuid4

load_dotenv()

Template.build(
    make_template(set_user_workdir=True),
    alias="code-interpreter-ci-" + str(uuid4()),
    cpu_count=2,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
)

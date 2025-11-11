import os
from e2b import Template, default_build_logger
from template import make_template

Template.build(
    make_template(),
    alias=os.environ["E2B_TESTS_TEMPLATE"],
    cpu_count=2,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
)

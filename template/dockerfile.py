from template import make_template

tmp = make_template(kernels=["python", "javascript"])
print(tmp.to_dockerfile())
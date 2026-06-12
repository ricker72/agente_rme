import os

base = r"c:\Users\samatha\OneDrive\Desktop\agente_rme\tests\agents"
os.makedirs(base, exist_ok=True)
os.makedirs(r"c:\Users\samatha\OneDrive\Desktop\agente_rme\tests", exist_ok=True)
open(
    os.path.join(r"c:\Users\samatha\OneDrive\Desktop\agente_rme\tests", "__init__.py"),
    "a",
).close()
open(os.path.join(base, "__init__.py"), "a").close()
print("done")

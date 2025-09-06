# settings.py

# General settings for all diagrams
node_attr = {
    "fontsize": "20",
    "fontname": "Arial Bold"
}

# You can add other general settings here in the future
import os
# ---- Fix for Graphviz on Windows ----
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.name == "nt" and os.path.isdir(graphviz_bin):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ["GRAPHVIZ_DOT"] = os.path.join(graphviz_bin, "dot.exe")

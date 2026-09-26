import glob
for f in glob.glob("*.py"):
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    if "width='stretch'" in content or "width='content'" in content:
        content = content.replace("width='stretch'", "width='stretch'")
        content = content.replace("width='content'", "width='content'")
        with open(f, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Fixed {f}")

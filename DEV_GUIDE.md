
# 🔧 Developer Guide: Logic App Documentation Generator

This guide contains the Git workflow and branch safety tips to help you manage changes, test features, and always restore your stable working state.

---

## 🔒 STABLE BRANCH MANAGEMENT

### Tag your last-known-good commit
```bash
git tag stable-v1
git push origin stable-v1
```

### Create a new feature branch for testing
```bash
git checkout -b feature/add-diagrams
git push -u origin feature/add-diagrams
```

---

## 🔄 RESTORE FILES OR RESET STATE

### Restore just `generate_docx.py` from the stable branch
```bash
git restore --source stable/working-docgen logicapp_docgen/generate_docx.py
```

### Restore the file from a tag (e.g., `stable-v1`)
```bash
git restore --source stable-v1 logicapp_docgen/generate_docx.py
```

### Restore the entire working tree to stable version
```bash
git checkout stable/working-docgen
```

### Reset your current branch to match stable (warning: erases changes!)
```bash
git reset --hard stable/working-docgen
```

---

## 🧪 EXPERIMENTATION WORKFLOW

| Task                             | Command                                                        |
|----------------------------------|-----------------------------------------------------------------|
| Create new feature branch        | `git checkout -b feature/my-feature`                           |
| Revert single file to stable     | `git restore --source stable-v1 path/to/file.py`               |
| Discard all uncommitted changes  | `git restore .`                                                |
| View diff of file                | `git diff path/to/file.py`                                     |
| Commit your progress             | `git add . && git commit -m "Add X"`                           |
| Push to GitHub                   | `git push`                                                     |
| Compare with main/stable         | Use GitHub Pull Request interface                              |

---

## 📁 Helpful Paths in Your Repo

| File                             | Purpose                             |
|----------------------------------|-------------------------------------|
| `logicapp_docgen/generate_docx.py` | Generates the Word document         |
| `logicapp_docgen/core.py`        | Calls parser + docx generator       |
| `logicapp_docgen/diagram_builder.py` | Builds DOT diagrams from ARM       |
| `cli_updated.py`                 | CLI entry point for Docker/local    |

---

To ensure future work stays safe, always tag before testing, and branch before modifying.

<div align="center">

<!-- Logo/Header -->
<h1>
  <code style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.15em 0.4em; border-radius: 8px; font-family: 'Fira Code', monospace;">
    tdd-dsl
  </code>
</h1>

<p><strong>🧪 One contract. Every language. Test-first.</strong></p>

<p>
  An LLM-friendly DSL for describing behavior once and emitting executable tests<br/>
  for Python, TypeScript, Java, C#, Rust, Go, Odin, and Zig.
</p>

<!-- Badges -->
<p>
  <a href="#">
    <img src="https://img.shields.io/github/actions/workflow/status/JMoak/tdd-dsl/ci.yml?style=flat-square&logo=github&label=build" alt="Build Status"/>
  </a>
  <a href="https://pypi.org/project/tdd-dsl/">
    <img src="https://img.shields.io/pypi/v/tdd-dsl?style=flat-square&logo=pypi&color=blue" alt="PyPI Version"/>
  </a>
  <a href="#">
    <img src="https://img.shields.io/pypi/pyversions/tdd-dsl?style=flat-square&logo=python&color=3776AB" alt="Python Versions"/>
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/coverage-94%25-success?style=flat-square&logo=pytest&logoColor=white" alt="Coverage"/>
  </a>
</p>

<p>
  <a href="#">
    <img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square&logo=python&logoColor=white" alt="Code style: Black"/>
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/ruff-lint%7Cformat-261230?style=flat-square&logo=ruff&logoColor=white" alt="Ruff"/>
  </a>
  <a href="#license">
    <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square&logo=open-source-initiative&logoColor=white" alt="License"/>
  </a>
</p>

<!-- Language Badges -->
<p>
  <img src="https://img.shields.io/badge/🐍_Python-3.11+-success?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/%E2%9A%A1_TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/☕_Java-17+-orange?style=flat-square&logo=java&logoColor=white" alt="Java"/>
  <img src="https://img.shields.io/badge/%F0%9F%94%B7_C%23-12+-512BD4?style=flat-square&logo=csharp&logoColor=white" alt="C#"/>
  <img src="https://img.shields.io/badge/%E2%98%95_Rust-stable-DEA584?style=flat-square&logo=rust&logoColor=black" alt="Rust"/>
  <img src="https://img.shields.io/badge/%F0%9F%90%80_Go-1.21+-00ADD8?style=flat-square&logo=go&logoColor=white" alt="Go"/>
  <img src="https://img.shields.io/badge/%E2%9A%94%EF%B8%8F_Odin-dev-black?style=flat-square" alt="Odin"/>
  <img src="https://img.shields.io/badge/%E2%9A%A1_Zig-0.11+-FF4F00?style=flat-square&logo=zig&logoColor=white" alt="Zig"/>
</p>

</div>

---

## ✨ Quick Demo

Write your contract once:

```text
suite "Billing policy contract"
target python "billing_policy"
target typescript "billing-policy"
target java "com.example.BillingPolicy"

case "flags enterprise usage before charging":
  given input:
    {
      "account": {"plan": "team", "yearsActive": 1},
      "usage": {"projects": 91, "seats": 42}
    }
  when call "quoteSubscription"
  then equals:
    {
      "tier": "enterprise",
      "monthlyUsd": null,
      "requiresReview": true,
      "reason": "seat_count"
    }
```

Emit to any language:

```bash
# Python with pytest
$ tdd-dsl emit --target python contract.tdd
✓ Generated billing_policy_test.py

# TypeScript with Vitest
$ tdd-dsl emit --target typescript contract.tdd
✓ Generated billing-policy.test.ts

# Java with JUnit 5
$ tdd-dsl emit --target java contract.tdd
✓ Generated BillingPolicyTest.java
```

---

## 🚀 Installation

```bash
# From PyPI (recommended)
pip install tdd-dsl

# Or from source
git clone https://github.com/JMoak/tdd-dsl.git
cd tdd-dsl
pip install -e .
```

---

## 📖 Usage

### CLI Commands

```bash
# Validate a contract
tdd-dsl validate contract.tdd

# Emit tests for a target language
tdd-dsl emit --target python contract.tdd
tdd-dsl emit --target typescript contract.tdd
tdd-dsl emit --target java contract.tdd

# Run contract against local implementation
tdd-dsl run --target python --cwd ./my-project contract.tdd
```

### Python API

```python
from tdd_dsl import parse, validate, emit

# Parse and validate
ast = parse("contract.tdd")
diags = validate(ast)

# Emit to Python
python_code = emit(ast, target="python")
print(python_code)
```

---

## 🌍 Language Support Matrix

| Language | Emitter | Framework | Status | Runner |
|----------|---------|-----------|--------|--------|
| 🐍 Python | `python` | pytest | ✅ Stable | ✅ |
| ⚡ TypeScript | `typescript` | Vitest | ✅ Stable | ✅ |
| ☕ Java | `java` | JUnit 5 | ✅ Stable | ✅ |
| 🔷 C# | `csharp` | xUnit | ✅ Stable | ✅ |
| 🦀 Rust | `rust` | std test | ✅ Stable | ✅ |
| 🐹 Go | `go` | testing | ✅ Stable | ✅ |
| ⚔️ Odin | `odin` | core:testing | ✅ Stable | ✅ |
| ⚡ Zig | `zig` | std.testing | 🚧 Planned | ⏳ |

---

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   .tdd      │───▶│   Parser     │───▶│     AST     │
│  Contract   │    │  + Validate  │    │   + Diags   │
└─────────────┘    └──────────────┘    └──────┬──────┘
                                              │
                       ┌──────────────────────┼──────────────────────┐
                       ▼                      ▼                      ▼
                ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
                │ PyEmitter   │        │ TSEmitter   │        │ JavaEmitter │
                │  (pytest)   │        │  (Vitest)   │        │  (JUnit 5)  │
                └─────────────┘        └─────────────┘        └─────────────┘
```

---

## 🧪 Development

```bash
# Run tests
PYTHONPATH=src python -m unittest discover -s tests

# Update golden fixtures (intentional emitter changes only)
PYTHONPATH=src TDD_DSL_UPDATE_GOLDENS=1 python -m unittest tests.test_golden_fixtures

# Validate a contract
PYTHONPATH=src python -m tdd_dsl validate tests/fixtures/valid_minimal.tdd
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Overview & quickstart |
| [docs/SPEC.md](docs/SPEC.md) | DSL specification & grammar |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [docs/TICKETS.md](docs/TICKETS.md) | Development backlog |

**Emitter Docs:**
- [Python/pytest](docs/emitters/python.md)
- [TypeScript/Vitest](docs/emitters/typescript.md)
- [Java/JUnit 5](docs/emitters/java.md)
- [C#/xUnit](docs/emitters/csharp.md)
- [Rust](docs/emitters/rust.md)
- [Go](docs/emitters/go.md)
- [Odin](docs/emitters/odin.md)
- [Zig](docs/emitters/zig.md) (planned)

---

## 🤝 Contributing

Contributions welcome! The project follows a test-first approach:

1. **Issues first** — Check [docs/TICKETS.md](docs/TICKETS.md) for backlog
2. **Test-first** — Add fixtures before implementation
3. **Golden fixtures** — Update intentionally via `TDD_DSL_UPDATE_GOLDENS=1`
4. **Mutation tests** — Include failure cases, not just happy paths

```bash
# Setup dev environment
git clone https://github.com/JMoak/tdd-dsl.git
cd tdd-dsl
pip install -e ".[dev]"

# Run the test suite
pytest tests/

# Or with unittest
python -m unittest discover -s tests
```

---

## 📄 License

MIT © [Rosavera](https://github.com/JMoak)

---

<div align="center">

<p>
  <sub><sup>Made with 🌹 and 🧪</sup></sub>
</p>

<p>
  <a href="https://github.com/JMoak/tdd-dsl/stargazers">⭐ Star</a> •
  <a href="https://github.com/JMoak/tdd-dsl/fork">🍴 Fork</a> •
  <a href="https://github.com/JMoak/tdd-dsl/issues">🐛 Issues</a>
</p>

</div>

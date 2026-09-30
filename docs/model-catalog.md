# Internal LLM Model Catalog

This document defines the logical models exposed by the
company LLM gateway.

Developers SHOULD use logical model names and SHOULD NOT
depend directly on provider-specific model identifiers.

---

## company-fast

### Purpose

Default model for common workloads where latency, quality,
and cost need to be balanced.

### Recommended use cases

- General chat
- Summarization
- Explanation
- Lightweight analysis
- Developer questions
- Lightweight coding

### Current backend

Provider:

OpenAI

Provider model:

gpt-5.6-terra

### Usage

Clients must request:

`company-fast`

Do not request the provider model directly.

---

## company-coding

### Purpose

Higher-capability model intended for software engineering
and complex technical workloads.

### Recommended use cases

- Code generation
- Debugging
- Refactoring
- Code review
- Software architecture
- Complex technical reasoning
- Agentic coding

### Current backend

Provider:

OpenAI

Provider model:

gpt-5.6-sol

### Usage

Clients must request:

`company-coding`

Do not request the provider model directly.

---

# Design Principle

Clients depend on:

logical model

not:

provider + provider model

This allows the platform team to change providers or model
versions without requiring changes to developer tools.
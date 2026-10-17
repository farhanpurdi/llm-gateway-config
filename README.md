# LLM Gateway Configuration

Repo ini menyimpan config runtime LiteLLM, katalog model/provider deskriptif, policy
team, dan template OpenCode. Dokumentasi naratif dipusatkan di repo docs sibling.

- [Mulai membaca project](../llm-gateway-docs/README.md)
- [Master dan batas scope](../llm-gateway-docs/MASTER_CONTEXT.md)
- [Model catalog](../llm-gateway-docs/developer/model-catalog.md)
- [OpenCode](../llm-gateway-docs/developer/opencode.md)
- [Compatibility](../llm-gateway-docs/developer/compatibility.md)

```text
config/       Runtime LiteLLM YAML yang di-mount oleh gateway
models/       Definisi model; identitas logis berasal dari filename
providers/    Metadata provider; Phase1 OpenAI saja
policies/     Input policy team untuk script provisioning infra
clients/      Template config client
scripts/      Validator config/policy dan scanner
```

Katalog deskriptif tidak otomatis di-load runtime. Kedua CLI validator membandingkan
runtime, filename/routing model dan provider catalog terhadap kontrak Phase 1: tepat
dua alias OpenAI dengan mapping yang disetujui. Alias tambahan/duplikat, upstream
salah, drift katalog, credential berbeda dan routing alternatif ditolak.
Identitas model tetap berasal dari filename.

Dari repository ini:

```bash
export PATH="$PWD/../.venv/bin:$PATH"
./scripts/ci/validate.sh
# Command lama menjalankan rangkaian lengkap yang sama:
./scripts/validate.sh
```

Validator config dapat berjalan tanpa checkout repo docs; ia memeriksa source/runtime/
policy dan README lokal. Tautan/dokumen/katalog manusia divalidasi terpisah oleh
`llm-gateway-docs/scripts/validate-docs.py --workspace` saat seluruh repo tersedia.

Tes kontrak offline memakai salinan sementara, bukan config yang di-mount:

```bash
python3 scripts/ci/test-model-contract.py
```

[Laporan P1-06 dan kode](../llm-gateway-docs/reports/P1_06_MODEL_CONTRACT_REPORT.md)
menjelaskan hasil lokal dan gate commit/review/CI/live yang masih tersisa.

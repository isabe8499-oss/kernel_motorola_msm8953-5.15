# Deen C100 — primeiro ledger binário de memória (somente host)

Checkpoint: 2026-11-19, Motorola One XT1941-3 C100/PVT1, objetivo ACK Linux 5.15 + AOSPA Android 14.

## Escopo, fontes e limitações

Este documento acrescenta uma leitura binária reproduzível dos **DTBs experimentais** do ZIP
`DEEN_PACOTE_COMPLETO_PARA_IA_2026-11-19.zip` e compara os intervalos com os
**valores documentados anteriormente** em `documentation/DEEN_C100_STOCK_FDT_PROPERTY_DIFF.md`
e `documentation/DEEN_C100_STOCK_FDT_BINARY_RECONCILIATION.md`.

- Branch experimental de origem (não alterada): `deen/c100-smem-memory-region-fix`
- Commit da origem: `8dd376a6291729fd388622d6058fa8a0e0cd5df5`
- ACK pinado: `5cb316cf9d39318326075731e4e0c39b725d9c99`
- GitHub Actions run: [44128812332](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44128812332)
- Artefato de referência: `14347749886`, SHA-256 `a265656a70c79043657c4b44bc706d687d72d7d0047e43e1c33bbaa0918a4c80`
- PVT1 DTB SHA-256: `92c7f5c5e1c42d1bd6912ebfa952334b1f1cdb662401a51d25228d5ea075f7a4` (24028 bytes, 249 nós)
- PVT2 DTB SHA-256: `1bbe3e8a9f339e728c3b1a6231b5f5ceeb7599531ecfa14e036fa645ed4c87b7` (23996 bytes, 249 nós)

**Limitação principal:** o pacote de 19/11 não contém o `boot_b-original.img` nem o
FDT stock C100 de 253.704 bytes. Portanto, **não foi feita comparação byte a byte nova
contra a árvore stock**. A tabela de stock abaixo é transcrição da evidência
documental anterior; a leitura de binário desta auditoria vale para o *candidato*.
Também não foi feita leitura da partição `vendor`/firmware.

## 1. Ledger de 11 reservas fixas do PVT1 experimental (extraído dos bytes)

| Nó DTB experimental | Início | Tamanho | Fim exclusivo | `no-map` |
|---|---|---|---|---|
| `/reserved-memory/memory@81800000` | `0x81800000` | `0x2000` | `0x81802000` | yes |
| `/reserved-memory/memory@86300000` | `0x86300000` | `0x100000` | `0x86400000` | yes |
| `/reserved-memory/memory@86400000` | `0x86400000` | `0x400000` | `0x86800000` | yes |
| `/reserved-memory/memory@86c00000` | `0x86c00000` | `0x6a00000` | `0x8d600000` | yes |
| `/reserved-memory/memory@8d600000` | `0x8d600000` | `0x1100000` | `0x8e700000` | yes |
| `/reserved-memory/memory@8e700000` | `0x8e700000` | `0x700000` | `0x8ee00000` | yes |
| `/reserved-memory/memory@90000000` | `0x90000000` | `0x1000` | `0x90001000` | yes |
| `/reserved-memory/memory@91400000` | `0x91400000` | `0x700000` | `0x91b00000` | yes |
| `/reserved-memory/memory@92000000` | `0x92000000` | `0x100000` | `0x92100000` | yes |
| `/reserved-memory/memory@f2d00000` | `0xf2d00000` | `0x180000` | `0xf2e80000` | yes |
| `/reserved-memory/qseecom@84300000` | `0x84300000` | `0x2000000` | `0x86300000` | yes |

- Total de reservas fixas observadas sob `/reserved-memory`: **11**.
- Sobreposição entre esses intervalos fixos: **0**.
- Tabela de reservas no cabeçalho FDT (`memreserve`): **0 entradas**.
- Regiões de memória dinâmica, pools implicitamente reservados ou alterados por firmware/bootloader **não são abrangidos por esta verificação**.
- `memory` da raiz possui um `reg` zero como placeholder na origem MSM8953; não interpretar como mapa real de RAM.

## 2. Phandles/consumidores identificados

| Consumidor | Propriedade | Phandle | Provedor resolvido |
|---|---|---|---|
| `/smem` | `memory-region` | `0x47` | `/reserved-memory/memory@86300000` |
| `/smem` | `qcom,rpm-msg-ram` | `0x48` | `/soc@0/sram@60000` |

O PVT1 e o PVT2 têm o mesmo mapeamento acima. Nenhuma dessas referências diretas
ficou sem provedor no DTB experimental. O `hwlocks = <&tcsr_mutex 3>` existente
requer validação do contrato de hardware e **não** é prova de equivalência IPC.

Este verificador não enumera todas as propriedades `qcom,*`, `memory-region` indiretas,
referências de runtime, carves do bootloader ou consumidores de firmware. Logo,
não afirma ter identificado *todos* os consumidores da memória.

## 3. Regiões fixas documentadas no stock C100 (não lidas novamente do binário)

| Região stock segundo auditoria anterior | Início | Tamanho | Comparação limitada |
|---|---|---|---|
| `other_ext_region` | `0x84300000` | `0x02500000` | Candidato soma 32 + 1 + 4 MiB; significado não comprovado |
| `modem_region` | `0x86c00000` | `0x06a00000` | Intervalo idêntico no candidato; nome/consumidores pendentes |
| `adsp_fw_region` | `0x8d600000` | `0x01100000` | Intervalo idêntico; firmware/IPC pendentes |
| `wcnss_fw_region` | `0x8e700000` | `0x00700000` | Intervalo idêntico; Wi-Fi/firmware pendentes |
| `dfps_data_mem` | `0x90000000` | `0x00001000` | Intervalo idêntico; propósito/consumidor pendente |
| `splash_region` | `0x90001000` | `0x013ff000` | Ausente no candidato; não inferir que seja dispensável |
| `ramoops_mem_region` | `0xef000000` | `0x000c0000` | Ausente no candidato |
| `tzlog_bck_region` | `0xaefd2000` | `0x00002000` | Ausente no candidato |
| `wdog_cpuctx_region` | `0xaefd4000` | `0x0002c000` | Ausente no candidato |

**Ponto central:** `other_ext_region` stock corresponde numericamente ao intervalo
`0x84300000`–`0x86800000` (37 MiB), enquanto o candidato o cobre com:
- `qseecom@84300000`: 32 MiB
- `memory@86300000`: 1 MiB, usada como região SMEM
- `memory@86400000`: 4 MiB, uso não demonstrado

A soma dos tamanhos e a contiguidade são fatos; **QSEE, SMEM e a região de 4 MiB
não estão comprovados como donos equivalentes à região stock**.
Não editar os endereços/tamanhos somente para igualar a tabela.

## 4. Teste reproduzível e gates

Ferramenta somente host: `scripts/deen_fdt_memory_ledger.py` (Python 3, stdlib).

```bash
python3 scripts/deen_fdt_memory_ledger.py PVT1.dtb \
  --expected-board-id 0xc100 --expected-msm-id 0x125 --strict-structural > pvt1-ledger.json
python3 scripts/deen_fdt_memory_ledger.py PVT2.dtb \
  --expected-board-id 0xc200 --strict-structural > pvt2-ledger.json

# Somente quando o FDT original estiver novamente disponível:
python3 scripts/deen_fdt_memory_ledger.py PVT1.dtb \
  --stock STOCK_C100.fdt --expected-board-id 0xc100 \
  --expected-msm-id 0x125 --strict-structural > stock-candidate-ledger.json
```

Esses nomes `PVT1.dtb`, `PVT2.dtb` e `STOCK_C100.fdt` são **exemplos**; a ferramenta
não contém os binários, não os baixa e não toca o telefone.

Testes host feitos com os DTBs reais do ZIP:
- Identidade PVT1/C100 (incluindo MSM ID), 11 intervalos, ausência de overlap, phandles: **PASS direcionado**.
- Identidade PVT2/C200, 11 intervalos, ausência de overlap, phandles: **PASS direcionado**.
- Identidade errada: **falha esperada** (`exit 3`).
- Cabeçalho FDT inválido: **falha esperada** (`exit 2`).
- Comparação do mesmo FDT contra si: **nenhuma diferença** (sanidade do parser; **não** compara stock).

**Gates após esta auditoria:**
- Inventário candidate fixed-memory: `PASS_SCOPE_LIMITED`
- SMEM estrutural: `PASS_SCOPE_LIMITED` (CI existente)
- Propriedade de memória/firmware/IPC: `HOLD`
- Schema geral (14 diagnósticos por variante): `REVIEW_REQUIRED`
- Equivalência stock FDT: `HOLD`
- TSENS TYPE3, config Deen, kernel completo, AOSPA 14, boot/flash e merge em main: `HOLD`

## 5. Próximas tarefas concretas

1. Obter o **FDT stock C100 binário** da cópia de `boot_b-original.img` previamente auditada,
   ou arquivo FDT exportado e hasheado, para executar `--stock`. Não alterar o aparelho para isso.
2. Enumerar **cada nó reservado, `reg`, `size`, `no-map`, `reusable`, `phandle`,
   `memory-region(-names)` e também os consumidores `qcom,*` legados** na árvore stock;
   classificar `UNKNOWN` quando o dono não é provado.
3. Levantar memória física/intervalos específicos do SMEM, RPM shared SRAM,
   QSEE, MPSS, ADSP, WCNSS, ramoops, TZ log, watchdog, splash, RMTFS e pools dinâmicos.
4. Cruzar firmware e drivers ACK 5.15 com os doadores; não ativar remoteproc nem SMP2P
   sem verificar sinais, IRQs, clocks, firmware e range ownership.
5. Manter o próximo patch numa **branch isolada**; compilar ambos DTBs, rerodar
   schema estrito e publicar logs/hashes, com gates explícitos antes de qualquer merge.

**Sem flash, sem boot image, sem merge automático, sem declaração de bootabilidade.**
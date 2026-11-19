# Motorola One Deen C100 — reconciliação SMEM, RPM/SMD e firmware (19/11/2026)

**Base:** PR [#3](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/3), branch `audit/c100-memory-ledger-20261119`, baseada em `deen/c100-smem-memory-region-fix` (`8dd376a6291729fd388622d6058fa8a0e0cd5df5`).  **Alvo:** XT1941-3/PVT1/C100, ACK 5.15, AOSPA Android 14. **Escopo:** auditoria estática somente host, sem alterações em DTS, drivers, ROM, boot ou partições.

## Critério de evidência

1. **Binário:** DTBs PVT1 e PVT2 do pacote do usuário, produzidos no [workflow 44128812332](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44128812332), artefato `14347749886`; SHA-256 PVT1 `92c7f5c5e1c42d1bd6912ebfa952334b1f1cdb662401a51d25228d5ea075f7a4`, PVT2 `1bbe3e8a9f339e728c3b1a6231b5f5ceeb7599531ecfa14e036fa645ed4c87b7`.
2. **Código 5.15:** `arch/arm64/boot/dts/qcom/msm8953.dtsi` SHA de conteúdo GitHub `d75e7b8a43122671657d55bb8802adcba283d194`, `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi` SHA `2fe463a6802e52c1fb6f1351b6ef13d2e6318ad2` e drivers específicos da branch acima.
3. **Doador 4.19:** `arch/arm64/boot/dts/vendor/qcom/msm8953.dtsi` SHA `0879dae22d29fbe6af4c0967a92f65971ddb79ae`, `motorola/deen/reserved-memory.dtsi` SHA `1cc2d97e7f89962747191003f1543db6cfb7cc9d` e `motorola/deen/misc.dtsi` SHA `b79c74f759b33d606b222f768fda58f19a6c0e0a` da branch `4.19.325-WIP`.
4. **Stock:** números e propriedades descritos em `documentation/DEEN_C100_STOCK_FDT_BINARY_RECONCILIATION.md`, `documentation/DEEN_C100_STOCK_FDT_PROPERTY_DIFF.md` e no pacote; **o binário FDT stock original não está no pacote atual**, portanto os itens stock não são uma nova verificação direta.
5. O ZIP **não contém firmware da partição vendor**. Os nomes em DTS ou drivers não comprovam a presença de arquivos em `/vendor/firmware*` ou o funcionamento do carregamento.

## 1. Contrato SMEM × RPM RAM × hwspinlock

Leitura direta dos DTBs de ambos os PVT:

| Consumidor | Propriedade | Phandle/valor | Provedor | Evidência |
|---|---|---|---|---|
| `/smem` | `memory-region` | `0x47` | `/reserved-memory/memory@86300000` | `reg = 0x86300000/0x100000`, `no-map`, sem `compatible=qcom,smem` no nó reservado |
| `/smem` | `qcom,rpm-msg-ram` | `0x48` | `/soc@0/sram@60000` | `compatible=qcom,rpm-msg-ram`, `reg=0x60000/0x8000` no barramento SoC |
| `/smem` | `hwlocks` | `<0x49 3>` | `/soc@0/hwlock@1905000` | `compatible=qcom,tcsr-mutex`, `#hwlock-cells=1` |
| `/smd/rpm` | `qcom,ipc` | `<0x0d 8 0>` | `/soc@0/mailbox@b011000` | Região APCS, **não** confundir com `qcom,rpm-msg-ram` |
| `/smd/rpm` | `qcom,smd-edge` | `15` | RPM edge | `interrupts` contém SPI 168 no candidato |

**Resultado estrutural: PASS_SCOPE_LIMITED.** O driver `drivers/soc/qcom/smem.c` do ACK 5.15 executa `qcom_smem_map_memory(..., "memory-region", 0)` e, quando presente, mapeia o segundo segmento `"qcom,rpm-msg-ram"`. A etapa de inicialização também verifica o cabeçalho SMEM que foi estabelecido pelo bootloader. As referências corretas no FDT **não provam** que o cabeçalho, a inicialização firmware ou a topologia de memória são equivalentes no aparelho.

**Atenção à propriedade de memória:** o candidato cobre numericamente `0x84300000–0x86800000` com QSEE 32 MiB (`0x84300000–0x86300000`), SMEM 1 MiB (`0x86300000–0x86400000`) e região genérica 4 MiB (`0x86400000–0x86800000`). O stock documenta `other_ext_region` de 37 MiB no mesmo intervalo. **Não deduzir ownership, uso de DMA, sharing ou coerência a partir da soma.** Há 11 reservas fixas no candidato, sem sobreposição entre elas; isto não abrange reservas dinâmicas, bootloader, QSEE ou firmware ativo.

## 2. RPM, clocks, reguladores e domínio de energia

No DTB experimental, a árvore `/smd/rpm/rpm-requests` inclui:

| Nó | Compatible no DTB | Correspondência encontrada na fonte ACK 5.15 | Status |
|---|---|---|---|
| `rpm-requests` | `qcom,rpm-msm8953` | **Ausente** em `drivers/soc/qcom/smd-rpm.c::qcom_smd_rpm_of_match` na branch examinada (linhas 233–249) | **LACUNA ESTÁTICA / REVIEW_REQUIRED** |
| `rpmcc` | `qcom,rpmcc-msm8953` | Presente em `drivers/clk/qcom/clk-smd-rpm.c` (linha 1075) | `OF_MATCH_PRESENT`, não há prova de probe |
| `power-controller` | `qcom,msm8953-rpmpd` | Presente em `drivers/soc/qcom/rpmpd.c` (linha 403) | `OF_MATCH_PRESENT`, binding ainda em revisão |
| `regulators` | `qcom,rpm-pm8953-regulators` | Presente em `drivers/regulator/qcom_smd-regulator.c` (linha 1183) | `OF_MATCH_PRESENT`, firmware/voltagem não validados |

**Nova descoberta:** a ausência de `qcom,rpm-msm8953` na tabela `of_match` do *transporte* SMD RPM não aparece nos diagnósticos dt-schema anteriores, mas merece um gate específico. O barramento RPMsg (`drivers/rpmsg/rpmsg_core.c`, `rpmsg_dev_match`) usa `of_driver_match_device` quando não há match anterior por ID; o driver RPM examinado não declara `id_table`. Isso indica um risco concreto de o RPM não se associar ao dispositivo correspondente. **Não editar o driver nem substituir por `qcom,rpm-msm8916`** por suposição: confirmar a criação/nomeação do `rpmsg_device`, os bindings de ACK e a plataforma; depois submeter a menor correção compatível em outra branch e compilar seus objetos.

Também há diagnósticos de schema nos filhos RPM/RPMPD, ainda não resolvidos. `OF_MATCH_PRESENT` jamais equivale a `probe PASS`, hardware PASS ou a um schema PASS.

## 3. Firmware, canais SMD e SMP2P

| Subsistema | Doador 4.19 (DTS) | Backport ACK 5.15 separado | Candidato C100 atual |
|---|---|---|---|
| MSS/MPSS | `qcom,pil-q6v55-mss`, PAS ID **5**, `qcom,firmware-name="modem"`, memory-region `modem_mem`, `0x86c00000/0x06a00000` | `qcom,msm8953-mss-pil` na branch `deen/msm8953-remoteproc-backports`, **não integrada** | Reserva de 106 MiB existente; **sem nó MSS remoteproc** |
| ADSP/LPASS | `qcom,pil-tz-generic`, PAS ID **1**, firmware `"adsp"`, SMEM ID **423**, `adsp_fw_mem` em `0x8d600000/0x01100000` | `qcom,msm8953-adsp-pil` na branch isolada, configuração de driver com `adsp.mdt` | Reserva de 17 MiB existente; **sem nó ADSP remoteproc** |
| WCNSS/Pronto | `qcom,pil-tz-generic`, PAS ID **6**, firmware `"wcnss"`, SMEM ID **422**, `wcnss_fw_mem` em `0x8e700000/0x00700000` | `qcom,pronto-v3-pil` na branch isolada, driver upstream tem `WCNSS_FIRMWARE_NAME="wcnss.mdt"` | Reserva de 7 MiB existente; **sem nó Pronto remoteproc** |

O doador SoC inclui SMP2P com remote PIDs **1** (modem), **2** (ADSP), **4** (WCNSS), e canais SMD `modem=0`, `adsp=1`, `wcnss=6` no DTS, mas o `motorola/deen/misc.dtsi` declara **nós legados nomeados** `qcom,smp2p-*@0x0b011008` como `disabled`. **Os nomes são diferentes** dos nós SMP2P sem endereço presentes no SoC DTS; só a árvore *compilada* do doador/stock mostra quais endpoints ficaram realmente ativos. Não concluir indiscriminadamente que os SMP2P finais do aparelho estavam todos desabilitados.

No candidato ACK 5.15 atual, a única aresta SMD identificada é a RPM. Não há os canais SMD remotos modem/ADSP/WCNSS nem os nós remoteproc citados. **Manter assim** até mapear contra stock: endpoint, remote PID, doorbell/IRQ, SMEM state IDs, PAS/SCM, clock/reset/regulator e o formato de firmware.

O doador inclui ainda pools `shared-dma-pool` **dinâmicos** (Venus, secure, QSEECom, ADSP) e um RMTFS legado que não correspondem automaticamente aos intervalos fixos do candidato. O FDT candidato contém `qcom,rmtfs-mem` fixo em `0xf2d00000/0x180000`; o doador tem `qcom,sharedmem-uio` com `reg=0x00000000/0x180000` — diferença de **binding e endereço** que requer inspeção stock, sem alteração imediata.

## 4. Gates e ações a partir daqui

| Gate | Decisão |
|---|---|
| PVT1/PVT2 ID e SMEM phandles | `PASS_SCOPE_LIMITED` |
| RPM shared SRAM e APCS/IPC phandles | `PASS_SCOPE_LIMITED` para geometria de DTB |
| RPM `qcom,rpm-msm8953` × tabela `smd-rpm.c` | `REVIEW_REQUIRED` (lacuna confirmada em fonte) |
| RPMCC/RPMPD/PM8953 `of_match` | `MATCH_PRESENT_ONLY`, sem prova runtime |
| Endpoints SMD remotos, SMP2P e PAS | `NOT_PORTED / HOLD` |
| Arquivos vendor de modem, adsp, wcnss e seus hashes | `NOT_AVAILABLE / HOLD` |
| Equivalência `other_ext_region`, QSEE/SMEM, RMTFS, pools dinâmicos | `HOLD` |
| Schema global | `REVIEW_REQUIRED` (14 diagnósticos por PVT no artefato anterior) |
| Kernel final, ROM, boot/flash e merge | `HOLD` / `NOT_AUTHORIZED` |

**Próximos trabalhos permitidos:**

1. Executar o gate host `scripts/deen_c100_ipc_contract_audit.py` após gerar DTBs no CI, com `--kernel-root .`, arquivando JSON, `.config`, logs, hashes e SHA de origem. Ele **relata** o match RPM ausente, sem alterar drivers e sem chamar isso de PASS global.
2. Quando houver **cópia de backup existente** do `boot_b-original.img`/FDT stock C100, extrair o FDT fora do aparelho, verificar hash e executar a comparação com o candidato. Não solicitar novo flash nem gravação de partição.
3. Conferir árvore stock efetivamente compilada para as diferenças de `smp2p`, `rmtfs` e regiões dinâmicas, e conferir blobs vendor (hashes, caminhos reais e ABI) antes de criar qualquer DTS de MSS, ADSP ou WCNSS.
4. Separar um futuro patch mínimo de compatibilidade RPM (drivers/bindings), com testes de objeto e schema, **sem misturar** com este PR de auditoria; não ativar remoteproc ou SMP2P sem prova.

**Resultado:** auditoria estática e script reprodutível. **Não** aprova boot, merge, alteração de memória ou qualquer imagem para flash.
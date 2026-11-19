# Deen C100/PVT1 — auditoria dos gates RPM/SMEM após o PR #4

**Data:** 2026-11-19  
**Alvo:** Motorola One XT1941-3, C100/PVT1, ACK Linux 5.15 / AOSPA Android 14 experimental  
**Escopo:** documentação e análise *read-only*, sem alteração de DTS, firmware, drivers, imagem de boot ou partições  
**Base exata:** `fix/deen-c100-rpm-of-match-20261119` em `366a6db4a77c479f2547b21c707bef7fb0dbbbdb`  
**Histórico:** PR #3 (auditoria de memória) e PR #4 (match OF RPM), ambos drafts, sem merge  

## 1. Verificação final do GitHub Actions PR #4

| Run | Gatilho | Head SHA | Status final | Artefato e digest ZIP |
|---|---|---|---|---|
| [44540735878](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44540735878) | push | `64179a0185f06659a9b778dbf3fe2e325c122464` | SUCCESS | `14537273704`; `sha256:fa8c7427427cfc35c5a22ab94429ed577c603bd19be8cf8d57c7fa6af09bea7b` |
| [44540905891](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44540905891) | push final | `366a6db4a77c479f2547b21c707bef7fb0dbbbdb` | SUCCESS | `14537388679`; `sha256:47e19500aa115f3d16ed7985ffba7a8043e858ff44aa9628f11eac4e6d77a2cf` |
| [44540977638](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44540977638) | pull_request | `366a6db4a77c479f2547b21c707bef7fb0dbbbdb` | SUCCESS | `14538477426`; `sha256:1b709880a03bdb1d625b7ba64d705c13fd9ab650298ef02e3da108d88a2a345f` |

Todos os jobs/steps, incluindo artifact upload, concluíram `success`. Os logs dos três jobs registram seis testes de associação RPMsg/OF + dois testes de regressão, objeto `drivers/soc/qcom/smd-rpm.o` identificado como ELF AArch64, geração dos DTBs PVT1/PVT2, **RPM OF match `PASS_SCOPE_LIMITED`** e `dt-doc-validate` do **documento** `qcom,smd-rpm.yaml` sem falhas. **Não houve link do kernel `vmlinux`, boot nem execução no telefone.** O schema completo dos DTBs **não** faz parte deste gate.

## 2. Ordem de dependências de inicialização: verificado vs ainda não provado

### G1 — reservar e mapear SMEM e RPM message SRAM

- PVT1 compilado do pacote: `/reserved-memory/memory@86300000` `reg = 0x86300000/0x00100000`, `no-map`; `/smem` com `compatible = "qcom,smem"`, `memory-region = <0x47>` apontando à reserva e `qcom,rpm-msg-ram = <0x48>` apontando a `/soc@0/sram@60000` (`reg = 0x60000/0x8000`).
- `hwlocks = <0x49 3>` aponta a `/soc@0/hwlock@1905000`, `compatible = "qcom,tcsr-mutex"`, `reg = 0x1905000/0x20000`, `#hwlock-cells = <1>`.
- `drivers/soc/qcom/smem.c`: `qcom_smem_probe()` mapeia `memory-region` e `qcom,rpm-msg-ram`; **exige** `header->initialized == 1`, `header->reserved == 0`, versão global suportada 11 ou 12, partições coerentes e posse do hwspinlock. Geometria e phandles PASS; **cabeçalho SBL, versão e lock em hardware NÃO VERIFICADOS**.
- `drivers/hwspinlock/qcom_hwspinlock.c`: tabela OF aceita `qcom,tcsr-mutex`, com caminho MMIO; não há evidência de `probe` real ou lock adquirido no XT1941-3.

### G2 — registrar a aresta SMD RPM

- PVT1: `/smd` `compatible = "qcom,smd"`; `/smd/rpm` tem `qcom,smd-edge = 15`, `qcom,ipc = <&apcs 8 0>`, interrupção GIC SPI 168; APCS resolve para `/soc@0/mailbox@b011000` com reg 0xb011000/0x1000. `qcom,remote-pid` **não aparece**, mas é explicitamente opcional em `qcom,smd.txt` e o driver usa `QCOM_SMEM_HOST_ANY` por padrão: **não é bug demonstrado**.
- `drivers/rpmsg/qcom_smd.c`: a aresta depende de SMEM, de registrar o IRQ e de que a tabela de alocações SMD contenha o canal; o dispositivo RPMsg só nasce quando o processador remoto manifesta estado `OPENING`/`OPENED`. Tudo isto é exigência de **runtime ainda não demonstrada**.
- Não substituir a tupla APCS/IRQ ou supor que exista canal anunciado sem prova do firmware/bootloader e da seleção C100.

### G3 — criar o RPM RPMsg e associar o driver

- PVT1: `/smd/rpm/rpm-requests` tem `compatible = "qcom,rpm-msm8953"` e `qcom,smd-channels = "rpm_requests"`.
- `qcom_smd_match_channel()` localiza o filho pelo nome do canal; `qcom_smd_create_device()` transfere esse nó para `rpdev->dev.of_node`.
- `rpmsg_dev_match()` usa `of_driver_match_device()` após a tentativa por ID; `qcom_smd_rpm_driver` usa `qcom_smd_rpm_of_match[]`.
- PR #4 adicionou **apenas** `{ .compatible = "qcom,rpm-msm8953" }` ao driver. O binding `Documentation/devicetree/bindings/soc/qcom/qcom,smd-rpm.yaml` **já incluía** esta string e requer o canal apropriado. **Match estático PASS.**
- Mesmo com o match, `qcom_smd_rpm_probe()` precisa do endpoint RPMsg e chama `of_platform_populate()` para filhos de clocks, power domains e reguladores. Não há prova de troca de mensagens RPM nem de respostas/ACK em hardware.

### G4 — configuração e consumidores

- `arch/arm64/configs/defconfig` contém `CONFIG_QCOM_SMEM=y`, `CONFIG_QCOM_SMD_RPM=y`, `CONFIG_RPMSG_QCOM_SMD=y`, `CONFIG_HWSPINLOCK_QCOM=y`, `CONFIG_HWSPINLOCK=y` e `CONFIG_QCOM_RPMPD=y` na revisão analisada. **Isso é configuração genérica ARM64, não uma defconfig Deen derivada do stock.**
- Drivers `clk-smd-rpm.c`, `rpmpd.c` e `qcom_smd-regulator.c` têm entradas MSM8953/PM8953 correspondentes. `of_match` presente é pré-requisito, não teste de comunicação/consumo real.

## 3. Gate de schema distinto do gate do PR #4

- Os logs **anteriores** `PVT1-schema.log` e `PVT2-schema.log` contidos no pacote 19/11 exibem **14 diagnósticos por variante**. Entre eles:
  - `rpm-requests`: filhos `power-controller`, `regulators` e `rpmcc` rejeitados por `qcom,smd-rpm.yaml` (`additionalProperties: false` e sem descrição dos filhos nesta revisão);
  - `power-controller`: `clock-names` e `clocks` diagnosticados por `qcom,rpmpd.yaml`;
  - outras incompatibilidades de bindings (TSENS, USB, SPMI, RTC, APCS, GCC e placeholder de memória).
- Os testes do PR #4 executam `dt-doc-validate` **no YAML**; isso é `BINDING_DOCUMENT_PASS`, mas **não é** `DTB_SCHEMA_PASS`. Não foi executado gate completo de `dt-validate` em ambos os DTBs para aceitar o PR #4.
- Não apagar filhos, clocks ou propriedades do DTB apenas para silenciar o schema. Primeiro investigar os schemas exatos e os consumidores, em outro patch isolado. O RPM transport match **não exige alterações de binding neste PR**.

## 4. Memória: aritmética não é propriedade

- PVT1 do pacote: 11 reservas fixas sem sobreposição entre si; `other_ext_region` do stock anteriormente documentado corresponde a `0x84300000/0x02500000`, enquanto o candidato o divide em QSEE 32 MiB + SMEM 1 MiB + região 4 MiB. Propriedade/semântica **HOLD**.
- Não há no pacote de 19/11 o FDT binário original stock C100 de 253.704 bytes, nem as partições vendor com os blobs de firmware. Não foi possível fazer nova equivalência binária stock-vs-candidato ou aferir versões, nomes reais e hashes de firmware.
- Outras regiões stock (splash, ramoops, tzlog e watchdog) ainda não estão semanticamente reconciliadas. O RMTFS candidato usa binding/endereço diferentes do doador 4.19; não converter por aproximação.
- MSS, ADSP, WCNSS e SMP2P não estão integrados nos DTBs experimentais. Sem ativação nesta etapa.

## 5. Gatilhos de aceitação para futuras análises (sem executar no telefone)

| Gate | Estado | Evidência necessária |
|---|---|---|
| CI de objeto RPM / OF / documento binding | **PASS_SCOPE_LIMITED** | Executado em 3 runs, artefatos e logs preservados |
| DTBs C100/C200 identidade, phandles e reservas fixas | **PASS_SCOPE_LIMITED** | Verificadores host anteriores e novo gate PR #4 |
| SMEM cabeçalho SBL, versão de partição, lock MMIO | **UNKNOWN_RUNTIME / HOLD** | Evidência de boot stock/diagnóstico somente leitura já existente ou autorizado separadamente |
| Aresta SMD RPM: IRQ, APCS e anúncio `rpm_requests` | **UNKNOWN_RUNTIME / HOLD** | Registro verificável do canal e dos recursos em boot; não inferir de DTS |
| `qcom_smd_rpm_probe()`, RPM ACK e votos de reguladores | **UNKNOWN_RUNTIME / HOLD** | Evidência de probe e protocolo, sem habilitar firmware desconhecido |
| Schema completo PVT1/PVT2 | **REVIEW_REQUIRED** | Executar `dt-validate` pinado e reconciliar causas sem remover funções |
| Equivalência stock C100, reserva, vendor/firmware | **HOLD** | Original C100 FDT e evidência vendor já existente, com SHA-256 |
| Kernel completo, ROM, boot image, flash, merge | **HOLD / NOT_AUTHORIZED** | Gates técnicos prévios não satisfeitos |

**Conclusão:** o PR #4 corrige a única lacuna de correspondência OF demonstrada para RPM. Prosseguir com diagnóstico de schema/consumidores e dependências SMEM/SMD, sem tocar na topologia de memória, habilitar firmware, produzir boot ou integrar na branch principal.
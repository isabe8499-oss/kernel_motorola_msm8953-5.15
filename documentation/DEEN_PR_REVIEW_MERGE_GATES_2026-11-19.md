# Motorola One Deen — revisão dos PRs e regras de integração ACK 5.15

Verificado no GitHub em **2026-11-19**. Aplicação: [isabe8499-oss/kernel_motorola_msm8953-5.15](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15), projeto Motorola One XT1941 (deen), MSM8953, C100/PVT1 e C200/PVT2.

> **Este documento é uma decisão de fluxo de desenvolvimento, não autorização para boot, flash, firmware ou merge de driver.** CI de objeto, Kconfig, DTS ou documentação não valida o hardware.

## 1. Bloqueador estrutural da branch principal

- Branch default `main` em `2cbac8401f3aada1ca74c60dba4a10e50fcc5426`: é uma árvore de **gestão, documentação, bootstrap e workflows**, não a árvore-fonte completa do Linux. Sua raiz contém `.github/`, `README.md`, `bootstrap/` e `documentation/`.
- A árvore Linux/ACK 5.15 está na família de branches `upstream/android14-5.15-lts`, `deen/bringup-ack515-base` e `deen/c100-schema-reconcile-v2` e descendentes.
- `compare main...deen/c100-schema-reconcile-v2` e `compare main...fix/deen-tsens-hw-id-count-guard-20261119` retornam **“No common ancestor”** no GitHub. `drivers/thermal/qcom/tsens.c` e `arch/arm64/boot/dts/qcom/msm8953.dtsi` nem existem em `main`.
- Consequência: **não usar merge normal/forçado das branches do Linux em `main`**, nem alterar o default branch por atalho. A revisão humana deve primeiro aprovar um plano explícito para o repositório-fonte/branch de integração ACK. Este bloqueio já aparecia no relatório `documentation/DEEN_LIVE_REPOSITORY_STATE_2026-11-17.md`.

## 2. Estado dos PRs abertos: revisão ≠ merge

Os PRs são empilhados numa cadeia de bases dependentes; nenhum tem `main` como base. Os dez PRs marcados **ready for review** em 19/11/2026 continuam `open` e **não foram merged**.

| PR | Objeto | Estado de revisão | Merge na cadeia ACK |
|---|---|---|---|
| [#2](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/2) | Alteração do SMEM no DTS | **DRAFT / HOLD** | NÃO: modelo stock SMEM/memória e semântica de handoff não conciliados |
| [#3](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/3) | Ledger e gate de memória | READY FOR REVIEW | Somente após revisão dos limites de evidência; sem implicar compatibilidade stock |
| [#4](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/4) | OF match `qcom,rpm-msm8953` | READY FOR REVIEW | NÃO agora: efeitos de probe/RPM/remote firmware requerem controle de integração |
| [#5](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/5) | Auditoria documental RPM/SMEM | READY FOR REVIEW | Documentação apenas; sem CI próprio na branch |
| [#6](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/6) | Schema RPM/RPMPD e DTS | READY FOR REVIEW | Revisão de binding + prova stock/DTB, antes de integração |
| [#7](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/7) | Binding SPMI e gate | READY FOR REVIEW | Revisão de efeito global do schema, não só Deen |
| [#9](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/9) | Contrato TSENS TYPE3 3.18→5.15 | READY FOR REVIEW | Auditoria estática, TSENS runtime HOLD |
| [#10](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/10) | Registradores TSENS, IRQ e zonas CPU | READY FOR REVIEW | Auditoria estática, sem calibração comprovada |
| [#11](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/11) | Descritor staged 15 IDs sem callbacks nem OF | **DRAFT / HOLD** | NÃO: incompleto, não é driver funcional |
| [#12](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/12) | Guarda `data->hw_ids` contra override DT 16×15 | READY FOR REVIEW | Avaliar reaplicação isolada sobre branch ACK sem depender do #11; verificar código + testes |
| [#13](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/13) | Kconfig GKI+Deen20+host5 e CI de 13 objetos | READY FOR REVIEW | **Host-only**; não promover fragmento a defconfig final |
| [#15](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/15) | APCS/SMSM, três `qcom,ipc` e CI de 15 objetos | READY FOR REVIEW | **Host-only**; não habilitar APCS/SMSM só porque compilam |

O GitHub considera os PRs `mergeable=true` **com suas bases imediatas**, e o último check do HEAD de cada PR com workflow próprio foi aprovado. Isso não é uma revisão de integração em outra branch. Até esta auditoria, **nenhum dos PRs possuía aprovação de revisão humana**. A ausência de checks específicos no PR #5 documental não deve ser descrita como CI verde.

## 3. Decisão técnica: APCS, SMSM e RPM

[PR #15](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/15), SHA `80e43ac9708ac93b18076e1398e076957b2477ad`, passou nos checks *push* [#44583818560](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44583818560) e *pull_request* [#44583833029](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44583833029), com **54 testes, 15 objetos LLVM18 AArch64 e DTBs imutáveis**. Seu gate é estritamente `PASS_HOST_ONLY_WITH_RUNTIME_HOLD`.

O candidato DTS descreve um **syscon** `/soc@0/mailbox@b011000` e as propriedades legadas `qcom,ipc`:
- RPM SMD edge 15: `<&apcs 8 0>`;
- SMSM host1: `<&apcs 8 13>`;
- SMSM host3: `<&apcs 8 19>`.

O código `drivers/rpmsg/qcom_smd.c` tenta mailbox, mas, sem `mboxes` e quando obtém `-ENODEV`, usa `qcom,ipc` com `syscon_node_to_regmap`; `drivers/soc/qcom/smsm.c` usa `qcom,ipc-%d` pelo mesmo padrão legado. Assim, **não há prova de que `CONFIG_QCOM_APCS_IPC=y` seja necessária ao caminho RPM/SMD já descrito**. SMSM, por sua vez, depende do estado real em SMEM e de semântica do firmware, ainda não confirmadas.

O fragmento de duas opções `QCOM_APCS_IPC=y` e `QCOM_SMSM=y` deve permanecer **somente em host-CI**. A configuração mínima Deen20, o host5 e os DTBs não são expandidos para uso físico nesta fase. Nenhum remoteproc/SMP2P/ADSP/WCNSS deve ser habilitado por inferência de Kconfig.

## 4. Evidência stock e gates não resolvidos

`documentation/C100_DTB_IDENTITY_AND_BOOT_EVIDENCE_AUDIT.md` no ramo `main` documenta que um `boot_b` stock anteriormente analisado contém **sete FDTs** e identifica C100 com 1.471 nós (253.704 bytes). A variante candidata original tinha cerca de 248 nós. Portanto, **o relatório stock prévio existe**, mas isso não significa que tenhamos feito **nesta revisão** uma comparação binária *nova* dos três IPCs do PR #15 com o arquivo FDT stock. Solicitar a reabertura do binário stock verificado e um diff de propriedades/consumidores antes de declarar paridade.

Restam 11 diagnósticos de schema conhecidos **em cada DTB candidato compilado nos PRs recentes**, incluindo TSENS. O antigo relato de 160 diagnósticos pertence à etapa inicial do DTS, não deve ser confundido com a avaliação corrente. O gate de firmware/IPC e proteção térmica permanece **HOLD** mesmo quando os checks estáticos estão verdes.

## 5. Sequência proposta para merges de código (NÃO executada)

1. **Escolher o destino real:** fixar o SHA de uma branch ACK-derived de integração, e verificar qual histórico de DTS/firmware foi selecionado. Não apontar a árvore Linux diretamente para o `main` de documentação. Se a intenção futura for mudar a branch default, isso exige decisão e plano de preservação de histórico próprios.
2. **Separar correções sem firmware de mudanças de hardware:** preparar changesets mínimos para testes de contrato e para a guarda genérica de `hw_ids` (#12), sem arrastar o descritor incompleto (#11). Manter revisão individual e checks sobre o exato SHA do destino escolhido.
3. **Revisar a cadeia #2→#7:** não integrar sem resolver a semântica do SMEM stock/hwlocks e os efeitos globais dos bindings; usar evidência binária e não apenas schema.
4. **Revisar #9–#15:** manter auditorias prontas para revisão, mas não conectar OF ao staged TYPE3 nem copiar host-only fragments para a configuração de produção.
5. **Somente após reviews e CI da árvore de integração completa:** decidir merges por ordem, com SHA esperado, preservando a possibilidade de reversão. A aprovação de um PR empilhado não aprova automaticamente seus ancestrais.
6. **Antes de sequer preparar uma imagem de boot para device:** obter configuração completa Deen, firmware/IPC/thermal/SMEM validados, concordância com o bootloader e estratégia de recuperação. Sem hardware autorizado ou prova da segurança, manter `BOOT/FLASH=HOLD`.

## 6. Estado de aceite

- `PR_REVIEW_TRIAGE = PASS`: dez PRs promovidos para revisão, dois continuam em draft.
- `HOST_ONLY_APCS_SMSM_AUDIT = PASS`: apenas fonte/config/DTB/objetos, não runtime.
- `MAIN_ACK_GIT_HISTORY = UNRELATED`: exige planejamento, não merge forçado.
- `HUMAN_CODE_REVIEW = PENDING`; `ACK_SOURCE_MERGE = HOLD`.
- `SMEM/RPM_RUNTIME = HOLD`; `TSENS_RUNTIME = HOLD`; `GLOBAL_DTB_SCHEMA = REVIEW_REQUIRED`.
- `FULL_DEEN_DEFCONFIG = HOLD`; `BOOT_IMAGE = HOLD`; `FIRMWARE_ENABLEMENT = HOLD`; `FLASH = HOLD`.

**Única mudança de `main` permitida nesta etapa:** este documento de coordenação, sem tocar arquivos-fonte, drivers, DTS, imagens ou firmware.

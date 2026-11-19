# Motorola One Deen C100 — compatibilidade OF do RPM sobre SMD

Data: 2026-11-19. Alvo: XT1941-3, MSM8953, C100/PVT1, ACK 5.15 experimental.
Escopo: correção mínima no driver `smd-rpm.c`, sem alterar firmware, Device Tree, imagem de boot ou partições.

## Proveniência exata

- Base de auditoria PR #3: `audit/c100-memory-ledger-20261119`, início `3fb4de6781f01a79789d2a30fc3cee528f0520e7`.
- Branch isolada: `fix/deen-c100-rpm-of-match-20261119`.
- Fonte do driver antes do patch: `drivers/soc/qcom/smd-rpm.c`, blob `dfdd4f20f5fd4dec579e5ab799620e187e40b823`.
- Device Tree: `arch/arm64/boot/dts/qcom/msm8953.dtsi`, blob `d75e7b8a43122671657d55bb8802adcba283d194`.
- Binding do mesmo kernel: `Documentation/devicetree/bindings/soc/qcom/qcom,smd-rpm.yaml`, blob `1b0062e3c1a4b1fd5ce330a4f12ecaf47bd427ec`.
- Transportes: `drivers/rpmsg/qcom_smd.c` e `drivers/rpmsg/rpmsg_core.c`, ambos lidos na mesma fonte.

## Prova da cadeia de associação no código

1. DTS: `/smd/rpm/rpm-requests` declara `compatible = "qcom,rpm-msm8953"` e `qcom,smd-channels = "rpm_requests"`.
2. `qcom_smd_match_channel()` (qcom_smd.c, linhas 1009–1028) procura um filho disponível cujo `qcom,smd-channels` seja igual ao nome do canal SMEM/SMD.
3. `qcom_smd_create_device()` (linhas 1072–1101) registra `rpmsg_device` com `rpdev->dev.of_node = qcom_smd_match_channel(...)`. **Esse passo depende de o processador remoto efetivamente anunciar/abrir o canal**; não é provado por DTB ou compilação.
4. `rpmsg_dev_match()` (rpmsg_core.c, linhas 510–528) verifica eventual `id_table`; se não casar, retorna `of_driver_match_device(dev, drv)`.
5. `qcom_smd_rpm_driver` define `.of_match_table = qcom_smd_rpm_of_match`, sem `id_table` explícita. A tabela **não** continha `qcom,rpm-msm8953`.
6. O schema `qcom,smd-rpm.yaml` já inclui `qcom,rpm-msm8953` na enumeração e na exigência condicional de `qcom,smd-channels`. Logo, não há justificativa para alterar schema ou compatibilidade DTS.

## Delta proposto

Adicionar **uma única linha** em `drivers/soc/qcom/smd-rpm.c`:

```diff
   { .compatible = "qcom,rpm-msm8936" },
+  { .compatible = "qcom,rpm-msm8953" },
   { .compatible = "qcom,rpm-msm8974" },
```

Não há novas chamadas de RPM, mudanças de clock, regulador, firmware ou offsets. A correção evita apenas o match OF ausente no caminho esperado.

## Critérios de teste reprodutíveis

- Testes `scripts/test_deen_c100_rpm_of_match.py` comprovam presença exata de uma entrada na tabela, binding, nome do canal, transporte `qcom_smd` e fallback OF do RPMsg.
- GitHub Actions `deen-c100-rpm-of-match.yml` compila o objeto AArch64 `drivers/soc/qcom/smd-rpm.o` e DTBs PVT1/PVT2 em `defconfig`, valida a arquitetura ELF com `readelf`, e reutiliza os verificadores estáticos do PR #3.
- O gate do PR #3 exige `driver_match_gaps == []` para ambos os DTBs e `rpm_transport.driver.status == OF_MATCH_PRESENT`.
- `dt-doc-validate` (dtschema 2024.2) checa o **binding existente**, sem alterações.
- Anexar logs e SHA-256 dos objetos/DTBs; resultado CI isolado **não valida** boot, firmware vendor, SMP2P, modems, TSENS, equivalência total do DTB nem schema global.

## Restrições

**Gates em HOLD**: canal SMD anunciado em hardware; comunicação RPM real; memória QSEE/SMEM/firmware; inicialização do kernel; imagem de boot; ROM AOSPA Android 14; flash; merge. Nenhum passo do workflow cria arquivo de flash nem altera o aparelho.

Pull request proposto como **draft/stacked** com base no HEAD do PR #3, evitando modificar o PR de auditoria e a branch `main`.

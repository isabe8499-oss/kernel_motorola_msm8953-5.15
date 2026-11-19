# Deen C100 — triagem TSENS TYPE3 e correção restrita de schema SPMI (19/11/2026)

## Referência exata e limites

- Alvo: Motorola One deen XT1941-3, **C100/PVT1**; PVT2/C200 é controle de comparação.
- Base isolada: PR #6, commit `154dc21ade2744a55d86868637309e57aefd818e`; PRs #3 a #6 não mesclados.
- Pacote de 19/11: contém DTBs candidatos, logs e relatórios; **não contém o FDT original C100 em formato binário**, e portanto nenhuma comparação binária nova com stock foi possível. As propriedades stock TSENS descritas abaixo provêm da auditoria anterior registrada em `documentation/DEEN_C100_TSENS_AND_PINCTRL_AUDIT.md` no branch `main`.
- Não modificar endereço físico, IRQ, contador de sensor, PMIC, calibração, firmware, boot image ou telefone.

## 1. Diagnósticos exatos no artefato do PR #6

`PVT1-schema.log` e `PVT2-schema.log` do artefato 14540866082 (run [44544833312](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44544833312)) têm 12 diagnósticos por DTB:

- `thermal-sensor@4a9000`: `compatible: 'oneOf' conditional failed` para `['qcom,msm8953-tsens', 'qcom,tsens-v2']`. O binding `qcom-tsens.yaml` não aceita a identificação MSM8953 + fallback v2 nesta versão.
- `spmi@200f000`: `reg: [[33615872,4096],[37748736,8388608],[46137344,8388608],[58720256,2097152],[33595392,8448]] is too long`. O arquivo genérico `Documentation/devicetree/bindings/spmi/spmi.yaml` impõe `reg.maxItems: 1`.
- Os 10 restantes (root memory, GCC, RTC ×2, USB ×5, APCS) seguem `REVIEW_REQUIRED`.

## 2. TSENS — contrato stock demonstrado em documentação prévia; NÃO corrigir só o schema

| Campo | Auditoria stock C100 prévia | Candidato ACK 5.15 |
|---|---|---|
| Caminho | `/soc/tsens@4a8000` | `/soc@0/thermal-sensor@4a9000` |
| Compatible | `qcom,msm8953-tsens` | `qcom,msm8953-tsens`, `qcom,tsens-v2` |
| Recursos | `0x4a8000/0x2000`; `0xa4000/0x1000` | `0x4a9000/0x1000`; `0x4a8000/0x1000` |
| Interrupções | SPI 184 e 314; upper-lower / critical | Ainda não reconciliadas integralmente |
| Sensores | 15, IDs/clients 1 a 15, slopes 0xc80 | 16 na base candidata |
| Driver | `drivers/thermal/msm-tsens.c` 3.18; `TSENS_TYPE3` | `drivers/thermal/qcom/tsens.c` 5.15; fallback `data_tsens_v2` |

Código doador 3.18 `drivers/thermal/msm-tsens.c`: `qcom,msm8953-tsens` resolve para `TSENS_CALIB_FUSE_MAP_NONE` e o fluxo `TSENS_TYPE3` possui recursos/IRQ/IDs diferentes. A tabela OF de `drivers/thermal/qcom/tsens.c` ACK 5.15 tem `qcom,tsens-v2`, **não** `qcom,msm8953-tsens`. Não portar a força a implementação térmica v2, nem declarar `TSENS_SCHEMA_PASS` apenas adicionando compatible ao YAML.

**Gate térmico:** `TSENS_TYPE3_PORT=HOLD`; são necessários driver específico e validação de register map, janelas, IRQs, mapeamento 15 IDs, slopes, tratamento de calibração e provas no dispositivo antes de ativar. A ausência de leitura térmica validada é bloqueio de segurança.

## 3. SPMI — cinco regiões explicadas pelo binding e pelo driver ACK 5.15

Candidato `arch/arm64/boot/dts/qcom/msm8953.dtsi`, nó `spmi@200f000`:

| Índice | Reg-name | Endereço | Tamanho |
|---|---|---|---|
| 0 | core | `0x0200f000` | `0x1000` |
| 1 | chnls | `0x02400000` | `0x800000` |
| 2 | obsrvr | `0x02c00000` | `0x800000` |
| 3 | intr | `0x03800000` | `0x200000` |
| 4 | cnfg | `0x0200a000` | `0x2100` |

- O binding *Qualcomm* `Documentation/devicetree/bindings/spmi/qcom,spmi-pmic-arb.txt` prescreve `core/intr/cnfg` e `chnls/obsrvr` para controladores v2. Seu driver `drivers/spmi/spmi-pmic-arb.c` usa `platform_get_resource_byname()` para estes recursos. Nenhum dos cinco pode ser retirado só para eliminar o diagnóstico.
- A tabela OF do driver aceita `qcom,spmi-pmic-arb`; seu probe lê a versão do hardware em runtime. A correspondência de cada faixa com o FDT **stock C100 exato não foi retestada** porque falta seu binário.
- O binding genérico de barramento (`spmi.yaml`) **não pode ampliar a regra para todos os fabricantes**. Esta branch move a limitação de `reg` para uma condicional `compatible`: `qcom,spmi-pmic-arb` admite 3–5 recursos; todos os demais permanecem com `maxItems:1`. A condição usa `required: [compatible]` para nós genéricos sem compatible não receberem a exceção.
- Nenhuma mudança em `msm8953.dtsi`, driver SPMI, PMIC, offsets, IRQ, regulator, sensor térmico ou firmware.

## 4. Gate reproduzível

Workflow `.github/workflows/deen-c100-spmi-schema-scope.yml`:

1. Executa novos testes de escopo e regressivos dos PRs #3–#6.
2. Compila os DTBs PVT1/PVT2 e o objeto `drivers/spmi/spmi-pmic-arb.o` em AArch64, sem kernel Image.
3. `dt-doc-validate` verifica o binding editado; `dt-mk-schema` gera schema completo com `dtschema==2024.2`; `dt-validate` gera logs completos.
4. Gate estrito exige **11 diagnósticos restantes** em cada DTB, sem diagnóstico SPMI, com **TSENS ainda denunciado**, demais erros idênticos, geometrias SPMI/identidades intactas.
5. Dois controles independentes: nó SPMI não-Qualcomm com uma região é válido no escopo SPMI; com duas regiões deve gerar diagnóstico `spmi@1000: reg ... too long`. Isso prova que a regra genérica não foi relaxada.
6. Exige SHA-256 **idêntico** aos dois DTBs publicados no PR #6: PVT1 `fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a`, PVT2 `9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05`. A mudança é no schema **apenas**, portanto nenhum byte do DTB pode variar.

**Não chamar 11 diagnósticos de PASS global.** Persistem TSENS, restante do SoC, memória, boot, hardware runtime e firmware. Avisos de schemas externos (STM32) também não devem ser apagados ou mascarados.

## 5. Decisão e dependências seguintes

- `SPMI_SCHEMA`: PASS direcionado apenas após CI e fixtures.
- `TSENS_TYPE3`: HOLD (port do driver térmico é o próximo item substancial; criar plano específico antes de mexer em registradores).
- `STOCK_SPMI_BINARY`: HOLD até a cópia previamente existente e verificável do FDT stock C100 estar disponível.
- `BOOT/FLASH`, `FIRMWARE/REMOTEPROC`, `MEMORY_OWNERSHIP`, `MERGE`: HOLD.

# Deen C100/PVT1 — ponte de contrato TSENS TYPE3 (auditoria sem ativação)

Data: 19/11/2026. Branch: `audit/deen-c100-tsens-type3-contract-20261119`, criada do HEAD `e8e288572f9c4586a2023b8651cee0994964bae5` do [PR #7](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/7). Issue principal: [#8](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/8).

## Fontes inspecionadas, e o que elas NÃO provam

- Stock **documentado anteriormente**: [DEEN_C100_TSENS_AND_PINCTRL_AUDIT.md](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/blob/main/documentation/DEEN_C100_TSENS_AND_PINCTRL_AUDIT.md), extração C100 de `boot_b` (offset 0x00b7820a). O pacote `DEEN_PACOTE_COMPLETO_PARA_IA_2026-11-19.zip` **não contém o FDT stock binário**. Não foi feita nova verificação stock byte a byte.
- Doador 3.18.140: [drivers/thermal/msm-tsens.c](https://github.com/isabe8499-oss/kernel_motorola_msm8953/blob/lineage-18.1/drivers/thermal/msm-tsens.c), lido diretamente. A tabela `tsens_match` em torno de L924 aceita `qcom,msm8953-tsens` com `TSENS_CALIB_FUSE_MAP_NONE`. Em L5575–L5578, o MSM8953 segue o ramo `TSENS_TYPE3`.
- ACK 5.15 candidato: [drivers/thermal/qcom/tsens.c](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/blob/fix/deen-c100-spmi-schema-20261119/drivers/thermal/qcom/tsens.c), [tsens-v2.c](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/blob/fix/deen-c100-spmi-schema-20261119/drivers/thermal/qcom/tsens-v2.c), [tsens.h](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/blob/fix/deen-c100-spmi-schema-20261119/drivers/thermal/qcom/tsens.h), [msm8953.dtsi](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/blob/fix/deen-c100-spmi-schema-20261119/arch/arm64/boot/dts/qcom/msm8953.dtsi). O candidato segue `qcom,tsens-v2`, `#qcom,sensors = <16>` e índices implícitos 0–15.

## Resultado novo 1 — as janelas TM podem corresponder fisicamente

O FDT stock documenta `tsens_physical` em **0x4a8000 / 0x2000**. O DTSI 5.15 separa **SROT** (`0x4a8000 / 0x1000`) e **TM** (`0x4a9000 / 0x1000`).

| Registro | Doador TYPE3 3.18 | Moderno v2 5.15 | Endereço físico calculado |
|---|---|---|---|
| Status do sensor 0 | `tsens_physical + 0x10a0` | `TM + 0xa0` | `0x4a90a0` |
| Ready / TRDY | `tsens_physical + 0x10e4` | `TM + 0xe4` | `0x4a90e4` |

Constantes confirmadas diretamente em `msm-tsens.c` (`TSENS_TM_SN_STATUS`/`TSENS_TM_TRDY`), `tsens-v2.c` (`TM_Sn_STATUS_OFF`/`TM_TRDY_OFF`) e `tsens.c` (`init_common`). **Essas igualdades não demonstram, sozinhas, compatibilidade da versão, calibração, mapeamento, limiares ou interrupções.**

O stock também declara `tsens_eeprom_physical` **0x0a4000 / 0x1000**, recurso não descrito no candidato. O doador 3.18 o mapeia em `get_device_tree_data()`, mesmo com `TSENS_CALIB_FUSE_MAP_NONE` para o MSM8953. Não inferir leitura de efuse obrigatória nem dispensabilidade da região EEPROM apenas pelo nome.

## Resultado novo 2 — mapeamento de sensores, não apenas quantidade

| Aspecto | Stock documentado | Candidato atual |
|---|---|---|
| Número | 15 | 16 |
| Hardware IDs | 1–15 | 0–15 por default |
| Client IDs | 1–15 | não modelados |
| Slopes | 15 entradas `0xc80` | não modelados |
| IRQs físicos | SPI 184 / 314 | SPI 184 / 314 |
| Nomes de IRQ | `tsens-upper-lower`, `tsens-critical` | `uplow`, `critical` |
| Regiões | TM contíguo + EEPROM | SROT/TM separadas |

O 5.15 **possui suporte explícito** a subconjuntos de IDs pela tabela `struct tsens_plat_data.hw_ids`; em `tsens_probe()` (L1118–L1142), `#qcom,sensors` sobrescreve `data->num_sensors`, e `hw_ids[i]` é usado quando definido. Portanto, um port *poderia* usar 15 IDs 1–15 sem copiar todo o driver vendor, mas **nenhuma tabela/compatible foi criada ou associada nesta auditoria**. Esse caminho exige ainda provas dos demais contratos.

## Resultado novo 3 — atenção às unidades e à segurança térmica

O doador 3.18 faz leitura do campo TYPE3 de 12 bits, verifica o bit `VALID` (bit 21) e aplica extensão de sinal a partir do bit `0x800`. Seu retorno de `msm_tsens_get_temp()` para TYPE3 é o valor com sinal, sem executar a conversão ADC `tsens_tz_code_to_degc`.

O 5.15 v2 declara `adc = 0` e seu `tsens_hw_to_mC()` faz `sign_extend32(temp, resolution) * 100`; o novo modelo de referência host reproduz **somente essa regra 5.15** com vetores de 12 bits. **Não se conclui que o caminho térmico legado entregue exatamente as mesmas unidades à API 5.15.** Essa divergência deve ser investigada antes de habilitar um novo match, limites de viagem, governação térmica ou boot.

Em particular, `TSENS_CALIB_FUSE_MAP_NONE` não significa que temperatura/limiares estejam validados. É necessário verificar validação de leitura, valor negativo, limites físicos, medição da versão do bloco, máscaras de IRQ, throttling e a relação entre zona térmica e sensor.

## Entregáveis desta branch (somente host)

- `scripts/deen_c100_tsens_type3_contract.py`: confere DTBs PVT1/C100 e PVT2/C200, hashes identicamente aos publicados no PR #7, identidade, dois pares reg/IRQ, contador, compatibilidade, propriedades ausentes, correspondência física de offsets e a permanência **exata dos 11 diagnósticos anteriores**. Retorna `PASS_HOST_AUDIT_ONLY_WITH_THERMAL_HOLD`, jamais `TSENS_RUNTIME_PASS`.
- `scripts/test_deen_c100_tsens_type3_contract.py`: testes negativos de valores fora do campo de 12 bits, do cálculo de signed/mC do **5.15** e da divergência de IDs 15 vs 16; não lê sensores reais.
- `.github/workflows/deen-c100-tsens-type3-contract.yml`: compila **apenas objetos existentes** `tsens.o` e `tsens-v2.o` para AArch64, mais DTBs PVT1/PVT2, reaplica `dtschema==2024.2` e preserva os 11 erros por DTB. Logs/objetos são artefatos de auditoria; nenhum `Image`, `boot.img` ou ZIP de flash.

### Próximos passos obrigatórios antes de um port funcional

1. Recuperar e conferir a cópia antiga do FDT C100 por hash, ou outra fonte *stock* verificável, sem inventar propriedades ausentes.
2. Verificar na fonte 3.18 todos os offsets de threshold/status/clear e a política de IRQ; conferir com `tsens-v2.c` e a variação real do MSM8953.
3. Definir uma implementação 5.15 específica para 15 IDs 1–15 (e conversão/unidades validadas), em outra branch, com testes de vetores e compilação. Não fazer associação OF antes de provar a integridade térmica.
4. Reconciliar EEPROM e calibração/thermal zones/limites sem supor equivalência com a implementação genérica.
5. Manter `TSENS_TYPE3=HOLD`, `STOCK_FDT_DIRECT=HOLD`, `THERMAL_RUNTIME=HOLD`, `DTB_SCHEMA_GLOBAL=REVIEW_REQUIRED`, `FIRMWARE/BOOT/FLASH/MERGE=HOLD`.

**Não há nenhuma alteração de driver, DTS, binding, imagem ou firmware neste PR.**

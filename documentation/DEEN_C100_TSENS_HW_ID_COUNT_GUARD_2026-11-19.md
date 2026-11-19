# Deen C100 — proteção `hw_ids` contra `#qcom,sensors` maior que a tabela

Data: 19/11/2026. Base imutável: [PR #11](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/11), SHA `04c41b130583245a409a2216dc4648f8c78bf0e3`. Branch experimental `fix/deen-tsens-hw-id-count-guard-20261119`, sem merge ou boot. Documento-fonte: `drivers/thermal/qcom/tsens.c` e `tsens.h` no próprio kernel 5.15.

## Defeito de segurança demonstrado no código do kernel

Em `tsens_probe()` (na fonte de base, linhas ~1118–1149), a contagem começa com `data->num_sensors`, depois `of_property_read_u32(np, "#qcom,sensors", &num_sensors)` pode sobrescrevê-la. O código aloca `priv->sensor` usando a **contagem do DT** e copia `data->hw_ids[i]` até essa quantidade, **sem conferir o comprimento do array**. A validação de `priv->ops` fica depois da cópia.

No descritor **ainda não associado** de `tsens-v2.c`, `data_msm8953_stage_only` tem `num_sensors=15` e uma tabela `hw_ids` com 15 elementos (1–15). O DTS de origem `msm8953.dtsi` permanece com `#qcom,sensors=<16>`. Uma futura associação inadvertida antes de corrigir a contagem causaria leitura de `hw_ids[15]`, que não existe.

**A falha é de limites da API genérica, não uma prova de que TSENS C100 funcione ou deixe de funcionar.**

## Correção mínima, limitada à segurança da cópia

Em `drivers/thermal/qcom/tsens.c`, depois de validar `num_sensors > 0` e **antes da alocação e do primeiro acesso a `hw_ids[i]`**:

```c
/*
 * A DT #qcom,sensors override may be larger than the platform's
 * hw_ids table. Reject it before copying those IDs into priv->sensor.
 */
if (data->hw_ids && num_sensors > data->num_sensors) {
    dev_err(dev, "%s: sensor count exceeds hardware ID map\n", __func__);
    return -EINVAL;
}
```

- Com tabela explícita `hw_ids`, o máximo permitido é `data->num_sensors`, evitando acesso fora do array.
- Sem tabela `hw_ids`, o caminho genérico de IDs sequenciais é **inalterado** por essa guarda.
- DT com 15 IDs e contagem 15 continua válido **para a checagem de limites**; isso não significa que o driver térmico esteja pronto.
- DT que declara 16 contra array de 15 é rejeitado com `-EINVAL`, sem copiar a posição 16 inexistente.
- A correção é aplicável a quaisquer outros SoCs com mapas explícitos menores do que um possível override DT. A mudança exige revisão antes de merge para avaliar outros consumidores.

## Não alterado nesta branch

Nenhuma mudança de `msm8953.dtsi`, `tsens-v2.c`, `tsens.h`, `qcom-tsens.yaml`, `tsens_table`, descritor/ops/campos de registrador, EEPROM, temperaturas ou firmware. O *fallback* genérico `qcom,tsens-v2` já declarado no DTSI permanece exatamente como estava; **não afirmar que o TSENS atual está desativado**. A guarda só age quando existe `data->hw_ids`.

## Validação host

- `scripts/test_deen_tsens_hw_id_count_guard.py` exige o `if (data->hw_ids && num_sensors > data->num_sensors)` na rotina real **depois de ler a contagem DT e antes de alocar/copiar qualquer ID**. Testa 16×15 inválido, 15×15 válido, menor contagem válida, zero inválido e o caminho sem mapa sem regressão.
- Workflow novo `.github/workflows/deen-c100-tsens-hw-id-bound.yml` reexecuta os testes do descritor e dos PRs anteriores, fixa o doador 3.18 pelo SHA, compila objetos ARM64 `tsens.o`, `tsens-v2.o` e DTBs PVT1/C100 e PVT2/C200, confirma que **o descritor continua sem OF match** e os símbolos são apenas dados.
- Schema completo `dtschema==2024.2` ainda reporta **11 diagnósticos por variante**, incluindo TSENS. Hashes imutáveis esperados: PVT1 `fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a`, PVT2 `9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05`.
- **PASS do objeto e da guarda não testa uma leitura térmica real nem autoriza habilitar a entrada OF.**

## Passos de port ainda bloqueados

`TSENS_TYPE3_PORT=HOLD`, `EEPROM_CALIBRATION=HOLD`, `THERMAL_RUNTIME=HOLD`, `STOCK_FDT_DIRECT=HOLD`, `TSENS_SCHEMA=REVIEW_REQUIRED`, `DEEN_FULL_DEFCONFIG=HOLD`, `BOOT_IMAGE=HOLD`, `FIRMWARE=HOLD`, `FLASH=HOLD`, `MERGE=HOLD`.

Antes de qualquer boot/flash, ainda é necessário um FDT stock C100 verificável, compatibilidade de versão/limiares/IRQ/calibração, configuração completa específica do dispositivo, drivers essenciais e validação do contrato de boot/recovery. Não gerar um ZIP flashável como substituto dessas evidências.

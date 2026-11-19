# Deen C100 — rastreabilidade TSENS TYPE3: 11 registradores, 15 IDs, oito zonas térmicas

Data: 19/11/2026. Base: [PR #9](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/9), commit `c8dc5f61febaf3d203779b0fca5e339f4d34625b`. Doador 3.18.140 em `isabe8499-oss/kernel_motorola_msm8953`, branch `lineage-18.1`, **fixado no commit** `1f700e4c2e31c435358e7531dfc0c2e41e2a2684`. Issue de bloqueio: [#8](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/8).

**Objetivo exclusivamente analítico:** reconciliar definições numéricas do doador e da base 5.15. Não habilitar OF match, alterar DTS/driver, gravar firmware, inicializar TSENS ou autorizar boot.

## 1. Identidade e proveniência

- O documento `main/documentation/DEEN_C100_TSENS_AND_PINCTRL_AUDIT.md` **afirma**, a partir de extração histórica de `boot_b`, que C100/PVT1 usa `qcom,msm8953-tsens`, 15 IDs de sensores/cliente 1–15, duas IRQs 184/314 e registro físico `0x4a8000+0x2000` mais janela EEPROM `0x0a4000+0x1000`. Isso é **fonte secundária já registrada no repositório**, não uma comparação nova com o FDT stock original; o binário original continua ausente.
- O driver 3.18 `drivers/thermal/msm-tsens.c` tem match direto `qcom,msm8953-tsens`, ramo `TSENS_TYPE3`, e código para status, limiares e máscara de IRQ.
- O candidato 5.15 `msm8953.dtsi` tem `compatible = "qcom,msm8953-tsens", "qcom,tsens-v2"`, 16 sensores, duas janelas SROT/TM, IRQs 184/314. Seu driver usa fallback genérico `qcom,tsens-v2` e não fornece entrada OF exclusiva MSM8953.
- `Documentation/devicetree/bindings/thermal/qcom-tsens.yaml` não aceita essa combinação no schema. O diagnóstico TSENS **deve permanecer visível**; um PASS de schema artificial não valida o hardware.

## 2. Correspondência de 11 pares de registradores

O script confere, diretamente nas definições `#define` dos **dois repositórios**, a igualdade `0x4a8000 + deslocamento_TYPE3 = 0x4a9000 + deslocamento_TM_5.15`.

| Registro | Offset legado (base 0x4a8000) | Offset TM 5.15 (base 0x4a9000) |
|---|---:|---:|
| INT_EN | 0x1004 | 0x004 |
| UPPER_LOWER_INT_STATUS | 0x1008 | 0x008 |
| UPPER_LOWER_INT_CLEAR | 0x100c | 0x00c |
| UPPER_LOWER_INT_MASK | 0x1010 | 0x010 |
| CRITICAL_INT_STATUS | 0x1014 | 0x014 |
| CRITICAL_INT_CLEAR | 0x1018 | 0x018 |
| CRITICAL_INT_MASK | 0x101c | 0x01c |
| UPPER_LOWER_THRESHOLD | 0x1020 | 0x020 |
| CRITICAL_THRESHOLD | 0x1060 | 0x060 |
| SENSOR_STATUS | 0x10a0 | 0x0a0 |
| TRDY | 0x10e4 | 0x0e4 |

Isso valida a **geometria dos endereços no código**, não a identidade da versão real, as operações de escrita, calibração ou proteção térmica.

## 3. IDs e máscaras de interrupção

No contrato stock documentado, cada sensor lógico (i) tem hardware ID (i), para (i in [1,15]). O modelo host para cada ID confere, sem acessar hardware:

- limiar lower/upper: `TM + 0x20 + 4*i`; limiar crítico: `TM + 0x60 + 4*i`; status: `TM + 0xa0 + 4*i`;
- bit de máscara inferior `i`, bit superior `i+16`, bit crítico `i`;
- todas as referências ficam dentro da janela TM `0x4a9000–0x4a9fff` e são consistentes com os `REG_FIELD_FOR_EACH_SENSOR16` e `REG_FIELD_SPLIT_BITS_{0_15,16_31}` do 5.15;
- **ID0 e ID16** são rejeitados pelo modelo do stock C100, ainda que o genérico 5.15 permita 0–15.

**Risco de port em C:** o doador 3.18 usa `1 << (sensor_hw_num + 16)` para máscara upper. Para ID15, isso desloca um literal `int` assinado para o bit31; copiar a expressão literalmente para código novo pode produzir comportamento indefinido em C. Qualquer implementação eventual deve tratar as máscaras como **u32** e ser testada; não foi criado código que escreva nesses registradores.

## 4. Zonas térmicas da CPU: verificação no DTB, não só no DTS

Ambos os DTBs candidatos contêm oito `/thermal-zones/cpuN-thermal`, todos apontando ao phandle do controlador TSENS. O verificador confere a propriedade binária `thermal-sensors` e as oito zonas:

| CPU | Sensor hardware ID |
|---|---:|
| CPU0 | 9 |
| CPU1 | 10 |
| CPU2 | 11 |
| CPU3 | 12 |
| CPU4 | 4 |
| CPU5 | 5 |
| CPU6 | 6 |
| CPU7 | 7 |

Em cada zona o candidato declara trip passivo **80.000 m°C** e crítico **100.000 m°C**, ambos com histerese **2.000 m°C**. O script **preserva esses valores no gate binário**, mas não afirma que são limites seguros do stock nem que uma medição correta chega à zona. Não modificar ou ativar esses limiares antes de validar o sensor real.

## 5. Unidades e EEPROM continuam sem validação

- O TYPE3 3.18 lê 12 bits signed com bit de sinal `0x800`, valida status no bit21 e retorna valor convertido por extensão de sinal, mas sua API térmica histórica recebe `unsigned long`. O 5.15 interpreta campo v2 como deci°C e produz m°C multiplicando por 100. O contrato de unidade e os limites precisos ainda precisam de prova independente.
- `TSENS_CALIB_FUSE_MAP_NONE` no match vendor 3.18 significa ausência de uma rotina conhecida de leitura dos mapas de fuse para essa compatibilidade; **não comprova que o bloco EEPROM `0xa4000` seja dispensável**.
- As fontes mostram os mesmos offsets básicos dos dois IRQs, mas inicialização SROT, estado de hardware, read-modify-write, máscaras e software térmico **não foram ensaiados em runtime**.

## 6. Portas de teste (sem boot)

Workflow `.github/workflows/deen-c100-tsens-type3-register-zone.yml`:
1. Faz checkout imutável do próprio PR e do **doador 3.18 público fixado pelo SHA**, apenas para ler `msm-tsens.c`; a ausência/mudança de fonte quebra o gate.
2. Roda os novos testes negativos e regressões dos PRs anteriores.
3. Compila objetos TSENS AArch64 existentes e os DTBs PVT1/C100 e PVT2/C200 sem Image, sem boot.img e sem ZIP flashável.
4. Usa `dtschema==2024.2`, preserva **11 diagnósticos** por DTB e exige SHA-256 iguais ao PR #9.
5. Confere 11 pares de registradores, 15 IDs, máscaras e **oito zonas térmicas** com referências e valores de trip inalterados.
6. Publica logs, JSON, DTBs e objetos da compilação. **PASS_HOST_SOURCE_CONTRACT_ONLY** não autoriza driver/boot/flash.

### Próxima decisão

Antes de criar um descriptor 5.15 para os 15 sensores, faltam: leitura de fonte stock FDT binário; prova da unidade da API térmica TYPE3; reconciliação de calibração EEPROM; auditoria de leitura/escrita dos limiares; verificação de qual firmware configura e habilita TSENS/SROT; e identificação dos limites térmicos stock. Se esses pontos não puderem ser sustentados, **não ligar o OF match**.

**Gates permanentes nesta branch:** `TSENS_TYPE3_PORT=HOLD`, `THERMAL_RUNTIME=HOLD`, `STOCK_FDT=HOLD`, `GLOBAL_DTB_SCHEMA=REVIEW_REQUIRED`, `FIRMWARE/BOOT/FLASH/MERGE=HOLD`.

# Deen C100/PVT1 e C200/PVT2 — correção limitada de schema RPM/RPMPD

Data: 2026-11-19. Base exata: PR #5 em `88f979bd898cf18ad5aeab2292c49fd610b95536`, que incorpora os PRs #4 (match OF RPM) e #3 (auditorias). Branch de trabalho: `fix/deen-c100-rpm-dtb-schema-20261119`.

## Evidência original (pacote DEEN de 19/11)

Os arquivos `PVT1-schema.log` e `PVT2-schema.log` originais incluídos no ZIP do projeto foram relidos diretamente, não inferidos a partir de resumos. Ambos reportam **14 diagnósticos** com `dtschema==2024.2`, dos quais precisamente dois são do escopo deste PR:

| Nó | Texto do diagnóstico | Origem |
|---|---|---|
| `rpm-requests` | `'power-controller', 'regulators', 'rpmcc' do not match any of the regexes: 'pinctrl-[0-9]+'` | `qcom,smd-rpm.yaml` |
| `power-controller` | `'clock-names', 'clocks' do not match any of the regexes: 'pinctrl-[0-9]+'` | `qcom,rpmpd.yaml` |

O texto revela que o problema não é a compatibilidade `qcom,rpm-msm8953`, corrigida no **driver** pelo PR #4. São regras de schema que não reconhecem filhos ou propriedades do Device Tree.

O DTB compilado possui em `/smd/rpm/rpm-requests` exatamente três filhos diretos: `rpmcc`, `power-controller`, `regulators`. O driver `qcom_smd_rpm_probe()`, em `drivers/soc/qcom/smd-rpm.c`, chama `of_platform_populate()` para criar os dispositivos filhos, e os drivers `clk-smd-rpm.c`, `rpmpd.c` e `qcom_smd-regulator.c` contêm as respectivas compatibilidades. **Remover esses filhos apagaria consumidores necessários à configuração e não seria uma correção aceitável.**

## Mudanças delimitadas

1. **Binding `Documentation/devicetree/bindings/soc/qcom/qcom,smd-rpm.yaml`:** declarar somente os filhos `rpmcc`, `power-controller`, `regulators` com um `patternProperties` ancorado e `type: object`. **Preservar `additionalProperties: false`**: o binding continua rejeitando nós arbitrários. Cada filho com seu `compatible` continua sujeito a seus próprios bindings.
2. **Override `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi`:** remover `clocks` e `clock-names` herdados do nó `&rpmpd` somente para Deen. O driver ACK 5.15 `drivers/soc/qcom/rpmpd.c` recebe o handle RPM por `dev_get_drvdata(pdev->dev.parent)`; não faz `clk_get()` / `devm_clk_get()` nem habilitação de clock. Essas propriedades não são requeridas por `qcom,rpmpd.yaml`.
3. **Não modificar** `arch/arm64/boot/dts/qcom/msm8953.dtsi`, importado do SoC de upstream, nem driver, IRQ, SRAM, SMEM, memória reservada, regulators, clocks do nó `rpmcc`, OPPs, power domains ou firmware.

A ausência de uso por este driver comprova apenas que as propriedades de referência do nó RPMPD são **desnecessárias para a sua rotina de probe atual**; não demonstra que a plataforma inteira inicializa.

## Testes reproduzíveis e critério estrito

Workflow `.github/workflows/deen-c100-rpm-dtb-schema-scope.yml`:

- Executar testes unitários do novo gate e os testes anteriores do PR #4.
- Compilar **ambos** DTBs arm64 e os objetos `drivers/soc/qcom/smd-rpm.o`, `drivers/soc/qcom/rpmpd.o` (sem gerar Image, boot.img ou ZIP flashável).
- Validar os YAMLs `qcom,smd-rpm.yaml` e `qcom,rpmpd.yaml` por `dt-doc-validate` com dtschema **2024.2**.
- Executar `dt-mk-schema` em **todos os bindings** e `dt-validate` em ambos DTBs, arquivando **todos** os logs brutos.
- `scripts/deen_c100_rpm_schema_gate.py` só declara `PASS_RPM_SCHEMA_ONLY` se os diagnósticos `rpm-requests` e `power-controller` estiverem ausentes, identidades C100/C200 e os subnós/propriedades funcionais forem preservados, e **os outros 12 diagnósticos** por DTB mantiverem o inventário conhecido.

### Diagnósticos esperados fora do escopo (12 por DTB, continuam REVIEW_REQUIRED)

| Nó | Quantidade | Motivo ainda pendente |
|---|---:|---|
| `/` | 1 | nó de memória placeholder |
| `thermal-sensor@4a9000` | 1 | TSENS/compatibilidade |
| `clock-controller@1800000` | 1 | GCC clock names |
| `spmi@200f000` | 1 | enumeração `reg` |
| `rtc@6000` | 2 | `reg` e `reg-names` |
| `usb@70f8800` | 5 | compatible, clocks e IRQs |
| `mailbox@b011000` | 1 | sequência de `compatible` |

**Observação:** esses 12 continuam sendo *erros* de schema; não são aceitos como `DTB_SCHEMA_PASS`. Se aparecer um diagnóstico novo, se um dos 2 corrigidos persistir, ou se um dos 12 mudar, o CI falha por desvio de baseline. Isso não autoriza modificar valores de hardware para ajustar o número artificialmente.

## Gates explicitamente mantidos em HOLD

- Inicialização de SMEM pelo SBL, versão/partições do cabeçalho, posse de hwspinlock.
- Sinal de doorbell APCS, IRQ 168, anúncio real do canal SMD `rpm_requests` e ACK de mensagens RPM.
- Equivalência física da região stock `other_ext_region`, QSEE, SMEM, partições de memória e firmware/vendor.
- TSENS TYPE3, DTB/schema global, defconfig Deen, kernel, AOSPA Android 14 e boot.
- Merge e qualquer flash ou habilitação de modem, ADSP, WCNSS ou SMP2P.

**O verde do workflow, quando obtido, significa apenas schema RPM corrigido em host.**

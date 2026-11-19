# Motorola One Deen — conciliação binária STOCK C100/C200 × ACK 5.15

Data: **19/11/2026**. Fonte original fornecida pelo usuário: `Deen_Boot_B_Audit.zip`, contendo `boot_b-original.img`, `dto_b-original.img`, `SHA256SUMS.txt` e `RELATORIO.txt`. A inspeção é **read-only** no computador/ambiente de análise. **A imagem boot, os FDTs brutos e o arquivo ZIP do usuário NÃO são incluídos no repositório ou no GitHub Actions.**

Base de revisão: [PR #18](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/18); segue a [issue #19](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/19), o TSENS [#8](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/8) e o contrato APCS/SMSM [#14](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/14).

## 1. Cadeia de evidência e leitura direta

O `SHA256SUMS.txt` do arquivo enviado foi verificado com `sha256sum -c`:

| Item | Tamanho | SHA256 verificado |
|---|---:|---|
| `boot_b-original.img` | 67.108.864 bytes | `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765` |
| `dto_b-original.img` | 16.777.216 bytes | `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e` |

O parser FDT local examinou todos os 64 MiB e validou **sete FDTs**, sem sobreposição de seus intervalos. Os FDTs identificados pelo valor real `qcom,board-id`:

| Variante | Offset no boot | FDT SHA256 individual | Tamanho | Nós |
|---|---:|---|---:|---:|
| C100/PVT1 | `0x00b7820a` | `537dc8c3f0a75fbe0b27d8d32b067c7efa8472dccd86b33698700e7e4022408a` | 253.704 | 1.471 |
| C200/PVT2 | `0x00abe4f6` | `f1bd9bb41f203ebb443b79bfd38564e6203fb858be3d53d8ad132792952c9a16` | 253.704 | 1.471 |

Ambos contêm `qcom,msm-id = <0x125 0>`. Ao comparar **todas** as propriedades do FDT stock C100 e do stock C200, a única propriedade que diferiu foi **`/qcom,board-id`**. Isso não é prova de que os dois hardwares sejam idênticos em runtime.

Os DTBs **candidatos** foram lidos de um artefato GitHub Actions do [PR #15](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/15): PVT1 23.996 bytes, SHA256 `fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a`; PVT2 23.964 bytes, SHA256 `9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05`. Cada DTB candidato tem **249 nós**, contra 1.471 de cada stock.

**Limitação do CI GitHub:** como o `boot_b-original.img` não está versionado, os CI reconstroem os dois DTBs candidatos e comparam a saída com **um manifesto derivado e hash-pinned**. O CI deve dizer `PASS_REFERENCE_ONLY_STOCK_DIRECT_NOT_RECHECKED_IN_CI`, **nunca** fingir que releu o stock. A leitura direta do stock só pode ser reproduzida localmente quando o original é fornecido explicitamente ao script com `--stock-boot`. O script verifica o SHA completo antes de usar os FDTs.

## 2. Descoberta principal: mesmo registro/bit, DTs com modelos diferentes

No FDT stock existe `/soc/clock-controller@b011000`, `compatible = "qcom,8953-l2ccc"`, `reg=<0x0b011000 0x1000>`. Seu `/soc/qcom,smem@86300000` possui `reg-names="smem","irq-reg-base","aux-mem1","smem_targ_info_reg"`. A janela `irq-reg-base` começa em **`0x0b011008`** com tamanho quatro bytes.

Já o candidato 5.15 descreve `/soc@0/mailbox@b011000`, `compatible = "qcom,msm8953-apcs-kpss-global","syscon"`, `reg=<0x0b011000 0x1000>`. O mesmo endereço-base é identificado por drivers/bindings **diferentes**, o que exige revisão de arbitragem/uso do bloco: não constitui, isoladamente, uma colisão funcional comprovada.

Os sete canais stock residem **dentro** do nó SMEM:

| Função stock | SMD edge | SPI | Máscara stock | Bit |
|---|---:|---:|---:|---:|
| SMD RPM | 15 | 168 | `0x00000001` | 0 |
| SMD modem | 0 | 25 | `0x00001000` | 12 |
| SMSM modem | 0 | 26 | `0x00002000` | 13 |
| SMD WCNSS | 6 | 142 | `0x00020000` | 17 |
| SMSM WCNSS | 6 | 144 | `0x00080000` | 19 |
| SMD ADSP | 1 | 289 | `0x00000100` | 8 |
| SMSM ADSP | 1 | 290 | `0x00000200` | 9 |

Em todos esses sete canais, `qcom,*-irq-offset=<0>` aplica-se ao `irq-reg-base` stock `0x0b011008`. O stock **não** contém as propriedades `qcom,ipc`, `qcom,ipc-1` e `qcom,ipc-3` usadas pela descrição 5.15.

O candidato 5.15 contém somente o SMD edge 15 (`/smd/rpm`, SPI 168) e o SMSM raiz com três referências ao syscon via as tuplas `qcom,ipc=<&apcs 8 0>`, `qcom,ipc-1=<&apcs 8 13>` e `qcom,ipc-3=<&apcs 8 19>`. Como a janela syscon começa em `0x0b011000`, todas atingem o endereço físico **`0x0b011008`**.

**Correspondências numéricas diretamente verificadas:**
- RPM stock: `0x0b011008`, bit **0** = candidato SMD/RPM `0x0b011008`, bit **0**.
- SMSM modem stock: `0x0b011008`, bit **13** = candidato `qcom,ipc-1` `0x0b011008`, bit **13**.
- SMSM WCNSS stock: `0x0b011008`, bit **19** = candidato `qcom,ipc-3` `0x0b011008`, bit **19**.

**Ponto em aberto:** a coincidência dos bits 13 e 19 **não comprova o mapeamento dos IDs de host** (1/modem, 3/WCNSS), a direção da interrupção, entrega ao modem ou a semântica do firmware. O stock também contém SMD modem, ADSP e WCNSS (edges 0, 1 e 6) ausentes do modelo candidato; além disso, SMSM ADSP possui bit 9 no stock, não observado como `qcom,ipc` candidato. **Não adicionar nós por cópia mecânica do stock, nem habilitar MPSS/ADSP/WCNSS/SMP2P.**

## 3. SMEM — correspondência espacial, contrato diferente

- Stock `/soc/qcom,smem@86300000`: a janela de memória principal é **`0x86300000 / 1 MiB`**, mas há mais três regiões `reg`: `irq-reg-base` `0x0b011008/4`, `aux-mem1` `0x00060000/32768` e `smem_targ_info_reg` `0x0193d000/8`, além da propriedade booleana `qcom,mpu-enabled`.
- Candidato `/smem`: referências por `memory-region` (a mesma janela principal `0x86300000/1 MiB`), `qcom,rpm-msg-ram` e `hwlocks` (mutex número 3 de `qcom,tcsr-mutex`).
- A igualdade do endereço/tamanho **não prova** que o bootloader tenha inicializado a tabela SMEM, que o driver ACK aceite a versão/posição da tabela ou que a regra de MPU e aux memory permaneça válida. **`SMEM_BOOTLOADER_LAYOUT=HOLD`**.

## 4. TSENS e SPMI — prioridade de segurança

- Stock: `/soc/tsens@4a8000`, `compatible="qcom,msm8953-tsens"`, **15 sensores (IDs 1–15)**, 15 `qcom,slope=0xc80`, janelas `0x4a8000/0x2000` e `0x0a4000/0x1000`, interrupções SPI 184 e 314.
- Candidato: `/soc@0/thermal-sensor@4a9000`, `compatible="qcom,msm8953-tsens","qcom,tsens-v2"`, **16 sensores**, janelas `0x4a9000/0x1000` e `0x4a8000/0x1000`. A semântica Type3, calibração, IRQ/threshold e temperaturas continuam sem prova.
- **SPMI:** as **cinco janelas físicas** e a sequência `"core","chnls","obsrvr","intr","cnfg"` coincidiam exatamente entre ambos os FDTs stock e os candidatos. Isso confirma apenas a geometria de recursos, não o funcionamento do PMIC ou o boot.

O contraste 15×16 reforça a razão de manter [PR #11](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/11) em draft. O [PR #17](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/17) implementa em separado somente a proteção contra acesso fora do array `hw_ids`; **não ativa o descritor térmico**.

## 5. Reprodutibilidade, sem divulgar partições brutas

- Manifesto derivado: `documentation/DEEN_STOCK_C100_C200_BINARY_REFERENCE_2026-11-19.json`. Contém hashes de origem, offsets, geometria, bits e limites de inferência; **não contém o raw boot.img ou o FDT binário**.
- Ferramenta: `scripts/deen_stock_c100_c200_binary_gate.py` — com `--stock-boot`, faz scan, verifica os sete FDTs e confronta propriedades efetivas com o manifesto; sem `--stock-boot`, testa exclusivamente candidatos contra a referência, identificando a falta de leitura direta.
- Testes negativos: `scripts/test_deen_stock_c100_c200_binary_gate.py` — corrompimento de bitmask, TSENS 15×16, hash não aceito, três bits físicos, modelo e limites; **fixtures sintéticas não são prova de stock**.
- GitHub Actions: valida os dois DTBs reconstruídos e o manifesto derivado. Não recebe a imagem de boot stock. Logs preservam `STOCK_DIRECT_IN_CI=HOLD`, `RUNTIME=HOLD`.

## 6. Decisão de integração

**Pode ser revisado como evidência:** os hashes dos FDTs originais, os 7 canais SMD/SMSM stock, as três correspondências físicas de bit, a geometria de SPMI e o problema TSENS 15×16.

**Não pode ser tratado como pronto para merge de hardware:** APCS/SMSM, SMD/RPM, bootloader SMEM, remotes modem/ADSP/WCNSS, calibração TSENS, firmware, boot.img, full defconfig e flash.

`STOCK_FDT_BINARY_READ=PASS`; `IPC_PHYSICAL_BIT_RECONCILIATION=PASS_NUMERIC_ONLY`; `SMSM_HOST_ROLE_MAPPING=HOLD`; `L2CCC_APCS_DRIVER_OWNERSHIP=HOLD`; `SMEM_ABI=HOLD`; `TSENS_TYPE3=HOLD`; `FULL_KERNEL_BOOT_FLASH_MERGE=HOLD`.

Nenhuma escrita no aparelho e nenhum merge de driver foram feitos para produzir este relatório.

/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef __CLK_CPU_MSM8953_READBACK_H
#define __CLK_CPU_MSM8953_READBACK_H

#include <linux/io.h>
#include <linux/bits.h>

static inline bool deen_apss_rate_matches(void __iomem *pll, void __iomem * const mux[3],
					 unsigned long hz)
{
	u32 user, cfg;
	int i;

	/* The stock operating points use the 19.2 MHz reference and integer L.
	 * Require early output, unity pre-divider, and the fixed 1/1/2.5 mux
	 * ratios. Reject an update in flight or a clock on an alternate parent.
	 */
	if (!hz || !(readl(pll) & BIT(31)) || hz % 19200000 ||
	    readl(pll + 0x8) != hz / 19200000)
		return false;
	user = readl(pll + 0x18);
	if (!(user & BIT(3)) || (user & (BIT(12) | BIT(24))))
		return false;
	for (i = 0; i < 3; i++) {
		cfg = readl(mux[i] + 4);
		if ((readl(mux[i]) & BIT(0)) ||
		    (cfg & (GENMASK(10, 8) | GENMASK(4, 0))) !=
		    ((5 << 8) | (i == 2 ? 4 : 1)))
			return false;
	}
	return !!(readl(pll) & BIT(31)) && readl(pll + 8) == hz / 19200000;
}

#endif

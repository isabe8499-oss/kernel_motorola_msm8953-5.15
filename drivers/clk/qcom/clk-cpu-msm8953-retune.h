/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef __CLK_CPU_MSM8953_RETUNE_H
#define __CLK_CPU_MSM8953_RETUNE_H

#include <linux/delay.h>
#include <linux/iopoll.h>
#include "clk-cpu-msm8953-readback.h"

/* MSM8953 HW FSM timing from Qualcomm clock-pll.c, variable_rate_pll_set_rate
 * and variable_rate_pll_clk_{disable,enable}_hwfsm. No mux reparenting.
 */
static inline int deen_retune_integer_pll(void __iomem *pll, void __iomem * const mux[3],
					 unsigned long hz)
{
	const unsigned long ref = 19200000;
	unsigned long old = (unsigned long)readl(pll + 8) * ref;
	u32 mode;
	int ret;

	if (hz < 652800000 || hz > 2208000000UL || hz % ref)
		return -EINVAL;
	if (!deen_apss_rate_matches(pll, mux, old))
		return -EIO;
	udelay(1);
	writel(hz / ref, pll + 8);
	readl(pll + 8);
	udelay(50);
	ret = readl_poll_timeout_atomic(pll, mode, mode & BIT(31), 1, 200);
	if (ret)
		return ret;
	return deen_apss_rate_matches(pll, mux, hz) ? 0 : -EIO;
}
#endif

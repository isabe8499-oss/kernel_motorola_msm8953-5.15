/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef __CLK_CPU_MSM8953_H
#define __CLK_CPU_MSM8953_H

#include <linux/mutex.h>
#include <linux/types.h>

struct clk;
struct device;
struct device_node;
struct regulator;

/* Deen's CPR4 apc_corner regulator accepts selectors 1 through 9. */
#define DEEN_MAX_CORNERS	9

struct msm8953_cpuclk_level {
	u32 cpu_hz;
	u32 cci_hz;
	u32 corner;
};

struct msm8953_cpuclk_plan {
	struct msm8953_cpuclk_level levels[DEEN_MAX_CORNERS];
	unsigned int count;
	unsigned int bin;
};

/* One instance per shared PLL. The owner holds enabled clock and rail
 * references and serializes all changes to this clock domain through it.
 */
struct msm8953_cpuclk_domain {
	struct mutex lock;
	struct msm8953_cpuclk_plan plan;
	struct clk *power, *perf, *cci;
	struct regulator *apc;
};

int msm8953_cpuclk_read_plan(const struct device_node *np, unsigned int bin,
			     struct msm8953_cpuclk_plan *plan);
int msm8953_cpuclk_domain_init(struct msm8953_cpuclk_domain *d,
			       struct device *dev, unsigned int hw_bin,
			       struct clk *power, struct clk *perf, struct clk *cci,
			       struct regulator *apc);
int msm8953_cpuclk_set_rate(struct msm8953_cpuclk_domain *domain,
			    unsigned long cpu_hz);

#endif

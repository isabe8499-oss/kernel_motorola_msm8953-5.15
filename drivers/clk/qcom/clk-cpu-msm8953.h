/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef __CLK_CPU_MSM8953_H
#define __CLK_CPU_MSM8953_H

#include <linux/mutex.h>
#include <linux/types.h>

#define DEEN_POWER_CLK	0x2e6af930
#define DEEN_PERF_CLK	0xa0a0dc7f
#define DEEN_CCI_CLK	0x96854074

struct clk;
struct device;
struct device_node;
struct platform_device;
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
	struct device *dev;
	struct msm8953_cpuclk_plan plan;
	struct clk *power, *perf, *cci;
	struct regulator *apc;
	u64 verified_up, verified_down;
	int (*program)(struct msm8953_cpuclk_domain *d, unsigned long hz);
	void (*record_transition)(struct msm8953_cpuclk_domain *d, bool up);
	bool (*verify_rate)(struct msm8953_cpuclk_domain *d, unsigned long hz);
};

bool deen_is_c100(void);
int deen_apss_program(struct msm8953_cpuclk_domain *d, unsigned long hz);
void __iomem *deen_read_window(struct device *dev, struct platform_device *supplier,
			     const char *name, size_t size);
bool msm8953_cpuclk_has_cpr4(struct device_node *np);
int msm8953_cpuclk_check_resources(struct platform_device *pdev);
unsigned int msm8953_cpuclk_speed_bin(u32 efuse_value);
int msm8953_cpuclk_read_plan(const struct device_node *np, unsigned int bin,
			     struct msm8953_cpuclk_plan *plan);
int msm8953_cpuclk_domain_init(struct msm8953_cpuclk_domain *d,
			       struct device *dev, unsigned int hw_bin,
			       struct clk *power, struct clk *perf, struct clk *cci,
			       struct regulator *apc);
int msm8953_cpuclk_set_rate(struct msm8953_cpuclk_domain *domain,
			    unsigned long cpu_hz);

int msm8953_cpuclk_register_cpufreq(struct device *dev,
				    struct msm8953_cpuclk_domain *d,
				    const struct device_node *np);

#endif

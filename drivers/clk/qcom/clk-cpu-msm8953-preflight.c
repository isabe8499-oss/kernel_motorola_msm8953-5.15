// SPDX-License-Identifier: GPL-2.0-only
/*
 * Motorola One / MSM8953 CPU clock port: compile-only resource preflight.
 *
 * The original 3.18 driver controls A53 power/performance, CCI, PLL and
 * regulator voltage tables. These helpers validate the source resource
 * contract and speed-bin metadata, but do NOT register a clock provider,
 * request or write MMIO, alter voltages, change PLL rates, or bind a DT node.
 *
 * Deliberately guarded by COMPILE_TEST until CPU/CCI sequencing and thermal
 * safety are proven. Never enable this as a functional clock driver.
 */
#include <linux/errno.h>
#include <linux/ioport.h>
#include <linux/kernel.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/types.h>

struct msm8953_cpuclk_resource {
	const char *name;
	resource_size_t minimum_size;
};

static const struct msm8953_cpuclk_resource msm8953_cpuclk_resources[] = {
	{ "rcgwr-c0-base", 0x68 },
	{ "rcgwr-c1-base", 0x68 },
	{ "c0-pll", 0x400 },
	{ "c0-mux", 0x8 },
	{ "c1-mux", 0x8 },
	{ "cci-mux", 0x8 },
	{ "efuse", 0x8 },
};

/* No mapping of these resources or register accesses is performed here. */
int msm8953_cpuclk_check_resources(struct platform_device *pdev)
{
	struct resource *res;
	unsigned int i, j;

	for (i = 0; i < ARRAY_SIZE(msm8953_cpuclk_resources); i++) {
		res = platform_get_resource_byname(pdev, IORESOURCE_MEM,
						  msm8953_cpuclk_resources[i].name);
		if (!res || res->end < res->start ||
		    resource_size(res) < msm8953_cpuclk_resources[i].minimum_size)
			return -EINVAL;

		/* The source lists seven non-overlapping windows. */
		for (j = 0; j < i; j++) {
			struct resource *prev;

			prev = platform_get_resource_byname(pdev, IORESOURCE_MEM,
					msm8953_cpuclk_resources[j].name);
			if (!prev)
				return -EINVAL;
			if (res->start <= prev->end && prev->start <= res->end)
				return -EINVAL;
		}
	}

	return 0;
}

/* Original 3.18 clock-cpu-8953.c: speed bin = efuse bits [10:8]. */
unsigned int msm8953_cpuclk_speed_bin(u32 efuse_value)
{
	return (efuse_value >> 8) & 0x7;
}

/*
 * Validate the shape of speed-bin voltage/frequency pairs before a future
 * port consumes them. No OPPs or regulators are changed by this helper.
 */
int msm8953_cpuclk_check_speed_bin_table(const struct device_node *np,
					 unsigned int bin, bool cci)
{
	char name[32];
	int cells;

	if (bin > 7)
		return -EINVAL;

	scnprintf(name, sizeof(name), "qcom,speed%u-bin-v0-%s",
		  bin, cci ? "cci" : "cl");
	cells = of_property_count_u32_elems(np, name);
	if (cells < 0)
		return cells;

	/* OEM pairs are frequency-Hz / microvolt values. */
	if (!cells || (cells & 1))
		return -EINVAL;

	return 0;
}

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

#include "clk-cpu-msm8953.h"

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

static int msm8953_decode_plan(const __be32 *cl, const __be32 *cci,
			       unsigned int rows, struct msm8953_cpuclk_plan *plan)
{
	unsigned int i;
	u32 last_cpu = 0, last_corner = 0;

	/* The zero row is a sentinel, not an operating point. */
	if (rows < 2 || rows > DEEN_MAX_CORNERS + 1 ||
	    cl[0] || cl[1] || cci[0] || cci[1])
		return -EINVAL;

	for (i = 1; i < rows; i++) {
		u32 cpu_hz = be32_to_cpu(cl[2 * i]);
		u32 cci_hz = be32_to_cpu(cci[2 * i]);
		u32 corner = be32_to_cpu(cl[2 * i + 1]);

		if (cpu_hz <= last_cpu || !corner || corner < last_corner ||
		    corner > DEEN_MAX_CORNERS ||
		    corner != be32_to_cpu(cci[2 * i + 1]) ||
		    (u64)cci_hz * 5 != (u64)cpu_hz * 2)
			return -EINVAL;

		plan->levels[i - 1] = (struct msm8953_cpuclk_level) {
			.cpu_hz = cpu_hz, .cci_hz = cci_hz, .corner = corner,
		};
		last_cpu = cpu_hz;
		last_corner = corner;
	}
	plan->count = rows - 1;
	return 0;
}

/*
 * Deen stores CPR corner frequencies consecutively for each silicon bin.
 * Validate the CPU clock plan against the regulator's own bin, even when
 * the clock driver selected a fallback frequency table.
 */
static int msm8953_check_cpr_corners(const struct device_node *supply,
				    unsigned int hw_bin,
				    const struct msm8953_cpuclk_plan *plan)
{
	const char *counts = "qcom,cpr-speed-bin-corners";
	const char *freqs = "qcom,corner-frequencies";
	u32 corners[8], hz;
	unsigned int offset = 0, total = 0, i;
	int ret;

	if (of_property_count_u32_elems(supply, counts) != ARRAY_SIZE(corners))
		return -EINVAL;
	ret = of_property_read_u32_array(supply, counts, corners, ARRAY_SIZE(corners));
	if (ret)
		return ret;

	for (i = 0; i < ARRAY_SIZE(corners); i++) {
		if (corners[i] > DEEN_MAX_CORNERS)
			return -EINVAL;
		if (i == hw_bin)
			offset = total;
		total += corners[i];
	}
	if (!corners[hw_bin])
		return -ENODEV;
	if (of_property_count_u32_elems(supply, freqs) != total)
		return -EINVAL;

	for (i = 0; i < plan->count; i++) {
		const struct msm8953_cpuclk_level *level = &plan->levels[i];

		if (level->corner > corners[hw_bin])
			return -EINVAL;
		ret = of_property_read_u32_index(supply, freqs,
						 offset + level->corner - 1, &hz);
		if (ret)
			return ret;
		if (hz != level->cpu_hz)
			return -EINVAL;
	}
	return 0;
}

int msm8953_cpuclk_read_plan(const struct device_node *np, unsigned int bin,
			     struct msm8953_cpuclk_plan *plan)
{
	struct msm8953_cpuclk_plan selected = {};
	const struct property *cl, *cci;
	struct device_node *supply;
	unsigned int hw_bin = bin;
	char name[32];
	int ret;

	if (!np || !plan || bin > 7)
		return -EINVAL;

	for (;;) {
		scnprintf(name, sizeof(name), "qcom,speed%u-bin-v0-cl", bin);
		cl = of_find_property(np, name, NULL);
		scnprintf(name, sizeof(name), "qcom,speed%u-bin-v0-cci", bin);
		cci = of_find_property(np, name, NULL);
		if (cl || cci || !bin)
			break;
		bin = 0;
	}
	if (!cl && !cci)
		return -ENOENT;
	if (!cl || !cci || !cl->value || !cci->value || cl->length <= 0 ||
	    cl->length != cci->length || cl->length % (2 * sizeof(__be32)))
		return -EINVAL;

	ret = msm8953_decode_plan(cl->value, cci->value,
				  cl->length / (2 * sizeof(__be32)), &selected);
	if (ret)
		return ret;
	supply = of_parse_phandle(np, "vdd-cl-supply", 0);
	if (!supply)
		return -ENODEV;
	ret = msm8953_check_cpr_corners(supply, hw_bin, &selected);
	of_node_put(supply);
	if (ret)
		return ret;

	selected.bin = bin;
	*plan = selected;
	return 0;
}

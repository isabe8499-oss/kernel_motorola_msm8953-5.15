// SPDX-License-Identifier: GPL-2.0-only
/* Shared CPU/CCI clock transition for the Deen CPR4 virtual corner rail. */
#include <linux/clk.h>
#include <linux/device.h>
#include <linux/err.h>
#include <linux/errno.h>
#include <linux/of.h>
#include <linux/kernel.h>
#include <linux/regulator/consumer.h>

#include "clk-cpu-msm8953.h"

bool msm8953_cpuclk_has_cpr4(struct device_node *np)
{
	struct device_node *supply, *thread, *ctrl;
	bool is_cpr4;

	supply = of_parse_phandle(np, "vdd-cl-supply", 0);
	if (!supply)
		return false;
	thread = of_get_parent(supply);
	ctrl = thread ? of_get_parent(thread) : NULL;
	is_cpr4 = ctrl && of_device_is_compatible(ctrl, "qcom,cpr4-msm8953-apss-regulator");
	of_node_put(ctrl);
	of_node_put(thread);
	of_node_put(supply);
	return is_cpr4;
}

/* The clock provider passes its enabled vdd-cl consumer and clock handles
 * before exposing rate changes. It owns their lifetime and the MX vote.
 */
int msm8953_cpuclk_domain_init(struct msm8953_cpuclk_domain *d,
			       struct device *dev, unsigned int hw_bin,
			       struct clk *power, struct clk *perf, struct clk *cci,
			       struct regulator *apc)
{
	int ret;

	if (!d || !dev || !dev->of_node || IS_ERR_OR_NULL(power) ||
	    IS_ERR_OR_NULL(perf) || IS_ERR_OR_NULL(cci) || IS_ERR_OR_NULL(apc))
		return -EINVAL;

	if (!msm8953_cpuclk_has_cpr4(dev->of_node))
		return -ENODEV;

	ret = msm8953_cpuclk_read_plan(dev->of_node, hw_bin, &d->plan);
	if (ret)
		return ret;

	mutex_init(&d->lock);
	d->dev = dev;
	d->verify_rate = NULL;
	d->program = NULL;
	d->verified_up = 0;
	d->verified_down = 0;
	d->power = power;
	d->perf = perf;
	d->cci = cci;
	d->apc = apc;
	return 0;
}

static const struct msm8953_cpuclk_level *
find_level(const struct msm8953_cpuclk_plan *plan, unsigned long rate)
{
	unsigned int i;

	for (i = 0; i < plan->count; i++)
		if (plan->levels[i].cpu_hz == rate)
			return &plan->levels[i];
	return NULL;
}

static bool domain_matches(struct msm8953_cpuclk_domain *d,
			   const struct msm8953_cpuclk_level *level)
{
	return (!d->verify_rate || d->verify_rate(d, level->cpu_hz)) &&
	       clk_get_rate(d->power) == level->cpu_hz &&
	       clk_get_rate(d->perf) == level->cpu_hz &&
	       clk_get_rate(d->cci) == level->cci_hz;
}

/* apc must be an enabled consumer of the CPR4 virtual corner regulator.
 * Its provider lists corner N at selector N - 1. Never pass the PMIC rail.
 * The clock provider owns MX, PLL lock and low-power handshakes and must
 * report actual domain rates before a downwards corner vote is allowed.
 */
static int transition(struct msm8953_cpuclk_domain *d, unsigned long rate)
{
	const struct msm8953_cpuclk_level *old, *next;
	unsigned int corner;
	long rounded;
	int ret;

	if (!d->plan.count || d->plan.count > DEEN_MAX_CORNERS)
		return -EINVAL;
	next = find_level(&d->plan, rate);
	if (!next)
		return -EINVAL;
	old = find_level(&d->plan, clk_get_rate(d->power));
	if (!old || !domain_matches(d, old))
		return -EIO;

	ret = regulator_is_enabled(d->apc);
	if (ret <= 0)
		return ret ? ret : -ENODEV;
	corner = max(old->corner, next->corner);
	if (!next->corner || !old->corner || corner > DEEN_MAX_CORNERS)
		return -EINVAL;
	ret = regulator_list_voltage(d->apc, corner - 1);
	if (ret < 0 || ret != corner)
		return ret < 0 ? ret : -EINVAL;
	ret = regulator_list_voltage(d->apc, next->corner - 1);
	if (ret < 0 || ret != next->corner)
		return ret < 0 ? ret : -EINVAL;
	rounded = clk_round_rate(d->power, rate);
	if (rounded < 0 || rounded != rate)
		return rounded < 0 ? rounded : -EINVAL;

	ret = regulator_set_voltage(d->apc, corner, DEEN_MAX_CORNERS);
	if (ret)
		return ret;
	ret = regulator_get_voltage(d->apc);
	if (ret < 0)
		return ret;
	if (ret < corner || ret > DEEN_MAX_CORNERS)
		return -EIO;
	if (old != next) {
		ret = d->program ? d->program(d, rate) : clk_set_rate(d->power, rate);
		if (ret)
			return ret;
	}
	if (!domain_matches(d, next))
		return -EIO;
	if (corner != next->corner) {
		int actual;

		ret = regulator_set_voltage(d->apc, next->corner, DEEN_MAX_CORNERS);
		actual = regulator_get_voltage(d->apc);
		if (actual < 0)
			return actual;
		if (actual < next->corner || actual > DEEN_MAX_CORNERS)
			return ret ? ret : -EIO;
		if (ret)
			dev_warn_ratelimited(d->dev,
					     "CPR4 kept corner %d at %lu Hz (release error %d)\n",
					     actual, rate, ret);
	}
	if (d->verify_rate && old != next) {
		if (next->cpu_hz > old->cpu_hz)
			d->verified_up++;
		else
			d->verified_down++;
	}
	return 0;
}

int msm8953_cpuclk_set_rate(struct msm8953_cpuclk_domain *domain,
			    unsigned long cpu_hz)
{
	int ret;

	if (!domain || !domain->power || !domain->perf || !domain->cci ||
	    !domain->apc)
		return -EINVAL;
	mutex_lock(&domain->lock);
	ret = transition(domain, cpu_hz);
	mutex_unlock(&domain->lock);
	return ret;
}

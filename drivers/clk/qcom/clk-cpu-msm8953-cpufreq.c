// SPDX-License-Identifier: GPL-2.0-only
/* CPUFreq consumer for the Deen shared A53/CCI clock and CPR4 domain. */
#include <linux/clk.h>
#include <linux/cpufreq.h>
#include <linux/device.h>
#include <linux/of.h>
#include <linux/kernel.h>
#include <linux/slab.h>

#include "clk-cpu-msm8953.h"

struct deen_cpufreq {
	struct cpufreq_driver driver;
	struct msm8953_cpuclk_domain *domain;
	struct cpufreq_frequency_table table[DEEN_MAX_CORNERS + 1];
	unsigned int count;
};

static unsigned int deen_get(unsigned int cpu)
{
	struct deen_cpufreq *df = cpufreq_get_driver_data();

	return clk_get_rate(df->domain->power) / 1000;
}

static int deen_target_index(struct cpufreq_policy *policy, unsigned int index)
{
	struct deen_cpufreq *df = policy->driver_data;

	if (index >= df->count)
		return -EINVAL;
	return msm8953_cpuclk_set_rate(df->domain,
				       df->table[index].frequency * 1000UL);
}

static int deen_policy_init(struct cpufreq_policy *policy)
{
	struct deen_cpufreq *df = cpufreq_get_driver_data();
	struct msm8953_cpuclk_domain *d = df->domain;
	unsigned long rate = clk_get_rate(d->power);
	unsigned int i;
	int ret;

	for (i = 0; i < df->count; i++)
		if (df->table[i].frequency * 1000UL == rate)
			break;
	if (i == df->count)
		return -ERANGE;
	/* Establish our own corner vote and check both clusters and CCI. */
	ret = msm8953_cpuclk_set_rate(d, rate);
	if (ret)
		return ret;
	policy->driver_data = df;
	cpufreq_generic_init(policy, df->table, CPUFREQ_ETERNAL);
	return 0;
}

static const struct cpufreq_driver deen_driver = {
	.name = "deen-cpr4",
	.flags = CPUFREQ_IS_COOLING_DEV,
	.init = deen_policy_init,
	.get = deen_get,
	.verify = cpufreq_generic_frequency_table_verify,
	.target_index = deen_target_index,
	.attr = cpufreq_generic_attr,
};

static int build_table(struct deen_cpufreq *df, const struct device_node *np)
{
	const struct msm8953_cpuclk_plan *plan = &df->domain->plan;
	const char *prop = "qcom,cpufreq-table";
	u32 khz, maximum, previous = 0;
	unsigned int j;
	int i, count;
	long rate;

	count = of_property_count_u32_elems(np, prop);
	if (count <= 0 || of_property_read_u32_index(np, prop, count - 1, &maximum))
		return -EINVAL;
	for (i = 0; i < count; i++) {
		if (of_property_read_u32_index(np, prop, i, &khz) || khz <= previous)
			return -EINVAL;
		previous = khz;
		rate = clk_round_rate(df->domain->power, khz * 1000UL);
		if (rate == -ERANGE || rate == -EINVAL)
			continue;
		if (rate < 0)
			return rate;
		if (rate > maximum * 1000UL || rate % 1000)
			continue;
		for (j = 0; j < plan->count; j++)
			if (plan->levels[j].cpu_hz == rate)
				break;
		if (j == plan->count)
			continue;
		khz = rate / 1000;
		if (df->count && khz <= df->table[df->count - 1].frequency)
			continue;
		df->table[df->count++].frequency = khz;
	}
	df->table[df->count].frequency = CPUFREQ_TABLE_END;
	return df->count ? 0 : -ERANGE;
}

/* All eight cpuN_clk entries on Deen name one shared provider and clock. */
static int check_cpu_clocks(const struct device_node *np,
			    const struct device_node *provider)
{
	struct of_phandle_args clock;
	unsigned int cpu, first_id = 0;
	char name[16];
	int index, ret;

	for (cpu = 0; cpu < 8; cpu++) {
		scnprintf(name, sizeof(name), "cpu%u_clk", cpu);
		index = of_property_match_string(np, "clock-names", name);
		if (index < 0)
			return index;
		ret = of_parse_phandle_with_args(np, "clocks", "#clock-cells",
						 index, &clock);
		if (ret)
			return ret;
		ret = clock.np == provider && clock.args_count == 1 &&
		      (!cpu || clock.args[0] == first_id) ? 0 : -EINVAL;
		if (!cpu && !ret)
			first_id = clock.args[0];
		of_node_put(clock.np);
		if (ret)
			return ret;
	}
	return 0;
}

static void deen_unregister(void *data)
{
	struct deen_cpufreq *df = data;

	cpufreq_unregister_driver(&df->driver);
}

/* Called by the owner only after the PLL, MX and CPR4 providers are ready.
 * Register last so devres unregisters CPUFreq before releasing the domain.
 */
int msm8953_cpuclk_register_cpufreq(struct device *dev,
				    struct msm8953_cpuclk_domain *d,
				    const struct device_node *np)
{
	struct deen_cpufreq *df;
	int ret;

	if (!dev || !d || !d->dev || !d->dev->of_node ||
	    !d->power || !d->plan.count ||
	    d->plan.count > DEEN_MAX_CORNERS || !np ||
	    !of_machine_is_compatible("qcom,msm8953-deen") ||
	    !of_device_is_available(np) ||
	    !of_device_is_compatible(np, "qcom,msm-cpufreq"))
		return -EINVAL;
	ret = check_cpu_clocks(np, d->dev->of_node);
	if (ret)
		return ret;
	df = devm_kzalloc(dev, sizeof(*df), GFP_KERNEL);
	if (!df)
		return -ENOMEM;
	df->domain = d;
	df->driver = deen_driver;
	df->driver.driver_data = df;
	ret = build_table(df, np);
	if (ret)
		return ret;
	ret = cpufreq_register_driver(&df->driver);
	if (ret)
		return ret;
	return devm_add_action_or_reset(dev, deen_unregister, df);
}

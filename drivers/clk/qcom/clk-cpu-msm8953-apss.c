// SPDX-License-Identifier: GPL-2.0-only
/* Motorola Deen C100 APSS integer PLL, taking over a running OEM clock tree. */
#include <linux/clk.h>
#include <linux/clk-provider.h>
#include <linux/cpu.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/pm_qos.h>
#include <linux/regulator/consumer.h>
#include <linux/sched.h>
#include <linux/slab.h>
#include <linux/smp.h>

#include "clk-cpu-msm8953.h"
#include "clk-cpu-msm8953-retune.h"

#define XO_HZ 19200000UL

struct deen_apss;
struct deen_output {
	struct clk_hw hw;
	struct deen_apss *apss;
	unsigned int id;
};

struct deen_apss {
	void __iomem *pll;
	void __iomem *mux[3];
	struct deen_output outputs[3];
	struct msm8953_cpuclk_plan plan;
	struct regulator *mx;
	struct task_struct *writer;
	unsigned long requested;
	bool fault;
	int result;
};

static unsigned long deen_apss_rate(struct deen_apss *a)
{
	unsigned long rate = (unsigned long)readl(a->pll + 8) * XO_HZ;

	if (READ_ONCE(a->fault) || !deen_apss_rate_matches(a->pll, a->mux, rate))
		return 0;
	return rate;
}

static unsigned long deen_recalc(struct clk_hw *hw, unsigned long parent_rate)
{
	struct deen_output *o = container_of(hw, struct deen_output, hw);
	unsigned long cpu = deen_apss_rate(o->apss);

	return o->id == DEEN_CCI_CLK ? cpu * 2 / 5 : cpu;
}

static long deen_round(struct clk_hw *hw, unsigned long hz, unsigned long *parent)
{
	struct deen_output *o = container_of(hw, struct deen_output, hw);
	const struct msm8953_cpuclk_plan *plan = &o->apss->plan;
	unsigned int i;

	for (i = 0; i < plan->count; i++)
		if (plan->levels[i].cpu_hz >= hz)
			return plan->levels[i].cpu_hz;
	return -ERANGE;
}

/* Qualcomm MSM8953 variable-rate HW FSM changes the integer L only. The
 * early output and all three HID dividers stay in their boot configuration.
 * The CPUFreq transaction has already obtained and checked the CPR4 vote.
 */
static int deen_set_pll(struct clk_hw *hw, unsigned long hz, unsigned long parent)
{
	struct deen_output *o = container_of(hw, struct deen_output, hw);
	struct deen_apss *a = o->apss;
	int ret;

	if (READ_ONCE(a->writer) != current || hz != READ_ONCE(a->requested))
		return -EPERM;
	if (READ_ONCE(a->fault) || deen_round(hw, hz, &parent) != hz) {
		a->result = -EIO;
		return -EIO;
	}
	ret = deen_retune_integer_pll(a->pll, a->mux, hz);
	if (ret)
		WRITE_ONCE(a->fault, true);
	a->result = ret;
	return ret;
}

static const struct clk_ops deen_power_ops = {
	.recalc_rate = deen_recalc,
	.round_rate = deen_round,
	.set_rate = deen_set_pll,
};

static const struct clk_ops deen_monitor_ops = {
	.recalc_rate = deen_recalc,
};

static struct clk_hw *deen_of_clock(struct of_phandle_args *args, void *data)
{
	struct deen_apss *a = data;
	unsigned int i;

	if (args->args_count == 1)
		for (i = 0; i < ARRAY_SIZE(a->outputs); i++)
			if (args->args[0] == a->outputs[i].id)
				return &a->outputs[i].hw;
	return ERR_PTR(-EINVAL);
}

static void deen_disable_mx(void *arg)
{
	regulator_disable(arg);
}

static int deen_pin_mx(struct device *dev, struct deen_apss *a)
{
	struct device_node *np = of_parse_phandle(dev->of_node, "vdd-mx-supply", 0);
	bool levels;
	int ret;

	if (!np)
		return -ENODEV;
	levels = of_device_is_compatible(np, "qcom,rpm-smd-regulator") &&
		 of_property_read_bool(np, "qcom,use-voltage-level");
	of_node_put(np);
	if (!levels)
		return -EINVAL;
	a->mx = devm_regulator_get_optional(dev, "vdd-mx");
	if (IS_ERR(a->mx))
		return PTR_ERR(a->mx);
	/* OEM SVS vote covers the entire Deen PLL range. These are RPM levels. */
	ret = regulator_set_voltage(a->mx, 128, 384);
	if (ret)
		return ret;
	ret = regulator_enable(a->mx);
	if (ret)
		return ret;
	return devm_add_action_or_reset(dev, deen_disable_mx, a->mx);
}

static int deen_apss_probe(struct platform_device *pdev)
{
	static const char * const mux_names[] = {"c0-mux", "c1-mux", "cci-mux"};
	static const char * const names[] = {"deen-a53-power", "deen-a53-perf", "deen-cci"};
	static const u32 ids[] = {DEEN_POWER_CLK, DEEN_PERF_CLK, DEEN_CCI_CLK};
	struct device *dev = &pdev->dev;
	struct deen_apss *a;
	struct clk *xo;
	void __iomem *fuse;
	unsigned int bin, i;
	int ret;

	if (!deen_is_c100() || !msm8953_cpuclk_has_cpr4(dev->of_node))
		return -ENODEV;
	ret = msm8953_cpuclk_check_resources(pdev);
	if (ret)
		return ret;
	a = devm_kzalloc(dev, sizeof(*a), GFP_KERNEL);
	if (!a)
		return -ENOMEM;
	xo = devm_clk_get(dev, "xo_a");
	if (IS_ERR(xo))
		return PTR_ERR(xo);
	if (clk_get_rate(xo) != XO_HZ)
		return -EINVAL;
	a->pll = devm_platform_ioremap_resource_byname(pdev, "c0-pll");
	if (IS_ERR(a->pll))
		return PTR_ERR(a->pll);
	for (i = 0; i < ARRAY_SIZE(mux_names); i++) {
		a->mux[i] = deen_read_window(dev, pdev, mux_names[i], 8);
		if (IS_ERR(a->mux[i]))
			return PTR_ERR(a->mux[i]);
	}
	fuse = deen_read_window(dev, pdev, "efuse", 4);
	if (IS_ERR(fuse))
		return PTR_ERR(fuse);
	bin = msm8953_cpuclk_speed_bin(readl(fuse));
	ret = msm8953_cpuclk_read_plan(dev->of_node, bin, &a->plan);
	if (ret)
		return ret;
	if (!deen_apss_rate(a))
		return -EIO;
	ret = deen_pin_mx(dev, a);
	if (ret)
		return ret;
	for (i = 0; i < ARRAY_SIZE(a->outputs); i++) {
		struct clk_init_data init = {
			.name = names[i],
			.ops = i ? &deen_monitor_ops : &deen_power_ops,
			.flags = CLK_GET_RATE_NOCACHE,
		};

		a->outputs[i].id = ids[i];
		a->outputs[i].apss = a;
		a->outputs[i].hw.init = &init;
		ret = devm_clk_hw_register(dev, &a->outputs[i].hw);
		if (ret)
			return ret;
	}
	dev_set_drvdata(dev, a);
	return devm_of_clk_add_hw_provider(dev, deen_of_clock, a);
}

static const struct of_device_id deen_apss_match[] = {
	{ .compatible = "qcom,cpu-clock-8953" },
	{}
};

static struct platform_driver deen_apss_driver = {
	.probe = deen_apss_probe,
	.driver = { .name = "deen-apss", .of_match_table = deen_apss_match,
		    .suppress_bind_attrs = true },
};
builtin_platform_driver(deen_apss_driver);

static void deen_wake_cpu(void *unused) {}

int deen_apss_program(struct msm8953_cpuclk_domain *d, unsigned long hz)
{
	struct deen_apss *a = dev_get_drvdata(d->dev);
	struct pm_qos_request qos = {};
	int ret;

	if (d->dev->driver != &deen_apss_driver.driver)
		return -ENODEV;
	if (!cpus_read_trylock())
		return -EBUSY;
	/* A cluster with no online CPU cannot acknowledge a wakeup. */
	if (!cpu_online(0) || nr_cpu_ids < 8 || !cpu_online(4)) {
		cpus_read_unlock();
		return -EBUSY;
	}
	cpu_latency_qos_add_request(&qos, 0);
	on_each_cpu(deen_wake_cpu, NULL, 1);
	a->result = -EIO;
	WRITE_ONCE(a->requested, hz);
	WRITE_ONCE(a->writer, current);
	ret = clk_set_rate(d->power, hz);
	WRITE_ONCE(a->writer, NULL);
	cpu_latency_qos_remove_request(&qos);
	cpus_read_unlock();
	return ret ? ret : a->result;
}

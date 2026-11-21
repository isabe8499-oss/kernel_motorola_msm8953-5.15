// SPDX-License-Identifier: GPL-2.0-only
/* Connect the stock C100 CPUFreq node to its APSS clock and CPR4 providers. */
#include <linux/clk.h>
#include <linux/device.h>
#include <linux/io.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_platform.h>
#include <linux/platform_device.h>
#include <linux/regulator/consumer.h>
#include <linux/slab.h>

#include "clk-cpu-msm8953.h"
#include "clk-cpu-msm8953-readback.h"

#define DEEN_POWER_CLK	0x2e6af930
#define DEEN_PERF_CLK	0xa0a0dc7f
#define DEEN_CCI_CLK	0x96854074

struct deen_handoff {
	struct msm8953_cpuclk_domain domain;
	void __iomem *pll;
	void __iomem *mux[3];
};

static bool deen_verify_rate(struct msm8953_cpuclk_domain *domain, unsigned long hz)
{
	struct deen_handoff *h = container_of(domain, struct deen_handoff, domain);

	return deen_apss_rate_matches(h->pll, h->mux, hz);
}

static void deen_clk_put(void *data)
{
	clk_put(data);
}

static struct clk *deen_clock(struct device *dev, struct device_node *provider, u32 id)
{
	struct of_phandle_args spec = { .np = provider, .args_count = 1, .args = {id} };
	struct clk *clk = of_clk_get_from_provider(&spec);
	int ret;

	if (IS_ERR(clk))
		return clk;
	ret = devm_add_action_or_reset(dev, deen_clk_put, clk);
	return ret ? ERR_PTR(ret) : clk;
}

static void __iomem *deen_read_window(struct device *dev, struct platform_device *supplier,
				     const char *name, size_t size)
{
	struct resource *res = platform_get_resource_byname(supplier, IORESOURCE_MEM, name);
	void __iomem *base;

	if (!res || resource_size(res) < size)
		return ERR_PTR(-EINVAL);
	/* The physical provider owns the window. This mapping is read-only. */
	base = devm_ioremap(dev, res->start, size);
	return base ? base : ERR_PTR(-ENOMEM);
}

/* Keep the last valid CPU voltage vote with the APSS supplier across policy
 * unregister and reprobe. CPUs continue running after CPUFreq goes away.
 */
static void deen_release_vote(struct device *dev, void *data)
{
	struct regulator *rail = *(struct regulator **)data;

	regulator_disable(rail);
	regulator_put(rail);
}

static struct regulator *deen_hold_vote(struct device *supplier)
{
	struct regulator **res, **held, *rail;
	int ret;

	held = devres_find(supplier, deen_release_vote, NULL, NULL);
	if (held)
		return *held;
	res = devres_alloc(deen_release_vote, sizeof(*res), GFP_KERNEL);
	if (!res)
		return ERR_PTR(-ENOMEM);
	rail = regulator_get_optional(supplier, "vdd-cl");
	if (IS_ERR(rail)) {
		devres_free(res);
		return rail;
	}
	ret = regulator_is_enabled(rail);
	if (ret > 0)
		ret = regulator_enable(rail);
	else if (!ret)
		ret = -ENODEV;
	if (ret) {
		regulator_put(rail);
		devres_free(res);
		return ERR_PTR(ret);
	}
	*res = rail;
	held = devres_get(supplier, res, NULL, NULL);
	if (*held != rail) {
		regulator_disable(rail);
		regulator_put(rail);
	}
	return *held;
}

static int deen_attach(struct platform_device *pdev, struct platform_device *supplier)
{
	static const char * const mux_names[] = { "c0-mux", "c1-mux", "cci-mux" };
	struct device *dev = &pdev->dev, *src = &supplier->dev;
	struct clk *power, *perf, *cci;
	struct regulator *apc;
	struct deen_handoff *h;
	void __iomem *fuse;
	unsigned int bin;
	int i, ret;

	ret = msm8953_cpuclk_check_resources(supplier);
	if (ret)
		return ret;
	power = deen_clock(dev, src->of_node, DEEN_POWER_CLK);
	if (IS_ERR(power))
		return PTR_ERR(power);
	perf = deen_clock(dev, src->of_node, DEEN_PERF_CLK);
	if (IS_ERR(perf))
		return PTR_ERR(perf);
	cci = deen_clock(dev, src->of_node, DEEN_CCI_CLK);
	if (IS_ERR(cci))
		return PTR_ERR(cci);
	h = devm_kzalloc(dev, sizeof(*h), GFP_KERNEL);
	if (!h)
		return -ENOMEM;
	h->pll = deen_read_window(dev, supplier, "c0-pll", 0x1c);
	if (IS_ERR(h->pll))
		return PTR_ERR(h->pll);
	for (i = 0; i < ARRAY_SIZE(h->mux); i++) {
		h->mux[i] = deen_read_window(dev, supplier, mux_names[i], 8);
		if (IS_ERR(h->mux[i]))
			return PTR_ERR(h->mux[i]);
	}
	fuse = deen_read_window(dev, supplier, "efuse", 4);
	if (IS_ERR(fuse))
		return PTR_ERR(fuse);
	bin = msm8953_cpuclk_speed_bin(readl(fuse));
	if (!msm8953_cpuclk_has_cpr4(src->of_node))
		return -ENODEV;
	ret = msm8953_cpuclk_read_plan(src->of_node, bin, &h->domain.plan);
	if (ret)
		return ret;
	if (!deen_verify_rate(&h->domain, clk_get_rate(power)))
		return -EIO;
	apc = deen_hold_vote(src);
	if (IS_ERR(apc))
		return PTR_ERR(apc);
	ret = msm8953_cpuclk_domain_init(&h->domain, src, bin, power, perf, cci, apc);
	if (ret)
		return ret;
	h->domain.verify_rate = deen_verify_rate;
	return msm8953_cpuclk_register_cpufreq(dev, &h->domain, dev->of_node);
}

static int deen_probe(struct platform_device *pdev)
{
	struct device_node *np = pdev->dev.of_node;
	struct platform_device *supplier;
	struct of_phandle_args clock;
	struct device_node *root;
	u32 board[2];
	int index, ret;

	if (!of_machine_is_compatible("qcom,msm8953-deen"))
		return -ENODEV;
	root = of_find_node_by_path("/");
	ret = of_property_read_u32_array(root, "qcom,board-id", board, 2);
	of_node_put(root);
	if (ret || board[0] != 0x4d || board[1] != 0xc100)
		return -ENODEV;
	index = of_property_match_string(np, "clock-names", "cpu0_clk");
	if (index < 0)
		return index;
	ret = of_parse_phandle_with_args(np, "clocks", "#clock-cells", index, &clock);
	if (ret)
		return ret;
	if (clock.args_count != 1 || clock.args[0] != DEEN_POWER_CLK ||
	    !of_device_is_available(clock.np) ||
	    !of_device_is_compatible(clock.np, "qcom,cpu-clock-8953")) {
		of_node_put(clock.np);
		return -EINVAL;
	}
	supplier = of_find_device_by_node(clock.np);
	of_node_put(clock.np);
	if (!supplier)
		return -EPROBE_DEFER;
	if (!device_link_add(&pdev->dev, &supplier->dev, DL_FLAG_AUTOREMOVE_CONSUMER))
		ret = -EINVAL;
	else if (!device_trylock(&supplier->dev))
		ret = -EPROBE_DEFER;
	else {
		ret = device_is_bound(&supplier->dev) ? 0 : -EPROBE_DEFER;
		device_unlock(&supplier->dev);
		if (!ret)
			ret = deen_attach(pdev, supplier);
	}
	put_device(&supplier->dev);
	return ret ? dev_err_probe(&pdev->dev, ret, "APSS CPUFreq handoff\n") : 0;
}

static const struct of_device_id deen_match[] = {
	{ .compatible = "qcom,msm-cpufreq" },
	{}
};

static struct platform_driver deen_cpufreq_platform = {
	.probe = deen_probe,
	.driver = { .name = "deen-cpr4-cpufreq", .of_match_table = deen_match },
};
builtin_platform_driver(deen_cpufreq_platform);

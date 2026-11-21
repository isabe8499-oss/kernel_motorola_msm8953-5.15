// SPDX-License-Identifier: GPL-2.0-only
/* Two virtual memory-access corners on Deen C100, shared by L1 and L2. */
#include <linux/io.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/regulator/driver.h>
#include <linux/regulator/of_regulator.h>

#include "msm8953-deen-mem-acc.h"

static int deen_acc_get_sel(struct regulator_dev *rdev)
{
	return deen_acc_get(rdev_get_drvdata(rdev));
}

static int deen_acc_set_sel(struct regulator_dev *rdev, unsigned int sel)
{
	return deen_acc_set(rdev_get_drvdata(rdev), sel);
}

static const struct regulator_ops deen_acc_ops = {
	.list_voltage = regulator_list_voltage_linear,
	.map_voltage = regulator_map_voltage_linear,
	.get_voltage_sel = deen_acc_get_sel,
	.set_voltage_sel = deen_acc_set_sel,
};

static const struct regulator_desc deen_acc_desc = {
	.name = "apc_mem_acc_corner",
	.owner = THIS_MODULE,
	.type = REGULATOR_VOLTAGE,
	.ops = &deen_acc_ops,
	.min_uV = 1,
	.uV_step = 1,
	.n_voltages = 2,
};

static int deen_acc_probe(struct platform_device *pdev)
{
	static const char * const banks[] = { "acc-sel-l1", "acc-sel-l2" };
	struct device *dev = &pdev->dev;
	struct device_node *np = dev->of_node;
	struct regulator_config cfg = { .dev = dev, .of_node = np };
	struct deen_acc *acc;
	u32 map[2], bit, size;
	unsigned int i;

	if (of_property_count_u32_elems(np, "qcom,corner-acc-map") != 2 ||
	    of_property_read_u32_array(np, "qcom,corner-acc-map", map, 2) ||
	    map[0] != 1 || map[1] != 0)
		return -EINVAL;
	acc = devm_kzalloc(dev, sizeof(*acc), GFP_KERNEL);
	if (!acc)
		return -ENOMEM;
	for (i = 0; i < ARRAY_SIZE(banks); i++) {
		char key[40];

		snprintf(key, sizeof(key), "qcom,%s-bit-pos", banks[i]);
		if (of_property_count_u32_elems(np, key) != 1 ||
		    of_property_read_u32(np, key, &bit) || bit != 0)
			return -EINVAL;
		snprintf(key, sizeof(key), "qcom,%s-bit-size", banks[i]);
		if (of_property_read_u32(np, key, &size) || size != 1)
			return -EINVAL;
		acc->sel[i] = devm_platform_ioremap_resource_byname(pdev, banks[i]);
		if (IS_ERR(acc->sel[i]))
			return PTR_ERR(acc->sel[i]);
	}
	if ((readl(acc->sel[0]) ^ readl(acc->sel[1])) & BIT(0))
		return -EIO;
	cfg.init_data = of_get_regulator_init_data(dev, np, &deen_acc_desc);
	if (!cfg.init_data)
		return -EINVAL;
	cfg.driver_data = acc;
	return PTR_ERR_OR_ZERO(devm_regulator_register(dev, &deen_acc_desc, &cfg));
}

static const struct of_device_id deen_acc_match[] = {
	{ .compatible = "motorola,deen-c100-mem-acc" },
	{}
};

static struct platform_driver deen_acc_driver = {
	.probe = deen_acc_probe,
	.driver = { .name = "deen-c100-mem-acc", .of_match_table = deen_acc_match },
};
builtin_platform_driver(deen_acc_driver);

// SPDX-License-Identifier: GPL-2.0-only
/* C100 system-CCI SAW4.1 and APCC APM, based on the Qualcomm MSM8953
 * msm-spm.c and apm.c register definitions and the Deen C100 boot DTB.
 */
#include <linux/bitfield.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/of_address.h>
#include <linux/slab.h>

#include "c100-power.h"

#define SAW_PMIC_DATA3	0x04c
#define SAW_VCTL	0x900
#define SAW_AVS_CTL	0x904
#define SAW_AVS_LIMIT	0x908
#define SAW_ID		0xc04
#define SAW_PMIC_STS	0xc18
#define SAW_RESET	0xc1c
#define SAW_VERSION	0xfd0
#define SAW_VLEVEL	GENMASK(7, 0)
#define SAW_PORT	GENMASK(18, 16)
#define SAW_BUSY	GENMASK(17, 16)
#define SAW_AVS_ENABLE	BIT(0)

struct deen_saw {
	void __iomem *base;
	spinlock_t lock;
};

struct msm_apm_ctrl_dev {
	void __iomem *base;
};

static void __iomem *map_supplier(struct device *dev, const char *property,
				  struct resource *res, resource_size_t address,
				  resource_size_t size)
{
	struct device_node *node;
	int ret;

	node = of_parse_phandle(dev->of_node, property, 0);
	if (!node)
		return ERR_PTR(-ENODEV);
	ret = of_address_to_resource(node, 0, res);
	of_node_put(node);
	if (ret)
		return ERR_PTR(ret);
	if (res->start != address || resource_size(res) != size)
		return ERR_PTR(-EINVAL);

	return devm_ioremap_resource(dev, res);
}

struct deen_saw *deen_saw_get(struct device *dev)
{
	struct deen_saw *saw;
	struct resource res;
	u32 version;

	saw = devm_kzalloc(dev, sizeof(*saw), GFP_KERNEL);
	if (!saw)
		return ERR_PTR(-ENOMEM);
	saw->base = map_supplier(dev, "motorola,cci-saw", &res, 0xb1d2000, 0x1000);
	if (IS_ERR(saw->base))
		return ERR_CAST(saw->base);
	spin_lock_init(&saw->lock);
	version = readl(saw->base + SAW_VERSION);
	if ((version >> 16) != 0x4001 || !(readl(saw->base + SAW_ID) & BIT(2)))
		return ERR_PTR(-ENODEV);
	return saw;
}

bool deen_saw_avs_enabled(struct deen_saw *saw)
{
	return !!(readl(saw->base + SAW_AVS_CTL) & SAW_AVS_ENABLE);
}

int deen_saw_get_vdd(struct deen_saw *saw)
{
	u32 status;
	int ret;

	ret = readl_poll_timeout_atomic(saw->base + SAW_PMIC_STS, status,
					!(status & SAW_BUSY), 1, 500);
	return ret ? ret : (int)FIELD_GET(SAW_VLEVEL, status);
}

int deen_saw_set_vdd(struct deen_saw *saw, unsigned int level)
{
	unsigned long flags;
	u32 vctl, data, status;
	int ret;

	if (level > FIELD_MAX(SAW_VLEVEL))
		return -ERANGE;
	spin_lock_irqsave(&saw->lock, flags);
	vctl = readl(saw->base + SAW_VCTL) & ~(SAW_PORT | SAW_VLEVEL);
	data = readl(saw->base + SAW_PMIC_DATA3) & ~(SAW_PORT | SAW_VLEVEL);
	writel(1, saw->base + SAW_RESET);
	writel(vctl | level, saw->base + SAW_VCTL);
	writel(data | level, saw->base + SAW_PMIC_DATA3);
	udelay(1);
	ret = readl_poll_timeout_atomic(saw->base + SAW_PMIC_STS, status,
					(status & (SAW_BUSY | SAW_VLEVEL)) == level, 1, 500);
	spin_unlock_irqrestore(&saw->lock, flags);
	return ret;
}

int deen_saw_set_limit(struct deen_saw *saw, unsigned int low, unsigned int high)
{
	unsigned long flags;
	u32 value;
	int ret;

	if (low > high || high > 255)
		return -ERANGE;
	value = low | (high << 16);
	spin_lock_irqsave(&saw->lock, flags);
	writel(value, saw->base + SAW_AVS_LIMIT);
	ret = readl(saw->base + SAW_AVS_LIMIT) == value ? 0 : -EIO;
	spin_unlock_irqrestore(&saw->lock, flags);
	return ret;
}

int deen_saw_avs(struct deen_saw *saw, bool enable)
{
	unsigned long flags;
	u32 val;
	int ret;

	spin_lock_irqsave(&saw->lock, flags);
	val = readl(saw->base + SAW_AVS_CTL);
	val = (val & ~SAW_AVS_ENABLE) | enable;
	writel(val, saw->base + SAW_AVS_CTL);
	ret = readl(saw->base + SAW_AVS_CTL) == val ? 0 : -EIO;
	spin_unlock_irqrestore(&saw->lock, flags);
	return ret;
}

/* Only reserve the three APM registers. The shared CPU mux at +0x50 has
 * a different owner. The CPR controller serializes changes under its lock.
 */
#define APM_MODE	0
#define APM_DELAY	4
#define APM_STATUS	8
#define APM_STATE	GENMASK(4, 0)
#define APM_MX_DONE	0
#define APM_APCC_DONE	3

struct msm_apm_ctrl_dev *msm_apm_ctrl_dev_get(struct device *dev)
{
	struct msm_apm_ctrl_dev *apm;
	struct resource res;
	int ret;

	apm = devm_kzalloc(dev, sizeof(*apm), GFP_KERNEL);
	if (!apm)
		return ERR_PTR(-ENOMEM);
	apm->base = map_supplier(dev, "qcom,apm-ctrl", &res, 0xb1112a8, 12);
	if (IS_ERR(apm->base))
		return ERR_CAST(apm->base);
	ret = msm_apm_get_supply(apm);
	if (ret < 0)
		return ERR_PTR(ret);
	/* C100 stock delays: post-halt 2, halt-clock 17, resume 16, switch 1. */
	writel(0x02111001, apm->base + APM_DELAY);
	if (readl(apm->base + APM_DELAY) != 0x02111001)
		return ERR_PTR(-EIO);
	return apm;
}

int msm_apm_get_supply(struct msm_apm_ctrl_dev *apm)
{
	u32 status = readl(apm->base + APM_STATUS) & APM_STATE;

	if (status == APM_APCC_DONE)
		return MSM_APM_SUPPLY_APCC;
	return status == APM_MX_DONE ? MSM_APM_SUPPLY_MX : -EIO;
}

int msm_apm_set_supply(struct msm_apm_ctrl_dev *apm, enum msm_apm_supply supply)
{
	u32 status, done;

	if (supply != MSM_APM_SUPPLY_APCC && supply != MSM_APM_SUPPLY_MX)
		return -EINVAL;
	done = supply == MSM_APM_SUPPLY_APCC ? APM_APCC_DONE : APM_MX_DONE;
	writel(supply == MSM_APM_SUPPLY_APCC ? 2 : 0, apm->base + APM_MODE);
	return readl_poll_timeout_atomic(apm->base + APM_STATUS, status,
					 (status & APM_STATE) == done, 1, 500);
}

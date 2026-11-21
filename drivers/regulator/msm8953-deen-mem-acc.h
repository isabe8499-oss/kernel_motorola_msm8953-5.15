/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef __DEEN_MEM_ACC_H
#define __DEEN_MEM_ACC_H

#include <linux/io.h>

struct deen_acc {
	void __iomem *sel[2];
};

static int deen_acc_get(struct deen_acc *acc)
{
	u32 bit = readl(acc->sel[0]) & BIT(0);

	if (bit != (readl(acc->sel[1]) & BIT(0)))
		return -EIO;
	return !bit;
}

static int deen_acc_set(struct deen_acc *acc, unsigned int sel)
{
	u32 before[2], target;
	unsigned int i, j;

	if (sel > 1)
		return -EINVAL;
	for (i = 0; i < ARRAY_SIZE(before); i++)
		before[i] = readl(acc->sel[i]);
	if ((before[0] ^ before[1]) & BIT(0))
		return -EIO;
	target = !sel;
	if ((before[0] & BIT(0)) == target)
		return 0;
	for (i = 0; i < ARRAY_SIZE(before); i++) {
		writel((before[i] & ~BIT(0)) | target, acc->sel[i]);
		if ((readl(acc->sel[i]) & BIT(0)) != target) {
			/* Restore the selector bit on both banks already attempted. */
			for (j = 0; j <= i; j++) {
				u32 val = readl(acc->sel[j]);

				writel((val & ~BIT(0)) | (before[j] & BIT(0)), acc->sel[j]);
				readl(acc->sel[j]);
			}
			return -EIO;
		}
	}
	return 0;
}

#endif

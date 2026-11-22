// SPDX-License-Identifier: GPL-2.0-only
#ifndef __DEEN_C100_POWER_H
#define __DEEN_C100_POWER_H

#include <linux/device.h>

struct deen_saw;
struct msm_apm_ctrl_dev;

enum msm_apm_supply {
	MSM_APM_SUPPLY_APCC,
	MSM_APM_SUPPLY_MX,
};

struct deen_saw *deen_saw_get(struct device *dev);
int deen_saw_get_vdd(struct deen_saw *saw);
int deen_saw_set_vdd(struct deen_saw *saw, unsigned int level);
int deen_saw_set_limit(struct deen_saw *saw, unsigned int low, unsigned int high);
int deen_saw_avs(struct deen_saw *saw, bool enable);
struct msm_apm_ctrl_dev *msm_apm_ctrl_dev_get(struct device *dev);
int msm_apm_get_supply(struct msm_apm_ctrl_dev *apm);
int msm_apm_set_supply(struct msm_apm_ctrl_dev *apm, enum msm_apm_supply supply);

#endif

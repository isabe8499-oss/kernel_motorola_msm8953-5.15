// SPDX-License-Identifier: GPL-2.0-only
/* Exercise the C100 SAW/APM driver against memory-backed MMIO, including
 * hardware failure responses. The ARM64 build uses the actual kernel APIs. */
#include <assert.h>
#include <stdbool.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define __iomem
#define GFP_KERNEL 0
#define BIT(n) (1U << (n))
#define GENMASK(h,l) ((~0U >> (31 - (h))) & (~0U << (l)))
#define FIELD_MAX(m) (m)
#define FIELD_GET(m,v) ((v) & (m))
#define PTR_ERR(v) ((long)(v))
#define IS_ERR(v) ((unsigned long)(v) >= (unsigned long)-4095)
#define ERR_PTR(v) ((void *)(long)(v))
#define ERR_CAST(v) ((void *)(v))
typedef unsigned int u32, spinlock_t;
typedef unsigned long resource_size_t;
struct resource { unsigned long start, end; };
struct device_node { struct resource aperture; };
struct device { struct device_node *of_node; };
static u32 saw_regs[1024], apm_regs[3];
static bool applied, status_busy, delay_writable = true;
static unsigned int writes;
#define spin_lock_init(v) (*(v) = 0)
#define spin_lock_irqsave(l,f) ((void)(l), (f)=0)
#define spin_unlock_irqrestore(l,f) ((void)(l),(void)(f))
#define udelay(us) ((void)(us))
static struct device_node *of_parse_phandle(struct device_node *n, const char *p, int i)
{ (void)i; (void)p; return n; }
static void of_node_put(struct device_node *n) { (void)n; }
static int of_address_to_resource(struct device_node *n, int i, struct resource *r)
{ (void)i; *r=n->aperture; return 0; }
static unsigned long resource_size(struct resource *r) { return r->end-r->start+1; }
static void *devm_ioremap_resource(struct device *d, struct resource *r)
{ (void)d; return r->start==0xb1d2000 ? saw_regs : apm_regs; }
static void *devm_kzalloc(struct device *d, size_t size, int f)
{ (void)d; (void)f; return calloc(1,size); }
static u32 readl(const void *addr) { return *(const u32 *)addr; }
static void writel(u32 v, void *addr)
{
	writes++;
	if (addr != apm_regs+1 || delay_writable) *(u32 *)addr=v;
	if (applied && addr == &saw_regs[0x900/4])
		saw_regs[0xc18/4] = (v&255) | (status_busy ? 0x10000 : 0);
	if (applied && addr == apm_regs) apm_regs[2] = v==2 ? 3 : 0;
}
#define readl_poll_timeout_atomic(a,v,c,d,t) ({ (void)(d); (void)(t); (v)=readl(a); (c) ? 0 : -ETIMEDOUT; })
#include "c100-power.c"

int main(void)
{
	struct device_node node = {{0xb1d2000,0xb1d2fff}};
	struct device dev = {&node};
	struct deen_saw *saw;
	struct msm_apm_ctrl_dev *apm;
	unsigned int before;

	assert(PTR_ERR(deen_saw_get(&dev)) == -ENODEV);
	assert(writes == 0);
	saw_regs[SAW_VERSION/4] = 0x40010000;
	saw_regs[SAW_ID/4] = 4;
	saw = deen_saw_get(&dev);
	assert(!IS_ERR(saw));
	saw_regs[SAW_VCTL/4] = 0x810700a1;
	saw_regs[SAW_PMIC_DATA3/4] = 0x110700a1;
	applied = true;
	assert(!deen_saw_set_vdd(saw, 81));
	assert(deen_saw_get_vdd(saw) == 81);
	assert(saw_regs[SAW_VCTL/4] == 0x81000051);
	assert(saw_regs[SAW_PMIC_DATA3/4] == 0x11000051);
	before = writes;
	assert(deen_saw_set_vdd(saw, 256) == -ERANGE);
	assert(deen_saw_set_limit(saw, 81, 80) == -ERANGE);
	assert(deen_saw_set_limit(saw, 0, 256) == -ERANGE);
	assert(writes == before);
	applied = false;
	assert(deen_saw_set_vdd(saw, 80) == -ETIMEDOUT);
	applied = true;
	status_busy = true;
	assert(deen_saw_set_vdd(saw, 80) == -ETIMEDOUT);
	assert(deen_saw_get_vdd(saw) == -ETIMEDOUT);
	assert(!deen_saw_set_limit(saw, 81, 99));
	assert(saw_regs[SAW_AVS_LIMIT/4] == 0x00630051);
	saw_regs[SAW_AVS_CTL/4] = 0x10;
	assert(!deen_saw_avs_enabled(saw));
	assert(!deen_saw_avs(saw, true) && saw_regs[SAW_AVS_CTL/4] == 0x11);
	assert(deen_saw_avs_enabled(saw));
	assert(!deen_saw_avs(saw, false) && saw_regs[SAW_AVS_CTL/4] == 0x10);
	free(saw);

	node.aperture = (struct resource){0xb1112a8,0xb1112b3};
	apm = msm_apm_ctrl_dev_get(&dev);
	assert(!IS_ERR(apm) && apm_regs[1] == 0x02111001);
	assert(msm_apm_get_supply(apm) == MSM_APM_SUPPLY_MX);
	assert(!msm_apm_set_supply(apm, MSM_APM_SUPPLY_APCC));
	assert(msm_apm_get_supply(apm) == MSM_APM_SUPPLY_APCC);
	assert(!msm_apm_set_supply(apm, MSM_APM_SUPPLY_MX));
	applied = false;
	assert(msm_apm_set_supply(apm, MSM_APM_SUPPLY_APCC) == -ETIMEDOUT);
	apm_regs[2] = 2;
	assert(msm_apm_get_supply(apm) == -EIO);
	assert(PTR_ERR(msm_apm_ctrl_dev_get(&dev)) == -EIO);
	apm_regs[2] = apm_regs[1] = 0; delay_writable = false;
	assert(PTR_ERR(msm_apm_ctrl_dev_get(&dev)) == -EIO);
	node.aperture.start++;
	assert(PTR_ERR(msm_apm_ctrl_dev_get(&dev)) == -EINVAL);
	free(apm);
	puts("PASS C100 SAW4/APM register sequence, bounds, readback and timeout cases");
}

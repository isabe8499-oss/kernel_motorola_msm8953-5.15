// SPDX-License-Identifier: GPL-2.0-only
/* Host fault-injection test of the real transition functions. */
#include <assert.h>
#include <stdbool.h>
#include <errno.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

typedef uint32_t u32;
struct clk { unsigned long hz; };
struct regulator { int vote; };
struct mutex { int held; };
struct device_node { struct device_node *parent; };
struct device { struct device_node *of_node; };
#define max(a, b) ((a) > (b) ? (a) : (b))
#define IS_ERR_OR_NULL(p) (!(p))

static struct device_node ctrl, thread = {&ctrl}, supply = {&thread};
static struct clk cpu0, cpu1, cci_clk;
static int fail_vote, fail_clock, bad_readback, disabled, wrong_selector;
static int corner_readback;
static int events[8], nevents;

static struct device_node *of_parse_phandle(struct device_node *n, const char *s, int i)
{
	assert(n && !strcmp(s, "vdd-cl-supply") && !i);
	return &supply;
}
static struct device_node *of_get_parent(struct device_node *n) { return n ? n->parent : NULL; }
static void of_node_put(struct device_node *n) { (void)n; }
static bool of_device_is_compatible(struct device_node *n, const char *s)
{
	return n == &ctrl && !strcmp(s, "qcom,cpr4-msm8953-apss-regulator");
}
static void mutex_init(struct mutex *m) { m->held = 0; }
static void mutex_lock(struct mutex *m) { assert(!m->held); m->held = 1; }
static void mutex_unlock(struct mutex *m) { assert(m->held); m->held = 0; }
static unsigned long clk_get_rate(struct clk *c) { return c->hz; }
static long clk_round_rate(struct clk *c, unsigned long hz) { (void)c; return hz; }
static int clk_set_rate(struct clk *c, unsigned long hz)
{
	assert(c == &cpu0);
	events[nevents++] = -1;
	if (fail_clock)
		return -EIO;
	cpu0.hz = cpu1.hz = hz;
	if (!bad_readback)
		cci_clk.hz = hz * 2 / 5;
	return 0;
}
static int regulator_is_enabled(struct regulator *r) { (void)r; return !disabled; }
static int regulator_get_voltage(struct regulator *r)
{
	return corner_readback ? corner_readback : r->vote;
}
static int regulator_list_voltage(struct regulator *r, int sel)
{
	(void)r;
	return wrong_selector ? 800000 : sel + 1;
}
static int regulator_set_voltage(struct regulator *r, int corner, int limit)
{
	assert(corner >= 1 && limit == 9);
	events[nevents++] = corner;
	if (corner == fail_vote)
		return -EIO;
	r->vote = corner;
	return 0;
}

#include "../drivers/clk/qcom/clk-cpu-msm8953-transition.c"

int msm8953_cpuclk_read_plan(const struct device_node *np, unsigned int bin,
			     struct msm8953_cpuclk_plan *p)
{
	assert(np && bin == 0);
	*p = (struct msm8953_cpuclk_plan) {
		.count = 2, .levels = {{652800000, 261120000, 1}, {1036800000, 414720000, 2}}
	};
	return 0;
}
int main(void)
{
	struct msm8953_cpuclk_domain d = {0};
	struct device dev = {&ctrl};
	struct regulator r = {1};
	const unsigned long low = 652800000, high = 1036800000;
	assert(!msm8953_cpuclk_domain_init(&d, &dev, 0, &cpu0, &cpu1, &cci_clk, &r));
	cpu0.hz = cpu1.hz = low;
	cci_clk.hz = low * 2 / 5;
	assert(!msm8953_cpuclk_set_rate(&d, high));
	assert(nevents == 2 && events[0] == 2 && events[1] == -1);
	nevents = 0;
	assert(!msm8953_cpuclk_set_rate(&d, low));
	assert(nevents == 3 && events[0] == 2 && events[1] == -1 && events[2] == 1);
	nevents = 0;
	fail_vote = 2;
	assert(msm8953_cpuclk_set_rate(&d, high) == -EIO && nevents == 1 && cpu0.hz == low);
	fail_vote = 0;
	fail_clock = 1;
	nevents = 0;
	assert(msm8953_cpuclk_set_rate(&d, high) == -EIO && nevents == 2 && r.vote == 2);
	fail_clock = 0;
	nevents = 0;
	assert(!msm8953_cpuclk_set_rate(&d, high));
	nevents = 0;
	fail_vote = 1;
	assert(msm8953_cpuclk_set_rate(&d, low) == -EIO && cpu0.hz == low && r.vote == 2);
	fail_vote = 0;
	assert(!msm8953_cpuclk_set_rate(&d, low) && r.vote == 1);
	nevents = 0;
	assert(!msm8953_cpuclk_set_rate(&d, high));
	bad_readback = 1;
	nevents = 0;
	assert(msm8953_cpuclk_set_rate(&d, low) == -EIO && r.vote == 2 && nevents == 2);
	nevents = 0;
	assert(msm8953_cpuclk_set_rate(&d, low) == -EIO && !nevents);
	cci_clk.hz = low * 2 / 5;
	wrong_selector = 1;
	assert(msm8953_cpuclk_set_rate(&d, high) == -EINVAL && !nevents);
	wrong_selector = 0;
	bad_readback = 0;
	corner_readback = 1;
	assert(msm8953_cpuclk_set_rate(&d, high) == -EIO && nevents == 1 && cpu0.hz == low);
	corner_readback = -EAGAIN;
	nevents = 0;
	assert(msm8953_cpuclk_set_rate(&d, high) == -EAGAIN && nevents == 1 && cpu0.hz == low);
	corner_readback = 0;
	nevents = 0;
	disabled = 1;
	assert(msm8953_cpuclk_set_rate(&d, high) == -ENODEV && !nevents);
	assert(msm8953_cpuclk_set_rate(&d, 123) == -EINVAL && !nevents);
	assert(!d.lock.held);
}

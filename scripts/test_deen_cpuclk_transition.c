// SPDX-License-Identifier: GPL-2.0-only
/* Host fault-injection test of the real transition functions. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
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
#define dev_warn_ratelimited(dev, ...) ((void)(dev))
#define IS_ERR_OR_NULL(p) (!(p))

static struct device_node ctrl, thread = {&ctrl}, supply = {&thread};
static struct device_node policy_node;
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
static bool of_device_is_compatible(const struct device_node *n, const char *s)
{
	return (n == &ctrl && !strcmp(s, "qcom,cpr4-msm8953-apss-regulator")) ||
	       (n == &policy_node && !strcmp(s, "qcom,msm-cpufreq"));
}
static void mutex_init(struct mutex *m) { m->held = 0; }
static void mutex_lock(struct mutex *m) { assert(!m->held); m->held = 1; }
static void mutex_unlock(struct mutex *m) { assert(m->held); m->held = 0; }
static unsigned long clk_get_rate(struct clk *c) { return c->hz; }
static int round_to_plan;
static const unsigned long mock_rates[] = {
	652800000, 1036800000, 1401600000, 1689600000, 1804800000, 1958400000,
	2016000000, 2150400000, 2208000000,
};
static long clk_round_rate(struct clk *c, unsigned long hz)
{
	unsigned int i;

	assert(c == &cpu0);
	if (!round_to_plan)
		return hz;
	for (i = 0; i < sizeof(mock_rates) / sizeof(mock_rates[0]); i++)
		if (mock_rates[i] >= hz)
			return mock_rates[i];
	return -ERANGE;
}
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
/* Exercise registration, policy construction and target_index with the 5.15
 * callbacks. Core shims model one shared policy and device-managed cleanup.
 */
#define CPUFREQ_IS_COOLING_DEV 4
#define CPUFREQ_ETERNAL (~0U)
#define CPUFREQ_TABLE_END (~1U)
#define GFP_KERNEL 0
#define scnprintf snprintf
struct freq_attr { int unused; };
struct cpufreq_frequency_table { unsigned int frequency; };
struct cpufreq_policy {
	void *driver_data;
	struct cpufreq_frequency_table *freq_table;
};
struct cpufreq_policy_data { int unused; };
struct cpufreq_driver {
	char name[16];
	int flags;
	int (*init)(struct cpufreq_policy *);
	unsigned int (*get)(unsigned int);
	int (*verify)(struct cpufreq_policy_data *);
	int (*target_index)(struct cpufreq_policy *, unsigned int);
	struct freq_attr **attr;
	void *driver_data;
};
struct of_phandle_args { struct device_node *np; int args_count; u32 args[1]; };
static struct freq_attr *cpufreq_generic_attr[] = {NULL};
static struct cpufreq_driver *active;
static struct cpufreq_policy policy;
static void (*cleanup)(void *);
static void *cleanup_arg;
static int wrong_clock;
/* Original C100 policy, in kHz. */
static const u32 requests[] = {345600, 533000, 729600, 1036800, 1401600,
			       1651600, 1804800, 1958400, 2016000};
static bool of_device_is_available(const struct device_node *n) { return n == &policy_node; }
static bool of_machine_is_compatible(const char *s) { return !strcmp(s, "qcom,msm8953-deen"); }
static int of_property_match_string(const struct device_node *n, const char *p, const char *v)
{
	int cpu;
	assert(n == &policy_node && !strcmp(p, "clock-names") && sscanf(v, "cpu%d_clk", &cpu) == 1);
	return cpu + 1;
}
static int of_parse_phandle_with_args(const struct device_node *n, const char *p,
				      const char *cells, int index, struct of_phandle_args *a)
{
	assert(n == &policy_node && !strcmp(p, "clocks") && !strcmp(cells, "#clock-cells"));
	assert(index >= 1 && index <= 8);
	a->np = &ctrl;
	a->args_count = 1;
	a->args[0] = wrong_clock && index == 8 ? 42 : 778762544;
	return 0;
}
static int of_property_count_u32_elems(const struct device_node *n, const char *p)
{
	assert(n == &policy_node && !strcmp(p, "qcom,cpufreq-table"));
	return sizeof(requests) / sizeof(requests[0]);
}
static int of_property_read_u32_index(const struct device_node *n, const char *p,
				      int i, u32 *value)
{
	assert(i >= 0 && i < of_property_count_u32_elems(n, p));
	*value = requests[i];
	return 0;
}
static void *devm_kzalloc(struct device *dev, size_t size, int flags)
{
	assert(dev && !flags);
	return calloc(1, size);
}
static int devm_add_action_or_reset(struct device *dev, void (*fn)(void *), void *arg)
{
	assert(dev && !cleanup);
	cleanup = fn;
	cleanup_arg = arg;
	return 0;
}
static int cpufreq_generic_frequency_table_verify(struct cpufreq_policy_data *p)
{
	return p ? 0 : -EINVAL;
}
static void *cpufreq_get_driver_data(void) { return active->driver_data; }
static void cpufreq_generic_init(struct cpufreq_policy *p,
				 struct cpufreq_frequency_table *table, unsigned int latency)
{
	assert(latency == CPUFREQ_ETERNAL);
	p->freq_table = table;
}
static int cpufreq_register_driver(struct cpufreq_driver *drv)
{
	assert(!active);
	active = drv;
	return drv->init(&policy);
}
static int cpufreq_unregister_driver(struct cpufreq_driver *drv)
{
	assert(active == drv);
	active = NULL;
	return 0;
}

#include "../drivers/clk/qcom/clk-cpu-msm8953-cpufreq.c"

static void test_cpufreq(void)
{
	struct msm8953_cpuclk_domain d = {0};
	struct device dev = {&ctrl};
	struct regulator r = {1};
	unsigned int i;

	assert(!msm8953_cpuclk_domain_init(&d, &dev, 0, &cpu0, &cpu1, &cci_clk, &r));
	d.plan.count = sizeof(mock_rates) / sizeof(mock_rates[0]);
	for (i = 0; i < d.plan.count; i++)
		d.plan.levels[i] = (struct msm8953_cpuclk_level) {
			mock_rates[i], mock_rates[i] * 2 / 5, i + 1
		};
	round_to_plan = 1;
	cpu0.hz = cpu1.hz = mock_rates[0];
	cci_clk.hz = d.plan.levels[0].cci_hz;
	wrong_clock = 1;
	nevents = 0;
	assert(msm8953_cpuclk_register_cpufreq(&dev, &d, &policy_node) == -EINVAL);
	assert(!active && !nevents);
	wrong_clock = 0;
	assert(!msm8953_cpuclk_register_cpufreq(&dev, &d, &policy_node));
	for (i = 0; i < 7; i++)
		assert(policy.freq_table[i].frequency == mock_rates[i] / 1000);
	assert(policy.freq_table[7].frequency == CPUFREQ_TABLE_END);
	nevents = 0;
	assert(active->target_index(&policy, 7) == -EINVAL && !nevents);
	assert(!active->target_index(&policy, 6));
	assert(active->get(7) == 2016000 && events[0] == 7 && events[1] == -1);
	nevents = 0;
	assert(!active->target_index(&policy, 0));
	assert(nevents == 3 && events[0] == 7 && events[1] == -1 && events[2] == 1);
	cleanup(cleanup_arg);
	assert(!active);
	free(cleanup_arg);
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
	assert(!msm8953_cpuclk_set_rate(&d, low) && cpu0.hz == low && r.vote == 2);
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
	disabled = 0;
	test_cpufreq();
}

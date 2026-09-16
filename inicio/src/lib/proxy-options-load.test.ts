import { describe, expect, it } from 'vitest';

import proxyOptions from '../../proxyOptions';

describe('proxyOptions', () => {
	it('loads without frappe-bench sites/common_site_config.json', () => {
		const rule = proxyOptions['^/(app|api|assets|files|private)'];
		expect(rule).toBeDefined();
		expect(rule.target).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/);
	});
});

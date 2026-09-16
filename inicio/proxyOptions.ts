function readWebserverPort(): number {
	try {
		// Bench checkout only. GitHub Actions / vitest have no sites/.
		// eslint-disable-next-line @typescript-eslint/no-require-imports
		const common_site_config = require('../../../sites/common_site_config.json');
		const port = Number(common_site_config?.webserver_port);
		if (Number.isFinite(port) && port > 0) {
			return port;
		}
	} catch {
		// CI and isolated Vite loads: proxy is unused during `vitest run`.
	}
	return 8000;
}

const webserver_port = readWebserverPort();

export default {
	'^/(app|api|assets|files|private)': {
		target: `http://127.0.0.1:${webserver_port}`,
		ws: true,
		router: function (req) {
			const site_name = req.headers.host.split(':')[0];
			return `http://${site_name}:${webserver_port}`;
		},
	},
};

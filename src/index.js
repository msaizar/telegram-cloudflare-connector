/**
 * The Telegram Connector is a scheduled Cloudflare Worker that fetches messages from Telegram channels and stores them by running a container using `env.CONTAINER`
 *
 * ## Best Practices
 * - Simplicity, reliability, and efficiency.
 * - Stick to JSDoc for specifications, documentation, and type definitions.
 * - Robust error handling and logging techniques with succinct messages. Wrapping each data processing stage in a try-catch block, validating all inputs and outputs, and using `INFO` and `ERROR` levels with detailed contextual information, such as processing stage, task name, etc.
 * - Concise code with minimal formatting and indentation, which prioritizes descriptive element naming and log messages over inline comments to achieve readability.
 *
 * ## Additional Documentation
 *
 * ### Containers in Cloudflare Worker
 * ```js
 * import { Container, getContainer } from "@cloudflare/containers";
 *
 * export class MyContainer extends Container {
 *   defaultPort = 4000; // Port the container is listening on
 *   sleepAfter = "10m"; // Stop the instance if requests not sent for 10 minutes
 * }
 *
 * export default {
 *   async fetch(request, env) {
 *     const { "session-id": sessionId } = await request.json();
 *     // Get the container instance for the given session ID
 *     const containerInstance = getContainer(env.MY_CONTAINER, sessionId);
 *     // Pass the request to the container instance on its default port
 *     return containerInstance.fetch(request);
 *   },
 * };
 * ```
 */

import { Container, getContainer } from "@cloudflare/containers";

export class MyContainer extends Container {
	defaultPort = 8080;
	sleepAfter = "10s";

	onStart() {
		console.log("Container started successfully");
	}

	onError(error) {
		console.error("Container error occurred:");
		console.error("  Error type:", error.constructor.name);
		console.error("  Error message:", error.message);
		if (error.stack) {
			console.error("  Stack trace:", error.stack);
		}
		if (error.exitCode !== undefined) {
			console.error("  Exit code:", error.exitCode);
		}
	}
}

export default {
	async scheduled(_ctx, env) {
		try {
			const containerInstance = getContainer(env.CONTAINER, "theOnlyOne");

			console.log("Container instance created");

			await containerInstance.startAndWaitForPorts({
				startOptions: {
					envVars: {
						TELEGRAM_API_ID: env.TELEGRAM_API_ID,
						TELEGRAM_API_HASH: env.TELEGRAM_API_HASH,
						TELEGRAM_SESSION_STR: env.TELEGRAM_SESSION_STR,
						TIMESCALE_CONNECTION: env.TIMESCALE_CONNECTION,
					},
				},
			});

			const response = await containerInstance.fetch(
				new Request("http://localhost:8080/connector"),
			);
			console.log("Container response status:", response.status);

			if (!response.ok) {
				const errorText = await response.text();
				console.error("Container error response:", errorText);
				return new Response(errorText, { status: response.status });
			}
			return new Response("Success", { status: 200 });
		} catch (e) {
			console.error("Error in scheduled handler:", e);
			return new Response(e.message, { status: 500 });
		}
	},
};

import { plugin } from "bun";

// Register MDX loader for prompt templates
plugin({
  name: "mdx-loader",
  setup(build) {
    build.onLoad({ filter: /\.mdx$/ }, async (args) => {
      const text = await Bun.file(args.path).text();
      // Export MDX as a function component that interpolates props
      const code = `
        export default function MDXPrompt(props) {
          let text = ${JSON.stringify(text)};
          // Replace {props.X} patterns
          for (const [key, value] of Object.entries(props)) {
            text = text.replaceAll(\`{props.\${key}}\`, String(value ?? ""));
          }
          return text;
        }
      `;
      return { contents: code, loader: "ts" };
    });
  },
});

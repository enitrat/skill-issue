// types.d.ts — Type declarations and module augmentations
//
// MDX imports need declarations since they're loaded via bun preload plugin

declare module "*.mdx" {
  const MDXComponent: (props: Record<string, any>) => any;
  export default MDXComponent;
}

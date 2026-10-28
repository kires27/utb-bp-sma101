# File structure
> https://fadamakis.com/a-front-end-application-folder-structure-that-makes-sense-ecc0b690968b
> https://medium.com/@mohandabdiche/building-efficient-frontends-a-vue-3-blueprint-for-modern-medium-sized-applications-671dd403ca62
components: All shared components that are used across the entire application.
composables: All shared composables.
config: Application configuration files.
features: Contains all the application features. We want to keep most of the application code inside here. More on this later.
layouts: Different layouts for the pages.
lib: Configurations for different third-party libraries that are used in our application.
pages: The pages of our application.
services: Shared application services and providers.
stores: Global state stores.
test: Test-related mocks, helpers, utilities, and configurations.
types: Shared TypeScript type definitions.
utils: Shared utility functions
api: All the fetch logic goes here. This decouples the API and the UI.
components: Feature specific components.
composables: Feature specific composables.
stores: The state management code. Multiple sub-modules are expected and actually encouraged.
types: Feature specific typeScript type definitions.
index.ts: This is the entry point of the feature. It behaves as the public API of the feature, and it should only export things that should be public for other parts of the application.


# Nuxt Minimal Starter

Look at the [Nuxt documentation](https://nuxt.com/docs/getting-started/introduction) to learn more.

## Setup

Make sure to install dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.

# useful
- https://shadcn-vue.com/
- https://vue-bits.dev/
- https://uiverse.io/elements
- https://icon-sets.iconify.design/material-symbols/page-3.html
- https://supabase.nuxtjs.org/services/serversupabaseclient
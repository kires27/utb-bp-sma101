<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'body',
    validator: (v: string) =>
      [
        'hero',
        'h1',
        'h2',
        'h3',
        'body',
        'body-sm',
        'label',
      ].includes(v),
  },

  tone: {
    type: String,
    default: 'tone',
    validator: (v: string) =>
      ['tone', 'muted', 'green', 'yellow', 'red', 'blue', 'purple'].includes(v),
  },

  weight: {
    type: String,
    default: 'normal',
    validator: (v: string) =>
      ['light', 'normal', 'medium', 'bold'].includes(v),
  },

  link: {
    type: Boolean,
    default: false,
  },
})

const tag = computed(() => {
  switch (props.variant) {
    case 'hero':
      return 'h1'
    case 'h1':
      return 'h1'
    case 'h2':
      return 'h2'
    case 'h3':
      return 'h3'
    case 'label':
      return 'span'
    default:
      return 'p'
  }
})
</script>

<template>
  <component :is="tag" :class="[
    'text',
    `text--${variant}`,
    `text--${tone}`,
    weight && `text--${weight}`,
    link && 'text--link',
  ]" v-bind="$attrs">
    <slot />
  </component>
</template>

<style scoped>
.text {
  margin: 0;
  font-family: var(--font-main);
}

/* ---------- Size ---------- */

.text--hero {
  font-size: 52px;
  line-height: 1.1;
  letter-spacing: -.03em;
  font-weight: 300;
  padding: 1.5rem 0;
}

.text--h1 {
  font-size: 44px;
  line-height: 1.15;
  letter-spacing: -.02em;
  font-weight: 300;
  padding: 8px 0;
}

.text--h2 {
  font-size: 28px;
  line-height: 1.2;
  font-weight: 400;
}

.text--h3 {
  font-size: 20px;
  line-height: 1.3;
  font-weight: 500;
}

.text--body {
  font-size: 15px;
  line-height: 1.7;
}

.text--body-sm {
  font-size: 13px;
  line-height: 1.6;
}

.text--label {
  font-size: 11px;
  letter-spacing: .15em;
  text-transform: uppercase;
}

/* ---------- Color ---------- */

.text--tone {
  color: var(--fg);
}

.text--muted {
  color: var(--fg-2);
}

.text--green {
  color: var(--teal);
}

.text--purple {
  color: var(--purple);
}

.text--yellow {
  color: var(--gold);
}

.text--red {
  color: var(--rose);
}

.text--blue {
  color: var(--blue);
}

/* ---------- Weight ---------- */

.text--light {
  font-weight: 300;
}

.text--normal {
  font-weight: 500;
}

.text--medium {
  font-weight: 600;
}

.text--bold {
  font-weight: 800;
}

/* ---------- Link ---------- */

.text--link {
  transition: filter var(--transition);
  cursor: pointer;
}

.text--link:hover {
  filter: brightness(1.3);
}

/* ---------- Rich text ---------- */

.text :deep(em) {
  font-style: italic;
}

.text :deep(a) {
  color: inherit;
  text-decoration: underline;
}
</style>
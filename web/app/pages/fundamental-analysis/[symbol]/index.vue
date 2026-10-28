<script setup>
import { URI } from '#shared/constants/routes';

const route = useRoute()

await navigateTo(
	URI.tool.fa_financials(route.params.symbol),
	{ replace: true }
)
</script>

<template />
<script setup>
const cellSize2 = 15;
</script>

<template>
  <div class="cell1 skelet pulse">
    <div></div>
    <div></div>
    <div></div>
  </div>

  <div class="group1 pulse">
    <div class="cell2 skelet">
      <span></span>
      <div></div>
    </div>

    <div class="cell3 skelet">
      <div v-for="i in cellSize2" :key="i"></div>
    </div>
  </div>
</template>

<style scoped>
.skelet {
  display: flex;
  flex-direction: column;
  width: fit-content;
  gap: 8px;
  border: 1.5px solid var(--neutral500);
  padding: 1rem;
  border-radius: 10px;
}

.group1 {
  display: flex;
  gap: 1rem;
}

.cell1 {
  width: 13rem;
  height: 4rem;
}

.cell2 {
  width: 30rem;
  height: 40vh;
}

.cell3 {
  width: 20rem;
  height: 40vh;
}

.cell1 div, .cell2 div, .cell3 div {
  background-color: var(--neutral500);
  width: 100%;
  height: 100%;
}

.cell1 span, .cell2 span, .cell3 span {
  background-color: var(--neutral500);
  width: 100%;
  height: 15%;
}

.pulse {
  animation: pulse 1.5s linear infinite alternate;
}

@keyframes pulse {
  0% {
    opacity: 0.35;
  }
  100% {
    opacity: 0.6;
  }
}
</style>

<template>
  <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-base font-bold text-gray-800">Matriz de Riscos 5x5 (HC-UFPE)</h3>
        <p class="text-xs text-gray-500">Tolerância Institucional ao Risco: até 7,99 (Colegiado Executivo)</p>
      </div>
      <!-- Legenda de cores -->
      <div class="flex items-center space-x-3 text-xs">
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-emerald-500 mr-1"></span> Baixo (≤2)</span>
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-amber-400 mr-1"></span> Médio (3-7)</span>
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-orange-500 mr-1"></span> Alto (8-14)</span>
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-rose-600 mr-1"></span> Extremo (15-25)</span>
      </div>
    </div>

    <!-- Grade 5x5 -->
    <div class="flex items-center">
      <!-- Eixo Y: Probabilidade -->
      <div class="flex flex-col justify-between h-72 mr-3 text-xs font-semibold text-gray-600 text-right w-24">
        <span class="text-xs uppercase text-gray-400 tracking-wider">Probabilidade</span>
        <span>5 - Quase Certo</span>
        <span>4 - Provável</span>
        <span>3 - Possível</span>
        <span>2 - Pouco Prov.</span>
        <span>1 - Improvável</span>
      </div>

      <!-- Células da Matriz (5 linhas de 5 colunas) -->
      <div class="flex-1 grid grid-cols-5 gap-1.5 h-72">
        <template v-for="p in [5, 4, 3, 2, 1]" :key="'p-' + p">
          <template v-for="i in [1, 2, 3, 4, 5]" :key="'c-' + p + '-' + i">
            <div 
              :class="[
                getCellColor(p, i),
                isHighlight(p, i) ? 'ring-4 ring-blue-600 scale-105 z-10 shadow-lg' : 'opacity-90 hover:opacity-100',
                'rounded-lg flex flex-col items-center justify-center p-1 transition-all duration-200 cursor-pointer text-white font-medium relative select-none'
              ]"
              :title="'Probabilidade: ' + p + ' | Impacto: ' + i + ' (Inerente: ' + (p * i) + ')'"
            >
              <span class="text-xs font-bold">{{ p * i }}</span>
              <span v-if="counts && counts[p + '_' + i]" class="text-[11px] bg-white/30 backdrop-blur-sm px-1.5 py-0.5 rounded-full mt-0.5">
                {{ counts[p + '_' + i] }}
              </span>
              <span v-if="isHighlight(p, i)" class="absolute -top-2 -right-2 bg-blue-600 text-white rounded-full p-1 shadow">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
              </span>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Eixo X: Impacto -->
    <div class="flex justify-between mt-2 pl-28 text-xs font-semibold text-gray-600 text-center">
      <span class="flex-1">1 - Insignificante</span>
      <span class="flex-1">2 - Menor</span>
      <span class="flex-1">3 - Moderado</span>
      <span class="flex-1">4 - Maior</span>
      <span class="flex-1">5 - Catastrófico</span>
    </div>
    <div class="text-center text-xs uppercase text-gray-400 font-semibold tracking-wider mt-1 pl-24">
      Impacto
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  counts?: Record<string, number>;
  activeP?: number;
  activeI?: number;
}>();

function getCellColor(p: number, i: number): string {
  const inerente = p * i;
  if (inerente <= 2) return 'bg-emerald-500';
  if (inerente <= 7) return 'bg-amber-400 text-gray-900';
  if (inerente <= 14) return 'bg-orange-500';
  return 'bg-rose-600';
}

function isHighlight(p: number, i: number): boolean {
  return props.activeP === p && props.activeI === i;
}
</script>

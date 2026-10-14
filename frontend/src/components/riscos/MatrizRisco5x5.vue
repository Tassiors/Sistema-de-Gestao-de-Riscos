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
    <div class="flex items-stretch">
      <!-- Eixo Y: Título rotacionado -->
      <div class="flex items-center justify-center w-6 mr-1 select-none">
        <span class="-rotate-90 whitespace-nowrap text-[11px] uppercase text-gray-400 font-bold tracking-widest">
          Probabilidade
        </span>
      </div>

      <!-- Eixo Y: Rótulos das 5 Linhas perfeitamente alinhados -->
      <div class="grid grid-rows-5 gap-1.5 h-72 mr-2 text-xs font-semibold text-gray-600 text-right w-24">
        <div class="flex items-center justify-end">5 - Muito Alta</div>
        <div class="flex items-center justify-end">4 - Alta</div>
        <div class="flex items-center justify-end">3 - Média</div>
        <div class="flex items-center justify-end">2 - Baixa</div>
        <div class="flex items-center justify-end">1 - Muito Baixa</div>
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

    <!-- Eixo X: Impacto alinhado com as colunas -->
    <div class="flex items-center mt-2">
      <div class="w-6 mr-1 shrink-0"></div>
      <div class="w-24 mr-2 shrink-0"></div>
      <div class="flex-1 grid grid-cols-5 gap-1.5 text-xs font-semibold text-gray-600 text-center">
        <div>1 - Muito Baixo</div>
        <div>2 - Baixo</div>
        <div>3 - Médio</div>
        <div>4 - Alto</div>
        <div>5 - Muito Alto</div>
      </div>
    </div>

    <!-- Eixo X: Título centralizado -->
    <div class="flex items-center mt-1">
      <div class="w-6 mr-1 shrink-0"></div>
      <div class="w-24 mr-2 shrink-0"></div>
      <div class="flex-1 text-center text-xs uppercase text-gray-400 font-bold tracking-wider select-none">
        Impacto
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  counts?: Record<string, number>;
  activeP?: number | null;
  activeI?: number | null;
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

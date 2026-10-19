<template>
  <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-6">
    <!-- Cabeçalho do Gráfico com Total Geral e Destaque da Zona Dominante -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-100 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xl">📊</span>
          <h3 class="text-base font-bold text-gray-900">Mapa de Distribuição de Riscos por Zonas</h3>
        </div>
        <p class="text-xs text-gray-500 mt-0.5">
          Distribuição espacial dos riscos mapeados com status <strong>SUBMETIDO</strong> na Matriz de Riscos.
        </p>
      </div>

      <!-- Card do Total de Riscos Mapeados (Fundo Branco Suave e Elegante) -->
      <div class="flex items-center gap-3.5 bg-white border border-gray-200 hover:border-blue-300 px-5 py-3 rounded-2xl shadow-xs transition hover:shadow-sm">
        <div class="w-11 h-11 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0 text-blue-600 shadow-2xs">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-gray-500 block leading-tight">
            Total de Riscos Mapeados
          </span>
          <div class="flex items-baseline gap-2 mt-0.5">
            <span class="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight font-mono">
              {{ totalGeralRiscos }}
            </span>
            <span class="text-xs font-semibold text-gray-400">
              {{ totalGeralRiscos === 1 ? 'risco submetido' : 'riscos submetidos' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Cards das 4 Zonas com Distribuição e Destaque da Zona com Maior Concentração -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div 
        v-for="z in zonasOrdenadas" 
        :key="z.chave"
        class="p-3.5 rounded-xl border transition-all relative"
        :class="[
          z.chave === zonaMaiorConcentracao?.chave && totalGeralRiscos > 0
            ? `${z.corBordaAtiva} ring-2 ${z.corRing} shadow-sm bg-white` 
            : `${z.corBorda} ${z.corFundoCard}`
        ]"
      >
        <!-- Badge Indicadora da Zona de Maior Concentração -->
        <div 
          v-if="z.chave === zonaMaiorConcentracao?.chave && totalGeralRiscos > 0" 
          class="absolute -top-2.5 right-2"
        >
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-black tracking-wide text-white shadow-xs" :class="z.corBadgeDestaque">
            <span>🔥</span>
            <span>Maior Concentração</span>
          </span>
        </div>

        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold uppercase tracking-wider" :class="z.corTextoTitulo">
            {{ z.nome }}
          </span>
          <span class="w-2.5 h-2.5 rounded-full" :class="z.corPonto"></span>
        </div>

        <div class="flex items-baseline justify-between mt-2.5">
          <span class="text-2xl font-black text-gray-900 tracking-tight">
            {{ z.total }}
          </span>
          <span class="text-xs font-extrabold" :class="z.corTextoValor">
            {{ z.percentual }}%
          </span>
        </div>

        <div class="text-[10px] text-gray-500 mt-1 flex justify-between">
          <span>{{ z.intervalo }}</span>
          <span class="italic text-gray-400">{{ z.descricaoApetite }}</span>
        </div>
      </div>
    </div>

    <!-- Área da Matriz 5x5: Cores de Células Suavizadas e Fundo Neutro Limpo -->
    <div class="pt-2">
      <div class="flex items-stretch">
        <!-- Eixo Y: Título rotacionado -->
        <div class="flex items-center justify-center w-7 mr-2 select-none">
          <span class="-rotate-90 whitespace-nowrap text-[11px] uppercase text-gray-500 font-bold tracking-widest flex items-center gap-1">
            <span>Probabilidade</span>
            <span>↑</span>
          </span>
        </div>

        <!-- Eixo Y: Rótulos das 5 Linhas -->
        <div class="grid grid-rows-5 gap-1.5 h-88 mr-3 text-xs font-semibold text-gray-600 text-right w-28 select-none">
          <div class="flex items-center justify-end">5 - Muito Alta</div>
          <div class="flex items-center justify-end">4 - Alta</div>
          <div class="flex items-center justify-end">3 - Média</div>
          <div class="flex items-center justify-end">2 - Baixa</div>
          <div class="flex items-center justify-end">1 - Muito Baixa</div>
        </div>

        <!-- Grade 5x5 com Fundo Neutro e Células em Tons Pastéis Suaves -->
        <div class="flex-1 grid grid-cols-5 gap-1.5 h-88 p-2 rounded-2xl bg-slate-50/70 border border-gray-200/90 shadow-2xs relative">
          <template v-for="p in [5, 4, 3, 2, 1]" :key="'p-' + p">
            <template v-for="i in [1, 2, 3, 4, 5]" :key="'cell-' + p + '-' + i">
              <div 
                class="rounded-xl flex flex-col items-center justify-between p-2 transition-all duration-200 border relative select-none hover:shadow-xs"
                :class="getCelulaBgClass(p * i)"
                :title="`Probabilidade ${p} × Impacto ${i} = ${p * i} (${getZonaPorScore(p * i)})\nRiscos mapeados: ${getQtd(p, i)}`"
              >
                <!-- Score Numérico Inerente (P × I) no Canto Superior Esquerdo -->
                <div class="w-full flex items-center justify-between text-[10px] font-mono" :class="getCelulaTextoClass(p * i)">
                  <span class="font-bold opacity-85">{{ p * i }}</span>
                  <span class="text-[9px] uppercase font-black tracking-tight opacity-70">
                    {{ getZonaSigla(p * i) }}
                  </span>
                </div>

                <!-- Conteúdo Central: Exibe Badge Somente se Houver Riscos Mapeados -->
                <div class="my-auto flex flex-col items-center justify-center">
                  <div 
                    v-if="getQtd(p, i) > 0"
                    class="px-2.5 py-1 rounded-full text-xs font-black shadow-2xs flex items-center gap-1 transition-transform transform hover:scale-105"
                    :class="getBadgeClass(p * i)"
                  >
                    <span>{{ getQtd(p, i) }}</span>
                    <span class="text-[10px] opacity-90 font-bold">
                      ({{ ((getQtd(p, i) / (totalGeralRiscos || 1)) * 100).toFixed(0) }}%)
                    </span>
                  </div>
                  <span v-else class="text-[11px] font-bold opacity-25 select-none text-gray-400">
                    ·
                  </span>
                </div>

                <div class="h-1"></div>
              </div>
            </template>
          </template>
        </div>
      </div>

      <!-- Eixo X: Rótulos das Colunas -->
      <div class="flex items-center mt-2.5 select-none">
        <div class="w-7 mr-2 shrink-0"></div>
        <div class="w-28 mr-3 shrink-0"></div>
        <div class="flex-1 grid grid-cols-5 gap-1.5 text-xs font-semibold text-gray-600 text-center">
          <div>1 - Muito Baixo</div>
          <div>2 - Baixo</div>
          <div>3 - Médio</div>
          <div>4 - Alto</div>
          <div>5 - Muito Alto</div>
        </div>
      </div>

      <!-- Eixo X: Título Centralizado -->
      <div class="flex items-center mt-1 select-none">
        <div class="w-7 mr-2 shrink-0"></div>
        <div class="w-28 mr-3 shrink-0"></div>
        <div class="flex-1 text-center text-xs uppercase text-gray-500 font-bold tracking-widest flex items-center justify-center gap-1">
          <span>Impacto</span>
          <span>→</span>
        </div>
      </div>
    </div>

    <!-- Legenda Suave das Faixas de Risco -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
      <div class="flex items-center gap-3">
        <span class="font-bold text-gray-700">Escala de Riscos:</span>
        <div class="flex items-center gap-2 text-[11px]">
          <span class="inline-flex items-center gap-1">
            <span class="w-3 h-3 rounded-md bg-emerald-50 border border-emerald-300"></span>
            <span class="text-emerald-950 font-medium">Baixo (1–2)</span>
          </span>
          <span class="text-gray-300">→</span>
          <span class="inline-flex items-center gap-1">
            <span class="w-3 h-3 rounded-md bg-amber-50 border border-amber-300"></span>
            <span class="text-amber-950 font-medium">Médio (3–7)</span>
          </span>
          <span class="text-gray-300">→</span>
          <span class="inline-flex items-center gap-1">
            <span class="w-3 h-3 rounded-md bg-orange-50 border border-orange-300"></span>
            <span class="text-orange-950 font-medium">Alto (8–14)</span>
          </span>
          <span class="text-gray-300">→</span>
          <span class="inline-flex items-center gap-1">
            <span class="w-3 h-3 rounded-md bg-rose-50 border border-rose-300"></span>
            <span class="text-rose-950 font-medium">Extremo (15–25)</span>
          </span>
        </div>
      </div>

      <div class="text-[11px] text-gray-400">
        Valores exibidos representam a contagem de riscos submetidos.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  counts?: Record<string, number>;
}>();

function getQtd(p: number, i: number): number {
  if (!props.counts) return 0;
  return props.counts[`${p}_${i}`] || 0;
}

const totalGeralRiscos = computed(() => {
  if (!props.counts) return 0;
  return Object.values(props.counts).reduce((acc, val) => acc + (val || 0), 0);
});

function getZonaPorScore(score: number): 'BAIXO' | 'MEDIO' | 'ALTO' | 'EXTREMO' {
  if (score <= 2) return 'BAIXO';
  if (score <= 7) return 'MEDIO';
  if (score <= 14) return 'ALTO';
  return 'EXTREMO';
}

function getZonaSigla(score: number): string {
  const z = getZonaPorScore(score);
  switch (z) {
    case 'BAIXO': return 'Bx';
    case 'MEDIO': return 'Med';
    case 'ALTO': return 'Alt';
    case 'EXTREMO': return 'Ext';
  }
}

function getBadgeClass(score: number): string {
  const z = getZonaPorScore(score);
  switch (z) {
    case 'BAIXO': return 'bg-emerald-600 text-white';
    case 'MEDIO': return 'bg-amber-500 text-white';
    case 'ALTO': return 'bg-orange-500 text-white';
    case 'EXTREMO': return 'bg-rose-600 text-white';
  }
}

function getCelulaBgClass(score: number): string {
  const z = getZonaPorScore(score);
  switch (z) {
    case 'BAIXO':
      // Zona Baixo (Scores 1 a 2): Verde suave pastel com borda suave
      return 'bg-emerald-50/90 border-emerald-200/70 hover:bg-emerald-100/70 text-emerald-950';
    case 'MEDIO':
      // Zona Médio (Scores 3 a 7): Amarelo / Âmbar suave pastel com borda suave
      return 'bg-amber-50/90 border-amber-200/70 hover:bg-amber-100/70 text-amber-950';
    case 'ALTO':
      // Zona Alto (Scores 8 a 14): Laranja suave pastel com borda suave
      return 'bg-orange-50/90 border-orange-200/70 hover:bg-orange-100/70 text-orange-950';
    case 'EXTREMO':
      // Zona Extremo (Scores 15 a 25): Rosa/Vermelho suave pastel com borda suave
      return 'bg-rose-50/90 border-rose-200/70 hover:bg-rose-100/70 text-rose-950';
  }
}

function getCelulaTextoClass(score: number): string {
  const z = getZonaPorScore(score);
  switch (z) {
    case 'BAIXO': return 'text-emerald-800';
    case 'MEDIO': return 'text-amber-800';
    case 'ALTO': return 'text-orange-800';
    case 'EXTREMO': return 'text-rose-800';
  }
}

const totaisPorZona = computed(() => {
  const totais = { BAIXO: 0, MEDIO: 0, ALTO: 0, EXTREMO: 0 };
  for (let p = 1; p <= 5; p++) {
    for (let i = 1; i <= 5; i++) {
      const score = p * i;
      const z = getZonaPorScore(score);
      totais[z] += getQtd(p, i);
    }
  }
  return totais;
});

const zonasOrdenadas = computed(() => {
  const t = totalGeralRiscos.value || 0;
  const calPct = (val: number) => (t > 0 ? ((val / t) * 100).toFixed(1) : '0.0');

  return [
    {
      chave: 'BAIXO',
      nome: 'Zona Baixo',
      intervalo: 'Score 1 a 2',
      descricaoApetite: 'Apetite institucional',
      total: totaisPorZona.value.BAIXO,
      percentual: calPct(totaisPorZona.value.BAIXO),
      corPonto: 'bg-emerald-500',
      corTextoTitulo: 'text-emerald-900',
      corTextoValor: 'text-emerald-700',
      corFundoCard: 'bg-emerald-50/40',
      corBorda: 'border-emerald-200/70',
      corBordaAtiva: 'border-emerald-500',
      corRing: 'ring-emerald-300',
      corBadgeDestaque: 'bg-emerald-600'
    },
    {
      chave: 'MEDIO',
      nome: 'Zona Médio',
      intervalo: 'Score 3 a 7',
      descricaoApetite: 'Tolerância aceitável',
      total: totaisPorZona.value.MEDIO,
      percentual: calPct(totaisPorZona.value.MEDIO),
      corPonto: 'bg-amber-500',
      corTextoTitulo: 'text-amber-900',
      corTextoValor: 'text-amber-700',
      corFundoCard: 'bg-amber-50/40',
      corBorda: 'border-amber-200/70',
      corBordaAtiva: 'border-amber-500',
      corRing: 'ring-amber-300',
      corBadgeDestaque: 'bg-amber-600'
    },
    {
      chave: 'ALTO',
      nome: 'Zona Alto',
      intervalo: 'Score 8 a 14',
      descricaoApetite: 'Acima do apetite (Plano de Ação)',
      total: totaisPorZona.value.ALTO,
      percentual: calPct(totaisPorZona.value.ALTO),
      corPonto: 'bg-orange-500',
      corTextoTitulo: 'text-orange-900',
      corTextoValor: 'text-orange-700',
      corFundoCard: 'bg-orange-50/40',
      corBorda: 'border-orange-200/70',
      corBordaAtiva: 'border-orange-500',
      corRing: 'ring-orange-300',
      corBadgeDestaque: 'bg-orange-600'
    },
    {
      chave: 'EXTREMO',
      nome: 'Zona Extremo',
      intervalo: 'Score 15 a 25',
      descricaoApetite: 'Tratamento urgente',
      total: totaisPorZona.value.EXTREMO,
      percentual: calPct(totaisPorZona.value.EXTREMO),
      corPonto: 'bg-rose-600',
      corTextoTitulo: 'text-rose-900',
      corTextoValor: 'text-rose-700',
      corFundoCard: 'bg-rose-50/40',
      corBorda: 'border-rose-200/70',
      corBordaAtiva: 'border-rose-500',
      corRing: 'ring-rose-300',
      corBadgeDestaque: 'bg-rose-600'
    }
  ];
});

const zonaMaiorConcentracao = computed(() => {
  const zonas = zonasOrdenadas.value;
  let maior = zonas[0];
  for (const z of zonas) {
    if (z.total > maior.total) {
      maior = z;
    }
  }
  return maior.total > 0 ? maior : null;
});
</script>

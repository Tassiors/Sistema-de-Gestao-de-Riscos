<template>
  <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
    <!-- Cabeçalho da Matriz com Alternância de Visão Residual / Inerente -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div>
        <div class="flex items-center gap-2">
          <h3 class="text-base font-bold text-gray-800">Matriz de Riscos</h3>
          <span 
            v-if="temMitigacao" 
            class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-900 border border-blue-200"
          >
            Mitigação Ativa
          </span>
        </div>
        <p class="text-xs text-gray-500">Tolerância Institucional ao Risco: até 7,99</p>
      </div>

      <!-- Seletor de Visão (Residual padrão vs Inerente) quando há mitigação ativa -->
      <div v-if="temMitigacao" class="flex items-center bg-gray-100 p-1 rounded-lg border border-gray-200 shrink-0">
        <button
          type="button"
          @click="modoVisao = 'RESIDUAL'"
          class="px-2.5 py-1 text-xs font-bold rounded-md transition-all flex items-center gap-1 cursor-pointer"
          :class="modoVisao === 'RESIDUAL' ? 'bg-white text-blue-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'"
        >
          <span>🎯</span>
          <span>Visão Residual (Pós-Controles)</span>
        </button>
        <button
          type="button"
          @click="modoVisao = 'INERENTE'"
          class="px-2.5 py-1 text-xs font-bold rounded-md transition-all flex items-center gap-1 cursor-pointer"
          :class="modoVisao === 'INERENTE' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'"
        >
          <span>⚡</span>
          <span>Visão Inerente (Bruta)</span>
        </button>
      </div>

      <!-- Legenda de cores tradicional se não houver mitigação ativa -->
      <div v-else class="flex items-center space-x-3 text-xs flex-wrap gap-y-1">
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-emerald-500 mr-1"></span> Baixo (≤2)</span>
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-amber-400 mr-1"></span> Médio (3-7)</span>
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-orange-500 mr-1"></span> Alto (8-14)</span>
        <span class="inline-flex items-center"><span class="w-3 h-3 rounded-full bg-rose-600 mr-1"></span> Extremo (15-25)</span>
      </div>
    </div>

    <!-- Grade 5x5: Bloqueada para toda e qualquer interação do usuário, com células de tamanho rigorosamente uniforme -->
    <div class="flex items-stretch select-none justify-center">
      <!-- Eixo Y: Título rotacionado -->
      <div class="flex items-center justify-center w-6 mr-1 select-none">
        <span class="-rotate-90 whitespace-nowrap text-[11px] uppercase text-gray-400 font-bold tracking-widest">
          Probabilidade
        </span>
      </div>

      <!-- Eixo Y: Rótulos das 5 Linhas perfeitamente alinhados -->
      <div class="grid grid-rows-5 gap-1.5 mr-2 text-xs font-semibold text-gray-600 text-right w-28 shrink-0">
        <div class="flex items-center justify-end">5 - Muito Alta</div>
        <div class="flex items-center justify-end">4 - Alta</div>
        <div class="flex items-center justify-end">3 - Média</div>
        <div class="flex items-center justify-end">2 - Baixa</div>
        <div class="flex items-center justify-end">1 - Muito Baixa</div>
      </div>

      <!-- Células da Matriz: 5 linhas x 5 colunas com tamanho rigorosamente uniforme (quadradas) e totalmente bloqueada para interação -->
      <div class="w-full max-w-[420px] aspect-square grid grid-cols-5 grid-rows-5 gap-1.5 pointer-events-none select-none">
        <template v-for="p in [5, 4, 3, 2, 1]" :key="'p-' + p">
          <template v-for="i in [1, 2, 3, 4, 5]" :key="'c-' + p + '-' + i">
            <div 
              :class="[
                getCellColor(p, i),
                isHighlight(p, i) 
                  ? 'ring-4 ring-blue-600 z-10 shadow-md' 
                  : 'opacity-90',
                'rounded-lg flex items-center justify-center text-white select-none relative w-full h-full aspect-square'
              ]"
            >
              <!-- Valor intrínseco e imutável da célula P x I -->
              <span class="text-sm font-bold leading-none select-none">{{ p * i }}</span>

              <!-- Badge de contagem se fornecido pelo painel -->
              <span 
                v-if="counts && counts[p + '_' + i]" 
                class="absolute bottom-1 right-1 text-[10px] bg-white/30 backdrop-blur-sm px-1.5 py-0.2 rounded-full font-bold"
              >
                {{ counts[p + '_' + i] }}
              </span>

              <!-- Tick Verde Badge Superior Direito da Célula Ativa -->
              <span 
                v-if="isHighlight(p, i)"
                class="absolute -top-1.5 -right-1.5 bg-emerald-600 text-white rounded-full p-0.5 shadow-md flex items-center justify-center z-20 pointer-events-none"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </span>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Eixo X: Impacto alinhado com as colunas -->
    <div class="flex items-center mt-2 select-none justify-center">
      <div class="w-6 mr-1 shrink-0"></div>
      <div class="w-28 mr-2 shrink-0"></div>
      <div class="w-full max-w-[420px] grid grid-cols-5 gap-1.5 text-xs font-semibold text-gray-600 text-center">
        <div>1 - Muito Baixo</div>
        <div>2 - Baixo</div>
        <div>3 - Médio</div>
        <div>4 - Alto</div>
        <div>5 - Muito Alto</div>
      </div>
    </div>

    <!-- Eixo X: Título centralizado -->
    <div class="flex items-center mt-1 select-none justify-center">
      <div class="w-6 mr-1 shrink-0"></div>
      <div class="w-28 mr-2 shrink-0"></div>
      <div class="w-full max-w-[420px] text-center text-xs uppercase text-gray-400 font-bold tracking-wider select-none">
        Impacto
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = withDefaults(
  defineProps<{
    counts?: Record<string, number>;
    activeP?: number | null;
    activeI?: number | null;
    activeResidual?: number | null;
    activeClassificacao?: string | null;
    fatorMitigacao?: number | null;
    nivelControle?: string | null;
  }>(),
  {
    fatorMitigacao: 1.0
  }
);

// Visão Residual é a opção padrão institucional obrigatória
const modoVisao = ref<'RESIDUAL' | 'INERENTE'>('RESIDUAL');

const temMitigacao = computed(() => {
  if (!props.activeP || !props.activeI) return false;
  const inerente = props.activeP * props.activeI;
  if (props.activeResidual !== null && props.activeResidual !== undefined && props.activeResidual < inerente) {
    return true;
  }
  return (
    props.fatorMitigacao !== null &&
    props.fatorMitigacao !== undefined &&
    props.fatorMitigacao < 1.0
  );
});

/**
 * Calcula a coordenada residual exata na matriz (P_res, I_res)
 * buscando a célula correspondente ao nível de risco residual mitigado.
 * Quando o risco está dentro do apetite (<= 7, <= 7.99 ou Muito Baixo, Baixo ou Médio),
 * a matriz DEVE OBRIGATORIAMENTE destacar a célula na área de tolerância (produto <= 7)
 * com o valor que mais se aproxima do residual (ex: 6 para residual 7).
 * NUNCA deve ser representada numa célula na região acima do apetite (produto > 7).
 */
const coordenadasResiduais = computed(() => {
  if (!props.activeP || !props.activeI) return { p: 1, i: 1 };
  const pIn = props.activeP;
  const iIn = props.activeI;
  const inerente = pIn * iIn;

  const fator = (props.fatorMitigacao !== null && props.fatorMitigacao !== undefined)
    ? Number(props.fatorMitigacao)
    : 1.0;

  // Valor numérico residual alvo (arredondado para a escala de avaliação institucional)
  const rawTarget = (props.activeResidual !== undefined && props.activeResidual !== null)
    ? Number(props.activeResidual)
    : inerente * fator;
  let target = Math.round(rawTarget);

  // Se tem mitigação ativa (fator < 1.0) mas o arredondamento manteve o mesmo valor, reduz para buscar célula mitigada
  if (fator < 1.0 && target >= inerente && inerente > 1) {
    target = Math.max(1, inerente - 1);
  }

  // Limite institucional do Colegiado Executivo: tolerância ao risco até 7,99 (Zona Verde e Amarela / Muito Baixo, Baixo ou Médio)
  const isClassifDentroApetite = props.activeClassificacao
    ? ['MUITO BAIXO', 'BAIXO', 'MEDIO'].includes(props.activeClassificacao.toUpperCase())
    : false;
  const residualDentroApetite = target <= 7 || rawTarget <= 7.99 || isClassifDentroApetite;

  if (target >= inerente && (!residualDentroApetite || inerente <= 7)) {
    return { p: pIn, i: iIn };
  }

  let melhorP = pIn;
  let melhorI = iIn;
  let menorDiff = Infinity;
  let melhorScore = Infinity;

  // Busca o par (p, i) com p <= pIn e i <= iIn
  for (let p = pIn; p >= 1; p--) {
    for (let i = iIn; i >= 1; i--) {
      const prod = p * i;

      // REGRA INSTITUCIONAL MANDATÓRIA:
      // Se o residual está dentro do apetite (<= 7), a célula DEVE obrigatoriamente estar na zona de tolerância (prod <= 7)
      if (residualDentroApetite && prod > 7) continue;

      // Se o residual está acima do apetite (> 7) e inerente > 7, a célula DEVE obrigatoriamente estar acima da tolerância (prod > 7)
      if (!residualDentroApetite && prod <= 7 && inerente > 7) continue;

      // Quando há mitigação ou redução de risco, prefere coordenadas diferentes da inerente
      if (p === pIn && i === iIn && (fator < 1.0 || target < inerente) && menorDiff !== Infinity) continue;

      const diff = Math.abs(prod - target);
      // Controles atuam prioritariamente reduzindo probabilidade mantendo impacto estável
      const distP = Math.abs(p - (target / iIn));
      const distI = Math.abs(i - iIn);
      const score = diff * 100 + distP * 10 + distI;

      if (diff < menorDiff || (diff === menorDiff && score < melhorScore)) {
        menorDiff = diff;
        melhorScore = score;
        melhorP = p;
        melhorI = i;
      }
    }
  }

  // Fallback 1: se nenhuma célula atendeu com as restrições estritas dentro de (pIn, iIn)
  if (menorDiff === Infinity || (residualDentroApetite && melhorP * melhorI > 7)) {
    menorDiff = Infinity;
    for (let p = pIn; p >= 1; p--) {
      for (let i = iIn; i >= 1; i--) {
        const prod = p * i;
        if (residualDentroApetite && prod > 7) continue;
        if (!residualDentroApetite && prod <= 7 && inerente > 7) continue;

        const diff = Math.abs(prod - target);
        if (diff < menorDiff) {
          menorDiff = diff;
          melhorP = p;
          melhorI = i;
        }
      }
    }
  }

  // Fallback 2: garantia estrita de apetite
  // Se o residual está dentro do apetite mas o produto selecionado ainda for > 7,
  // varre TODA a matriz procurando a célula de tolerância (prod <= 7) mais próxima do residual
  if (residualDentroApetite && melhorP * melhorI > 7) {
    menorDiff = Infinity;
    for (let p = 5; p >= 1; p--) {
      for (let i = 5; i >= 1; i--) {
        const prod = p * i;
        if (prod <= 7) {
          const diff = Math.abs(prod - target);
          if (diff < menorDiff) {
            menorDiff = diff;
            melhorP = p;
            melhorI = i;
          }
        }
      }
    }
  } else if (!residualDentroApetite && inerente > 7 && melhorP * melhorI <= 7) {
    menorDiff = Infinity;
    for (let p = 5; p >= 1; p--) {
      for (let i = 5; i >= 1; i--) {
        const prod = p * i;
        if (prod > 7) {
          const diff = Math.abs(prod - target);
          if (diff < menorDiff) {
            menorDiff = diff;
            melhorP = p;
            melhorI = i;
          }
        }
      }
    }
  }

  return { p: melhorP, i: melhorI };
});

// Coordenada ativa a ser destacada com base no modo de visão
const celulaAtiva = computed(() => {
  if (!props.activeP || !props.activeI) return null;
  if (modoVisao.value === 'RESIDUAL') {
    if (temMitigacao.value || (props.activeResidual !== null && props.activeResidual !== undefined)) {
      return coordenadasResiduais.value;
    }
  }
  return { p: props.activeP, i: props.activeI };
});

function isHighlight(p: number, i: number): boolean {
  if (!celulaAtiva.value) return false;
  return celulaAtiva.value.p === p && celulaAtiva.value.i === i;
}

function getCellColor(p: number, i: number): string {
  // As cores das células são fixas baseadas na escala institucional P x I
  const inerente = p * i;
  if (inerente <= 2) return 'bg-emerald-500';
  if (inerente <= 7) return 'bg-amber-400 text-gray-900';
  if (inerente <= 14) return 'bg-orange-500';
  return 'bg-rose-600';
}
</script>

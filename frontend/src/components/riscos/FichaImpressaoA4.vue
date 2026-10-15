<template>
  <div v-if="listaFichas && listaFichas.length > 0" id="secao-relatorio-impressao" class="hidden print:block text-gray-900 bg-white font-sans max-w-[99%] mx-auto">
    <div 
      v-for="(dadosFicha, fIdx) in listaFichas" 
      :key="dadosFicha.id || fIdx"
      class="ficha-documento-item"
      :class="{ 'quebra-pagina-ficha': fIdx < listaFichas.length - 1 }"
    >
      <!-- Cabeçalho Institucional -->
      <div class="bloco-impressao border-b-2 border-blue-900 pb-2.5 mb-3 flex justify-between items-start">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 bg-blue-900 text-white rounded-lg flex items-center justify-center font-black text-lg tracking-tighter">
            HC
          </div>
          <div>
            <h1 class="text-sm font-extrabold uppercase text-blue-950 tracking-wide">Hospital das Clínicas da UFPE / EBSERH</h1>
            <p class="text-[11px] text-gray-700 font-semibold">UGERC - Unidade de Gestão de Riscos e Controles Internos</p>
          </div>
        </div>
        <div class="text-right">
          <span class="inline-block px-2.5 py-0.5 rounded border text-[11px] font-bold"
                :class="dadosFicha.status === 'HOMOLOGADO' ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : dadosFicha.status === 'SUBMETIDO' ? 'border-blue-500 bg-blue-50 text-blue-800' : 'border-amber-500 bg-amber-50 text-amber-800'">
            STATUS: {{ dadosFicha.status || 'RASCUNHO' }}
          </span>
          <p class="text-[10px] text-gray-500 mt-0.5">Ficha ID #{{ dadosFicha.id || 'NOVA' }}</p>
          <p class="text-[10px] text-gray-400">Emissão: {{ dataHoraAtual }}</p>
        </div>
      </div>

      <div class="bloco-impressao text-center mb-3">
        <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wide">Ficha Completa de Mapeamento de Risco</h2>
        <p class="text-[11px] text-gray-600">Relatório Unificado das 5 Etapas Metodológicas UGERC</p>
      </div>

      <!-- 1. Contexto e Processo -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>1. Entendimento do Contexto e Processo Hospitalar</span>
          <span class="text-[10px] font-normal text-gray-600">Etapa 1</span>
        </div>
        <div class="p-2.5 text-xs space-y-2">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <span class="font-bold text-gray-700 block text-[11px]">Unidade Organizacional:</span>
              <span class="text-gray-900">{{ getNomeUnidade(dadosFicha) }}</span>
            </div>
            <div>
              <span class="font-bold text-gray-700 block text-[11px]">Processo / Macroprocesso:</span>
              <span class="text-gray-900">{{ getNomeProcesso(dadosFicha) }}</span>
            </div>
          </div>

          <!-- Exibir Pilar Estratégico e Projeto Vinculado APENAS se houver registro destes na ficha -->
          <div 
            v-if="getNomePilar(dadosFicha) || (dadosFicha.possui_projeto && dadosFicha.nome_projeto)" 
            class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 border-t border-gray-100"
          >
            <div v-if="getNomePilar(dadosFicha)">
              <span class="font-bold text-gray-700 block text-[11px]">Pilar Estratégico HC-UFPE:</span>
              <span class="text-gray-900">{{ getNomePilar(dadosFicha) }}</span>
            </div>
            <div v-if="dadosFicha.possui_projeto && dadosFicha.nome_projeto">
              <span class="font-bold text-gray-700 block text-[11px]">Projeto Vinculado:</span>
              <span class="text-gray-900">{{ dadosFicha.nome_projeto }}</span>
            </div>
          </div>

          <div class="pt-1 border-t border-gray-100">
            <span class="font-bold text-gray-700 block text-[11px]">Entrega Esperada do Processo:</span>
            <p class="text-gray-800 italic bg-gray-50/70 p-2 rounded border border-gray-200 mt-0.5 whitespace-pre-wrap">{{ dadosFicha.entrega_processo || 'Não informada' }}</p>
          </div>
        </div>
      </div>

      <!-- 2. Identificação do Risco -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>2. Identificação do Risco</span>
          <span class="text-[10px] font-normal text-gray-600">Etapa 2</span>
        </div>
        <div class="p-2.5 text-xs space-y-2">
          <div class="flex items-center gap-2">
            <span class="font-bold text-gray-700 text-[11px]">Categoria do Risco:</span>
            <span class="px-2 py-0.5 bg-blue-100 text-blue-900 font-bold rounded text-[10px] border border-blue-200">
              {{ getEventoPrincipal(dadosFicha)?.categoria || 'Geral' }}
            </span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-1">
            <div class="p-2 rounded bg-gray-50/70 border border-gray-200">
              <span class="font-bold text-gray-700 block text-[10px] uppercase">Causa (Origem / Fator)</span>
              <p class="text-gray-900 mt-0.5 text-[11px]">{{ getEventoPrincipal(dadosFicha)?.causa || 'Não preenchida' }}</p>
            </div>
            <div class="p-2 rounded bg-gray-50/70 border border-gray-200">
              <span class="font-bold text-gray-700 block text-[10px] uppercase">Evento de Risco</span>
              <p class="text-gray-900 mt-0.5 font-semibold text-rose-950 text-[11px]">{{ getEventoPrincipal(dadosFicha)?.descricao_evento || 'Não preenchido' }}</p>
            </div>
            <div class="p-2 rounded bg-gray-50/70 border border-gray-200">
              <span class="font-bold text-gray-700 block text-[10px] uppercase">Consequência (Impacto)</span>
              <p class="text-gray-900 mt-0.5 text-[11px]">{{ getEventoPrincipal(dadosFicha)?.consequencia || 'Não preenchida' }}</p>
            </div>
          </div>
          <div class="p-2 bg-blue-50/60 rounded border border-blue-200 text-blue-950 text-[11px]">
            <span class="font-bold block text-[10px] text-blue-900 mb-0.5">Declaração Integrada do Risco:</span>
            <em>"Devido a {{ getEventoPrincipal(dadosFicha)?.causa || '[Causa]' }}, pode ocorrer {{ getEventoPrincipal(dadosFicha)?.descricao_evento || '[Evento]' }}, resultando em {{ getEventoPrincipal(dadosFicha)?.consequencia || '[Consequência]' }}."</em>
          </div>
        </div>
      </div>

      <!-- 3 e 4. Avaliação e Controles Existentes -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>3 e 4. Avaliação e Controles Existentes</span>
          <span class="text-[10px] font-normal text-gray-600">Etapas 3 e 4</span>
        </div>
        <div class="p-2.5 text-xs space-y-2.5">
          <div class="grid grid-cols-4 gap-2 text-center">
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Probabilidade</span>
              <span class="text-sm font-extrabold text-gray-900">{{ getAvaliacaoPrincipal(dadosFicha)?.probabilidade || '-' }}</span>
              <span class="text-[9px] text-gray-600 block">{{ getRotuloProbabilidade(dadosFicha) }}</span>
            </div>
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Impacto</span>
              <span class="text-sm font-extrabold text-gray-900">{{ getAvaliacaoPrincipal(dadosFicha)?.impacto || '-' }}</span>
              <span class="text-[9px] text-gray-600 block">{{ getRotuloImpacto(dadosFicha) }}</span>
            </div>
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Risco Inerente</span>
              <span class="text-sm font-extrabold text-blue-900">{{ getRiscoInerenteCalculado(dadosFicha) }}</span>
              <span class="text-[9px] text-gray-500 block">P × I</span>
            </div>
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Controles / FNC</span>
              <span class="text-sm font-extrabold text-gray-900">{{ getAvaliacaoPrincipal(dadosFicha)?.fator_mitigacao ?? 1.0 }}</span>
              <span class="text-[9px] text-gray-600 block truncate">{{ getRotuloControle(dadosFicha) }}</span>
            </div>
          </div>

          <div class="p-2 rounded border flex items-center justify-between"
               :class="isAcimaApetite(dadosFicha) ? 'bg-rose-50 border-rose-300 text-rose-950' : 'bg-emerald-50 border-emerald-300 text-emerald-950'">
            <div>
              <span class="text-[9px] font-bold uppercase tracking-wider block">
                {{ isAcimaApetite(dadosFicha) ? '⚠️ ACIMA DO APETITE A RISCO (> 7,99)' : '🛡️ DENTRO DO APETITE A RISCO (≤ 7,99)' }}
              </span>
              <p class="text-[11px] mt-0.5">
                {{ isAcimaApetite(dadosFicha) ? 'Este risco ultrapassa a tolerância da organização e exige tratamento compulsório (Plano de Ação e Contingência).' : 'Este risco está dentro da tolerância institucional. Tratamento complementar pode ser adotado voluntariamente.' }}
              </p>
            </div>
            <div class="text-right pl-3 shrink-0">
              <span class="text-[10px] uppercase font-bold block">Risco Residual:</span>
              <span class="text-xl font-black">{{ getRiscoResidualCalculado(dadosFicha) }}</span>
              <span class="text-[9px] uppercase font-bold block">({{ getClassificacaoCalculada(dadosFicha) }})</span>
            </div>
          </div>

          <!-- Controles Internos Existentes -->
          <div>
            <span class="font-bold text-gray-700 block mb-0.5 text-[11px]">Controles Internos Existentes Registrados:</span>
            <div v-if="!getAvaliacaoPrincipal(dadosFicha)?.controles || getAvaliacaoPrincipal(dadosFicha).controles.length === 0" class="text-gray-400 italic text-[11px]">
              Nenhum controle formal associado (Nível Inexistente / FNC 1.0).
            </div>
            <ol v-else class="list-decimal pl-5 space-y-0.5 text-gray-800 text-[11px]">
              <li v-for="(c, cIdx) in getAvaliacaoPrincipal(dadosFicha).controles" :key="cIdx">
                {{ c.descricao_controle }}
              </li>
            </ol>
          </div>
        </div>
      </div>

      <!-- 5. Planos de Ação e Contingência -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>5. Tratamento, Planos de Ação e Contingência</span>
          <span class="text-[10px] font-normal text-gray-600">Etapa 5</span>
        </div>
        <div class="p-2.5 text-xs space-y-3">
          <!-- Tabela de Planos de Ação -->
          <div>
            <h4 class="font-bold text-gray-800 uppercase text-[11px] mb-1">Planos de Ação</h4>
            <div v-if="!getEventoPrincipal(dadosFicha)?.planos_acao || getEventoPrincipal(dadosFicha).planos_acao.length === 0" class="text-gray-400 italic bg-gray-50 p-2 rounded border text-[11px]">
              Nenhum plano de ação cadastrado.
            </div>
            <table v-else class="w-full text-left border-collapse border border-gray-300 text-[10px] table-fixed">
              <thead>
                <tr class="bg-gray-100 border-b border-gray-300">
                  <th class="p-1 border-r border-gray-300 font-bold w-[5%] text-center">#</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[15%]">Tipo</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[32%]">O que fazer?</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[26%]">Como?</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[12%]">Quem?</th>
                  <th class="p-1 font-bold w-[10%]">Prazo</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="(pa, paIdx) in getEventoPrincipal(dadosFicha).planos_acao" :key="paIdx">
                  <td class="p-1 border-r border-gray-200 text-center font-bold">{{ paIdx + 1 }}</td>
                  <td class="p-1 border-r border-gray-200 font-semibold">{{ pa.tipo_resposta }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pa.o_que }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pa.como }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pa.quem }}</td>
                  <td class="p-1">{{ pa.data_inicio ? `${pa.data_inicio} até ${pa.data_termino}` : '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Tabela de Contingência -->
          <div>
            <div class="flex items-center gap-2 mb-1">
              <h4 class="font-bold text-gray-800 uppercase text-[11px]">Planos de Contingência</h4>
              <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-gray-100 text-gray-600 border border-gray-200">
                OPCIONAL
              </span>
            </div>
            <div v-if="!getEventoPrincipal(dadosFicha)?.planos_contingencia || getEventoPrincipal(dadosFicha).planos_contingencia.length === 0" class="text-gray-400 italic bg-gray-50 p-2 rounded border text-[11px]">
              Nenhum plano de contingência cadastrado.
            </div>
            <table v-else class="w-full text-left border-collapse border border-gray-300 text-[10px] table-fixed">
              <thead>
                <tr class="bg-gray-100 border-b border-gray-300">
                  <th class="p-1 border-r border-gray-300 font-bold w-[5%] text-center">#</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[28%]">Gatilho (Trigger)</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[17%]">Responsável</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[25%]">O que fazer?</th>
                  <th class="p-1 font-bold w-[25%]">Como agir?</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="(pc, pcIdx) in getEventoPrincipal(dadosFicha).planos_contingencia" :key="pcIdx">
                  <td class="p-1 border-r border-gray-200 text-center font-bold">{{ pcIdx + 1 }}</td>
                  <td class="p-1 border-r border-gray-200 font-semibold text-rose-900">{{ pc.gatilho }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pc.responsavel }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pc.o_que }}</td>
                  <td class="p-1">{{ pc.como }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Assinaturas e Homologação -->
      <div class="bloco-impressao mt-4 pt-4 border-t border-gray-300 grid grid-cols-2 gap-10 text-center text-xs">
        <div>
          <div class="border-b border-gray-400 mb-1 pb-6"></div>
          <p class="font-bold text-gray-800 text-[11px]">Responsável pelo Mapeamento</p>
          <p class="text-[10px] text-gray-500">{{ dadosFicha.unidade?.nome || dadosFicha.unidade_nome || 'Gestor da Unidade Organizacional' }}</p>
        </div>
        <div>
          <div class="border-b border-gray-400 mb-1 pb-6"></div>
          <p class="font-bold text-gray-800 text-[11px]">UGERC / Governança Institucional</p>
          <p class="text-[10px] text-gray-500">Unidade de Gestão de Riscos e Controles Internos - HC-UFPE</p>
        </div>
      </div>

      <!-- Divisor HTML explícito de Quebra de Página entre Fichas Distintas -->
      <div 
        v-if="fIdx < listaFichas.length - 1" 
        class="divisor-quebra-pagina-html"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  ficha?: any;
  fichas?: any[];
}>();

const listaFichas = computed(() => {
  if (props.fichas && props.fichas.length > 0) {
    return props.fichas;
  }
  if (props.ficha) {
    return [props.ficha];
  }
  return [];
});

const dataHoraAtual = computed(() => {
  return new Date().toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
});

function getNomeUnidade(f: any): string {
  if (!f) return 'Não informada';
  const nome = f.unidade?.nome || f.unidade_nome;
  const sigla = f.unidade?.sigla || f.unidade_sigla;
  if (!nome) return 'Não informada';
  return sigla ? `${nome} (${sigla})` : nome;
}

function getNomeProcesso(f: any): string {
  if (!f) return 'Não selecionado';
  if (f.processo_outro) {
    return `${f.processo_outro} (Outro Processo)`;
  }
  const proc = f.processo;
  const nomeProc = proc?.nome || f.processo_nome;
  if (!nomeProc) return 'Não selecionado';
  const macro = proc?.macroprocesso?.nome || proc?.macroprocessoNome || f.macroprocesso_nome || 'Processo Hospitalar';
  return `${nomeProc} [${macro}]`;
}

function getNomePilar(f: any): string | null {
  if (!f) return null;
  return f.pilar_estrategico?.nome || f.pilar_estrategico_nome || null;
}

function getEventoPrincipal(f: any): any {
  if (!f) return null;
  if (f.eventos && f.eventos.length > 0) {
    return f.eventos[0];
  }
  return f.evento || null;
}

function getAvaliacaoPrincipal(f: any): any {
  const ev = getEventoPrincipal(f);
  return ev?.avaliacao || null;
}

const rotulosProb: Record<number, string> = {
  1: 'Muito Baixa',
  2: 'Baixa',
  3: 'Média',
  4: 'Alta',
  5: 'Muito Alta'
};

const rotulosImp: Record<number, string> = {
  1: 'Insignificante',
  2: 'Menor',
  3: 'Moderado',
  4: 'Maior',
  5: 'Crítico'
};

function getRotuloProbabilidade(f: any): string {
  const av = getAvaliacaoPrincipal(f);
  const p = av?.probabilidade;
  return p ? rotulosProb[p] || '' : '';
}

function getRotuloImpacto(f: any): string {
  const av = getAvaliacaoPrincipal(f);
  const i = av?.impacto;
  return i ? rotulosImp[i] || '' : '';
}

function getRotuloControle(f: any): string {
  const av = getAvaliacaoPrincipal(f);
  if (!av) return 'Inexistente';
  const nc = av.nivel_controle;
  if (nc) {
    const mapa: Record<string, string> = {
      INEXISTENTE: 'Inexistente',
      FRACO: 'Fraco',
      MEDIANO: 'Mediano',
      SATISFATORIO: 'Satisfatório',
      FORTE: 'Forte'
    };
    return mapa[nc] || nc;
  }
  const fm = av.fator_mitigacao;
  if (fm === 1.0) return 'Inexistente';
  if (fm === 0.8) return 'Fraco';
  if (fm === 0.6) return 'Mediano';
  if (fm === 0.4) return 'Satisfatório';
  if (fm === 0.2) return 'Forte';
  return 'Inexistente';
}

function getRiscoInerenteCalculado(f: any): string | number {
  const av = getAvaliacaoPrincipal(f);
  if (!av) return '-';
  if (av.risco_inerente !== undefined && av.risco_inerente !== null) return av.risco_inerente;
  if (av.probabilidade && av.impacto) return av.probabilidade * av.impacto;
  return '-';
}

function getRiscoResidualCalculado(f: any): string | number {
  const av = getAvaliacaoPrincipal(f);
  if (!av) return '-';
  if (av.risco_residual !== undefined && av.risco_residual !== null) return av.risco_residual;
  return '-';
}

function getClassificacaoCalculada(f: any): string {
  const av = getAvaliacaoPrincipal(f);
  if (!av) return 'BAIXO';
  if (av.classificacao) return av.classificacao;
  const rrVal = getRiscoResidualCalculado(f);
  const rr = typeof rrVal === 'number' ? rrVal : parseFloat(rrVal as string);
  if (isNaN(rr)) return 'BAIXO';
  if (rr <= 2.0) return 'BAIXO';
  if (rr <= 7.99) return 'MÉDIO';
  if (rr <= 14.99) return 'ALTO';
  return 'EXTREMO';
}

function isAcimaApetite(f: any): boolean {
  const av = getAvaliacaoPrincipal(f);
  if (!av) return false;
  if (av.acima_apetite !== undefined && av.acima_apetite !== null) return Boolean(av.acima_apetite);
  const rrVal = getRiscoResidualCalculado(f);
  const rr = typeof rrVal === 'number' ? rrVal : parseFloat(rrVal as string);
  return !isNaN(rr) && rr > 7.99;
}


</script>

<style>
@media print {
  @page {
    size: A4 portrait;
    margin: 8mm 7mm !important;
  }
  
  #secao-relatorio-impressao {
    display: block !important;
    width: 100% !important;
    max-width: 99% !important;
    font-size: 11px !important;
    line-height: 1.3 !important;
    background: #ffffff !important;
    box-sizing: border-box !important;
    margin: 0 auto !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .ficha-documento-item {
    display: block !important;
    position: relative !important;
    width: 100% !important;
    box-sizing: border-box !important;
    clear: both !important;
    page-break-before: always !important;
    break-before: page !important;
    page-break-after: always !important;
    break-after: page !important;
    padding-bottom: 4mm !important;
  }

  .ficha-documento-item:first-child {
    page-break-before: avoid !important;
    break-before: avoid !important;
  }

  .ficha-documento-item:last-child {
    page-break-after: avoid !important;
    break-after: avoid !important;
  }

  .quebra-pagina-ficha {
    page-break-after: always !important;
    break-after: page !important;
  }

  .divisor-quebra-pagina-html {
    page-break-after: always !important;
    break-after: page !important;
    clear: both !important;
    display: block !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
  }

  .bloco-impressao {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    margin-bottom: 8px !important;
    box-sizing: border-box !important;
  }

  table {
    page-break-inside: avoid !important;
    width: 100% !important;
    max-width: 100% !important;
    table-layout: fixed !important;
    box-sizing: border-box !important;
  }

  th, td {
    word-break: break-word !important;
    overflow-wrap: break-word !important;
  }
}
</style>

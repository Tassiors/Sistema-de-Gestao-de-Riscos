<template>
  <div>
    <!-- Conteúdo Visual da Tela (Oculto estritamente durante a impressão) -->
    <div class="max-w-6xl mx-auto space-y-6 pb-16 print:hidden">
      
      <!-- Estado de Carregamento -->
      <div v-if="carregando" class="bg-white p-12 rounded-xl shadow-sm border border-gray-200 text-center">
        <span class="inline-block animate-spin text-3xl mb-3">⏳</span>
        <p class="text-sm font-semibold text-gray-700">Carregando detalhes da ficha de risco...</p>
        <p class="text-xs text-gray-400 mt-1">Aguarde enquanto os dados metodológicos são consultados.</p>
      </div>

      <!-- Estado de Erro -->
      <div v-else-if="erroCarregamento" class="bg-white p-10 rounded-xl shadow-sm border border-rose-200 text-center">
        <div class="text-4xl mb-3">⚠️</div>
        <h3 class="text-base font-bold text-gray-900">Não foi possível carregar a ficha de risco</h3>
        <p class="text-xs text-rose-600 mt-1">{{ erroCarregamento }}</p>
        <div class="mt-6 flex justify-center gap-3">
          <router-link
            to="/riscos/mapeados"
            class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg transition"
          >
            ← Voltar para Fichas Cadastradas
          </router-link>
          <button
            @click="carregarFicha"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition"
          >
            Tentar Novamente
          </button>
        </div>
      </div>

      <!-- Conteúdo da Ficha -->
      <template v-else-if="ficha">
        <!-- Barra Superior de Navegação e Ações Rápidas -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <router-link
            to="/riscos/mapeados"
            class="inline-flex items-center gap-1.5 text-xs font-bold text-gray-600 hover:text-blue-700 transition px-2.5 py-1.5 rounded-lg hover:bg-gray-100"
          >
            <span>←</span>
            <span>Voltar para Fichas Cadastradas</span>
          </router-link>

          <div class="flex items-center gap-2 flex-wrap">
            <!-- Botão Editar -->
            <router-link
              v-if="ficha.pode_editar"
              :to="'/riscos/' + ficha.id + '/editar'"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-xs transition"
              title="Editar esta ficha de risco"
            >
              <span>✏️</span>
              <span>Editar Ficha</span>
            </router-link>
            <span
              v-else
              class="inline-flex items-center gap-1 px-3 py-2 bg-gray-100 text-gray-500 text-xs font-medium rounded-lg border border-gray-200 cursor-not-allowed"
              title="Apenas o gestor da própria unidade ou administrador pode editar esta ficha"
            >
              <span>🔒</span>
              <span>Somente Leitura</span>
            </span>

            <!-- Botão Imprimir -->
            <button
              @click="imprimirFicha"
              type="button"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition cursor-pointer"
              title="Imprimir ficha completa em formato A4 da UGERC"
            >
              <span>🖨️</span>
              <span>Imprimir Ficha (PDF/A4)</span>
            </button>

            <!-- Botão Excluir -->
            <button
              v-if="ficha.pode_excluir"
              @click="confirmarExclusao"
              :disabled="excluindo"
              type="button"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-xs transition cursor-pointer disabled:opacity-50"
              title="Excluir permanentemente esta ficha de risco"
            >
              <span v-if="!excluindo">🗑️</span>
              <span v-else class="animate-spin">⏳</span>
              <span>{{ excluindo ? 'Excluindo...' : 'Excluir Ficha' }}</span>
            </button>
          </div>
        </div>

        <!-- Banner do Cabeçalho Executivo -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-gray-100 pb-5">
            <div>
              <div class="flex items-center gap-2.5 flex-wrap">
                <span class="text-xs font-mono font-bold bg-blue-100 text-blue-900 px-2 py-0.5 rounded border border-blue-200">
                  Ficha #{{ ficha.id }}
                </span>
                <span 
                  v-if="ficha.tag_versao" 
                  class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200"
                >
                  {{ ficha.tag_versao }}
                </span>
                <span 
                  :class="getStatusBadge(ficha.status)"
                  class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border"
                >
                  STATUS: {{ ficha.status }}
                </span>
              </div>
              <h1 class="text-lg sm:text-xl font-extrabold text-gray-900 mt-2 flex items-center gap-2">
                <span>{{ nomeProcesso }}</span>
              </h1>
              <p class="text-xs text-gray-500 mt-1 flex items-center gap-2 flex-wrap">
                <span>🏛️ {{ nomeUnidade }}</span>
                <span>•</span>
                <span>Macroprocesso: {{ nomeMacroprocesso }}</span>
              </p>
            </div>

            <!-- Card Resumo de Severidade -->
            <div class="flex items-center gap-4 bg-gray-50 p-3.5 rounded-xl border border-gray-200 shrink-0">
              <div class="text-right">
                <span class="text-[10px] font-bold text-gray-400 uppercase block tracking-wider">Severidade Residual</span>
                <div class="flex items-center justify-end gap-2 mt-0.5">
                  <span class="text-xl font-black text-gray-900">
                    {{ avaliacaoPrincipal?.risco_residual ?? '-' }}
                  </span>
                  <span 
                    :class="getClassificacaoBadge(classificacaoCalculada)"
                    class="px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase border"
                  >
                    {{ classificacaoCalculada }}
                  </span>
                </div>
              </div>
              <div 
                class="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-black"
                :class="getIconeSeveridadeBg(classificacaoCalculada)"
              >
                {{ getIconeSeveridade(classificacaoCalculada) }}
              </div>
            </div>
          </div>

          <!-- Seletor de Eventos de Risco (quando houver múltiplos eventos na mesma ficha) -->
          <div v-if="ficha.eventos && ficha.eventos.length > 1" class="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-gray-600">Eventos de Risco ({{ ficha.eventos.length }}):</span>
            <button
              v-for="(ev, idx) in ficha.eventos"
              :key="ev.id || idx"
              type="button"
              @click="eventoSelecionadoIndex = idx"
              :class="eventoSelecionadoIndex === idx ? 'bg-blue-600 text-white shadow-xs' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
              class="px-3 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
            >
              <span>Evento #{{ idx + 1 }}</span>
              <span class="max-w-[140px] truncate text-[11px] opacity-90">({{ ev.descricao_evento }})</span>
            </button>
          </div>

          <!-- Declaração Integrada do Risco (Destaque) -->
          <div class="mt-4 p-4 rounded-xl bg-gradient-to-r from-blue-50/80 to-indigo-50/60 border border-blue-200 text-blue-950">
            <span class="text-[10px] font-bold uppercase tracking-wider text-blue-800 block mb-1">
              📢 Declaração Integrada do Risco (Causa → Evento → Consequência)
            </span>
            <p class="text-xs sm:text-sm font-medium leading-relaxed italic text-gray-900">
              "Devido a <strong class="text-blue-900 not-italic">{{ eventoPrincipal?.causa || '[Causa não informada]' }}</strong>, 
              pode ocorrer <strong class="text-rose-950 not-italic">{{ eventoPrincipal?.descricao_evento || '[Evento não informado]' }}</strong>, 
              resultando em <strong class="text-amber-950 not-italic">{{ eventoPrincipal?.consequencia || '[Consequência não informada]' }}</strong>."
            </p>
          </div>
        </div>

        <!-- Grade de Detalhes da Metodologia UGERC (Etapas 1 a 5) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <!-- 1. Entendimento do Contexto e Processo -->
          <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
            <div class="flex items-center justify-between border-b border-gray-100 pb-2.5">
              <h3 class="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
                <span class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">1</span>
                <span>Contexto e Processo Hospitalar</span>
              </h3>
              <span class="text-[10px] text-gray-400 font-semibold">Etapa 1</span>
            </div>

            <div class="space-y-3 text-xs">
              <div>
                <span class="text-[11px] font-bold text-gray-500 block">Unidade Organizacional</span>
                <span class="text-gray-900 font-semibold">{{ nomeUnidade }}</span>
              </div>

              <div>
                <span class="text-[11px] font-bold text-gray-500 block">Processo / Macroprocesso</span>
                <span class="text-gray-900 font-semibold">{{ nomeProcesso }}</span>
                <span class="text-gray-500 block text-[11px] mt-0.5">Macroprocesso: {{ nomeMacroprocesso }}</span>
              </div>

              <div v-if="ficha.pilar_estrategico?.nome">
                <span class="text-[11px] font-bold text-gray-500 block">Pilar Estratégico HC-UFPE</span>
                <span class="text-gray-900">{{ ficha.pilar_estrategico.nome }}</span>
              </div>

              <div v-if="ficha.possui_projeto && ficha.nome_projeto">
                <span class="text-[11px] font-bold text-gray-500 block">Projeto Vinculado</span>
                <span class="text-blue-700 font-semibold">🚀 {{ ficha.nome_projeto }}</span>
              </div>

              <div>
                <span class="text-[11px] font-bold text-gray-500 block">Entrega Esperada do Processo</span>
                <p class="text-gray-800 bg-gray-50 p-2.5 rounded-lg border border-gray-200 mt-1 whitespace-pre-wrap leading-relaxed">
                  {{ ficha.entrega_processo || 'Não informada' }}
                </p>
              </div>
            </div>
          </div>

          <!-- 2. Identificação do Risco -->
          <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
            <div class="flex items-center justify-between border-b border-gray-100 pb-2.5">
              <h3 class="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
                <span class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">2</span>
                <span>Identificação do Risco</span>
              </h3>
              <span class="text-[10px] text-gray-400 font-semibold">Etapa 2</span>
            </div>

            <div class="space-y-3 text-xs">
              <div>
                <span class="text-[11px] font-bold text-gray-500 block">Categoria do Risco</span>
                <span class="inline-block mt-0.5 px-2.5 py-0.5 bg-blue-50 text-blue-800 border border-blue-200 font-bold rounded text-[11px]">
                  {{ eventoPrincipal?.categoria || 'Geral' }}
                </span>
              </div>

              <div class="p-2.5 rounded-lg bg-gray-50 border border-gray-200">
                <span class="text-[10px] font-bold uppercase text-gray-500 block">Causa (Origem / Fator)</span>
                <p class="text-gray-900 mt-1 font-medium">{{ eventoPrincipal?.causa || 'Não preenchida' }}</p>
              </div>

              <div class="p-2.5 rounded-lg bg-rose-50/60 border border-rose-200">
                <span class="text-[10px] font-bold uppercase text-rose-800 block">Evento de Risco</span>
                <p class="text-rose-950 mt-1 font-bold">{{ eventoPrincipal?.descricao_evento || 'Não preenchido' }}</p>
              </div>

              <div class="p-2.5 rounded-lg bg-gray-50 border border-gray-200">
                <span class="text-[10px] font-bold uppercase text-gray-500 block">Consequência (Impacto)</span>
                <p class="text-gray-900 mt-1 font-medium">{{ eventoPrincipal?.consequencia || 'Não preenchida' }}</p>
              </div>
            </div>
          </div>

        </div>

        <!-- 3 e 4. Avaliação e Controles Existentes (Matriz 5x5) -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-5">
          <div class="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 class="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
              <span class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">3/4</span>
              <span>Avaliação do Risco e Controles Existentes</span>
            </h3>
            <span class="text-[10px] text-gray-400 font-semibold">Etapas 3 e 4</span>
          </div>

          <!-- Cards das Métricas 5x5 -->
          <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-center">
            <!-- Probabilidade -->
            <div class="p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span class="text-[10px] uppercase font-bold text-gray-500 block">Probabilidade</span>
              <span class="text-lg font-black text-gray-900 mt-0.5 block">
                {{ avaliacaoPrincipal?.probabilidade || '-' }}
              </span>
              <span class="text-[10px] text-gray-600 font-medium block">
                {{ rotulosProb[avaliacaoPrincipal?.probabilidade] || '' }}
              </span>
            </div>

            <!-- Impacto -->
            <div class="p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span class="text-[10px] uppercase font-bold text-gray-500 block">Impacto</span>
              <span class="text-lg font-black text-gray-900 mt-0.5 block">
                {{ avaliacaoPrincipal?.impacto || '-' }}
              </span>
              <span class="text-[10px] text-gray-600 font-medium block">
                {{ rotulosImp[avaliacaoPrincipal?.impacto] || '' }}
              </span>
            </div>

            <!-- Risco Inerente -->
            <div class="p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span class="text-[10px] uppercase font-bold text-gray-500 block">Risco Inerente</span>
              <span class="text-lg font-black text-gray-900 mt-0.5 block">
                {{ riscoInerenteCalculado }}
              </span>
              <span class="text-[10px] text-gray-400 block">(P × I)</span>
            </div>

            <!-- Nível dos Controles -->
            <div class="p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span class="text-[10px] uppercase font-bold text-gray-500 block">Nível Controles</span>
              <span class="text-xs font-black text-blue-900 mt-1 block">
                {{ rotuloNivelControle }}
              </span>
              <span class="text-[10px] text-gray-500 block">
                Fator: {{ avaliacaoPrincipal?.fator_mitigacao ?? '1.0' }}
              </span>
            </div>

            <!-- Risco Residual -->
            <div class="p-3 bg-blue-50/70 rounded-xl border border-blue-200">
              <span class="text-[10px] uppercase font-bold text-blue-900 block">Risco Residual</span>
              <span class="text-lg font-black text-blue-950 mt-0.5 block">
                {{ avaliacaoPrincipal?.risco_residual ?? '-' }}
              </span>
              <span class="text-[10px] text-blue-700 block">Inerente × Fator</span>
            </div>

            <!-- Classificação Final -->
            <div class="p-3 bg-gray-50 rounded-xl border border-gray-200 flex flex-col justify-center items-center">
              <span class="text-[10px] uppercase font-bold text-gray-500 block mb-1">Classificação</span>
              <span 
                :class="getClassificacaoBadge(classificacaoCalculada)"
                class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border"
              >
                {{ classificacaoCalculada }}
              </span>
            </div>
          </div>

          <!-- Indicador de Apetite Institucional -->
          <div 
            class="p-3 rounded-xl border flex items-center justify-between text-xs"
            :class="isAcimaApetite ? 'bg-amber-50 border-amber-300 text-amber-900' : 'bg-emerald-50 border-emerald-300 text-emerald-900'"
          >
            <div class="flex items-center gap-2">
              <span class="text-base">{{ isAcimaApetite ? '⚠️' : '✅' }}</span>
              <span>
                <strong>Apetite / Tolerância Institucional:</strong> 
                {{ isAcimaApetite ? 'Risco Residual acima do limite (7,99). Exige Plano de Ação prioritário.' : 'Risco Residual dentro do limite institucional (até 7,99).' }}
              </span>
            </div>
            <span class="text-[11px] font-bold px-2 py-0.5 rounded bg-white/80 border">
              Limite: 7,99
            </span>
          </div>

          <!-- Controles Internos Existentes -->
          <div>
            <h4 class="text-xs font-bold text-gray-800 uppercase mb-2 flex items-center justify-between">
              <span>Controles Internos Existentes Cadastrados</span>
              <span class="text-gray-400 font-normal text-[11px]">
                ({{ controlesLista.length }} controle{{ controlesLista.length === 1 ? '' : 's' }})
              </span>
            </h4>

            <div v-if="controlesLista.length > 0" class="overflow-x-auto rounded-lg border border-gray-200">
              <table class="min-w-full divide-y divide-gray-200 text-left text-xs">
                <thead class="bg-gray-50 text-gray-600 font-semibold">
                  <tr>
                    <th class="py-2.5 px-3 w-12 text-center">#</th>
                    <th class="py-2.5 px-3">Descrição do Controle Interno</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 bg-white">
                  <tr v-for="(ctrl, cIdx) in controlesLista" :key="ctrl.id || cIdx">
                    <td class="py-2 px-3 text-center text-gray-400 font-mono text-[11px]">{{ cIdx + 1 }}</td>
                    <td class="py-2 px-3 text-gray-800">{{ ctrl.descricao_controle }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs text-gray-500 italic text-center">
              Nenhum controle interno cadastrado para este evento de risco (Fator de mitigação: 1.0 - Inexistente).
            </div>
          </div>
        </div>

        <!-- 5. Resposta ao Risco e Planos de Ação / Contingência -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-5">
          <div class="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 class="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
              <span class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">5</span>
              <span>Resposta ao Risco e Planos de Ação</span>
            </h3>
            <span class="text-[10px] text-gray-400 font-semibold">Etapa 5</span>
          </div>

          <!-- Tipo de Resposta Adotada -->
          <div class="flex items-center gap-3">
            <span class="text-xs font-bold text-gray-700">Tipo de Resposta Adotada:</span>
            <span class="px-3 py-1 bg-indigo-50 text-indigo-900 border border-indigo-200 font-bold text-xs rounded-full uppercase">
              {{ tipoRespostaPrincipal }}
            </span>
          </div>

          <!-- Tabela de Planos de Ação -->
          <div>
            <h4 class="text-xs font-bold text-gray-800 uppercase mb-2 flex items-center justify-between">
              <span>Planos de Ação (Ações Mitigadoras)</span>
              <span class="text-gray-400 font-normal text-[11px]">
                ({{ planosAcaoLista.length }} ação{{ planosAcaoLista.length === 1 ? '' : 'ões' }})
              </span>
            </h4>

            <div v-if="planosAcaoLista.length > 0" class="overflow-x-auto rounded-lg border border-gray-200">
              <table class="min-w-full divide-y divide-gray-200 text-left text-xs">
                <thead class="bg-gray-50 text-gray-600 font-semibold">
                  <tr>
                    <th class="py-2.5 px-3">O Que (Ação Proposta)</th>
                    <th class="py-2.5 px-3">Como (Método de Execução)</th>
                    <th class="py-2.5 px-3">Quem (Responsável)</th>
                    <th class="py-2.5 px-3 text-center">Início</th>
                    <th class="py-2.5 px-3 text-center">Término</th>
                    <th class="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 bg-white">
                  <tr v-for="(pa, pIdx) in planosAcaoLista" :key="pa.id || pIdx">
                    <td class="py-2.5 px-3 font-semibold text-gray-900 max-w-xs">{{ pa.o_que }}</td>
                    <td class="py-2.5 px-3 text-gray-700 max-w-xs">{{ pa.como || '-' }}</td>
                    <td class="py-2.5 px-3 text-gray-800 font-medium">{{ pa.quem || '-' }}</td>
                    <td class="py-2.5 px-3 text-center text-gray-600 whitespace-nowrap">{{ formatarData(pa.data_inicio) }}</td>
                    <td class="py-2.5 px-3 text-center text-gray-600 whitespace-nowrap">{{ formatarData(pa.data_termino) }}</td>
                    <td class="py-2.5 px-3 text-center">
                      <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gray-100 text-gray-700 border">
                        {{ pa.status || 'A Iniciar' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs text-gray-500 italic text-center">
              Nenhum plano de ação registrado nesta ficha.
            </div>
          </div>

          <!-- Planos de Contingência (se houver) -->
          <div v-if="planosContingenciaLista.length > 0">
            <h4 class="text-xs font-bold text-gray-800 uppercase mb-2 flex items-center justify-between">
              <span>Planos de Contingência (Gatilhos Operacionais)</span>
              <span class="text-gray-400 font-normal text-[11px]">
                ({{ planosContingenciaLista.length }} plano{{ planosContingenciaLista.length === 1 ? '' : 's' }})
              </span>
            </h4>

            <div class="overflow-x-auto rounded-lg border border-gray-200">
              <table class="min-w-full divide-y divide-gray-200 text-left text-xs">
                <thead class="bg-gray-50 text-gray-600 font-semibold">
                  <tr>
                    <th class="py-2.5 px-3">Gatilho (Evento Disparador)</th>
                    <th class="py-2.5 px-3">O Que Fazer (Ação Imediata)</th>
                    <th class="py-2.5 px-3">Como Executar</th>
                    <th class="py-2.5 px-3">Responsável</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 bg-white">
                  <tr v-for="(pc, cIdx) in planosContingenciaLista" :key="pc.id || cIdx">
                    <td class="py-2.5 px-3 font-semibold text-rose-900">{{ pc.gatilho }}</td>
                    <td class="py-2.5 px-3 text-gray-900">{{ pc.o_que }}</td>
                    <td class="py-2.5 px-3 text-gray-700">{{ pc.como || '-' }}</td>
                    <td class="py-2.5 px-3 text-gray-800 font-medium">{{ pc.responsavel || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 6. Governança, Autoria e Rastreabilidade -->
        <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
          <h3 class="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
            🏛️ Informações de Governança e Tramitação
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-gray-600">
            <div>
              <span class="font-bold text-gray-500 block text-[11px]">Elaborado por:</span>
              <span class="text-gray-900 font-medium">
                {{ ficha.criado_por?.nome || ficha.criado_por?.username || 'Não identificado' }}
              </span>
              <span v-if="ficha.criado_em" class="block text-[10px] text-gray-400 mt-0.5">
                em {{ formatarDataHora(ficha.criado_em) }}
              </span>
            </div>

            <div>
              <span class="font-bold text-gray-500 block text-[11px]">Submissão UGERC:</span>
              <span v-if="ficha.submetido_em" class="text-blue-800 font-semibold">
                {{ formatarDataHora(ficha.submetido_em) }}
              </span>
              <span v-else class="text-amber-700 font-medium italic">
                Em elaboração (Rascunho)
              </span>
            </div>

            <div>
              <span class="font-bold text-gray-500 block text-[11px]">Versão Atual do Mapeamento:</span>
              <span class="text-purple-900 font-bold">
                {{ ficha.tag_versao || 'v1.0 (Original)' }}
              </span>
            </div>
          </div>

          <div v-if="ficha.observacoes_ugerc" class="mt-4 pt-3 border-t border-gray-100 text-xs">
            <span class="font-bold text-gray-700 block text-[11px]">Observações / Parecer UGERC:</span>
            <p class="text-gray-800 italic bg-amber-50/60 p-2.5 rounded border border-amber-200 mt-1">
              {{ ficha.observacoes_ugerc }}
            </p>
          </div>
        </div>

        <!-- Rodapé de Ações -->
        <div class="flex flex-col sm:flex-row justify-between items-center gap-3 pt-2">
          <router-link
            to="/riscos/mapeados"
            class="text-xs font-semibold text-gray-600 hover:text-blue-700 transition"
          >
            ← Voltar para Fichas Cadastradas
          </router-link>

          <div class="flex items-center gap-2">
            <router-link
              v-if="ficha.pode_editar"
              :to="'/riscos/' + ficha.id + '/editar'"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-xs transition inline-flex items-center gap-1.5"
            >
              <span>✏️</span>
              <span>Editar Ficha</span>
            </router-link>

            <button
              @click="imprimirFicha"
              type="button"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition inline-flex items-center gap-1.5 cursor-pointer"
            >
              <span>🖨️</span>
              <span>Imprimir Ficha</span>
            </button>

            <button
              v-if="ficha.pode_excluir"
              @click="confirmarExclusao"
              :disabled="excluindo"
              type="button"
              class="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-xs transition inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <span>🗑️</span>
              <span>{{ excluindo ? 'Excluindo...' : 'Excluir Ficha' }}</span>
            </button>
          </div>
        </div>

      </template>
    </div>

    <!-- Componente de Impressão A4 Oculto na tela e Ativo no Print -->
    <FichaImpressaoA4 v-if="ficha" :ficha="ficha" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../../services/api';
import FichaImpressaoA4 from '../../components/riscos/FichaImpressaoA4.vue';

const route = useRoute();
const router = useRouter();

const fichaId = computed(() => Number(route.params.id));
const ficha = ref<any>(null);
const carregando = ref(true);
const erroCarregamento = ref<string | null>(null);
const excluindo = ref(false);

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

const eventoSelecionadoIndex = ref(0);

const eventoPrincipal = computed(() => {
  if (!ficha.value) return null;
  if (ficha.value.eventos && ficha.value.eventos.length > 0) {
    return ficha.value.eventos[eventoSelecionadoIndex.value] || ficha.value.eventos[0];
  }
  return ficha.value.evento || null;
});

const avaliacaoPrincipal = computed(() => {
  return eventoPrincipal.value?.avaliacao || null;
});

const controlesLista = computed(() => {
  return avaliacaoPrincipal.value?.controles || [];
});

const planosAcaoLista = computed(() => {
  return eventoPrincipal.value?.planos_acao || [];
});

const planosContingenciaLista = computed(() => {
  return eventoPrincipal.value?.planos_contingencia || [];
});

const tipoRespostaPrincipal = computed(() => {
  const pa = planosAcaoLista.value;
  if (pa && pa.length > 0 && pa[0].tipo_resposta) {
    return pa[0].tipo_resposta;
  }
  return 'MITIGAR';
});

const nomeUnidade = computed(() => {
  if (!ficha.value) return '-';
  const u = ficha.value.unidade;
  const nome = u?.nome || ficha.value.unidade_nome;
  const sigla = u?.sigla || ficha.value.unidade_sigla;
  if (!nome) return '-';
  return sigla ? `${nome} (${sigla})` : nome;
});

const nomeProcesso = computed(() => {
  if (!ficha.value) return '-';
  if (ficha.value.processo_outro) {
    return `[Outro] ${ficha.value.processo_outro}`;
  }
  return ficha.value.processo?.nome || ficha.value.processo_nome || '-';
});

const nomeMacroprocesso = computed(() => {
  if (!ficha.value) return 'Geral';
  const proc = ficha.value.processo;
  return proc?.macroprocesso?.nome || proc?.macroprocessoNome || ficha.value.macroprocesso_nome || 'Geral';
});

const riscoInerenteCalculado = computed(() => {
  const av = avaliacaoPrincipal.value;
  if (!av) return '-';
  if (av.risco_inerente !== undefined && av.risco_inerente !== null) return av.risco_inerente;
  if (av.probabilidade && av.impacto) return av.probabilidade * av.impacto;
  return '-';
});

const rotuloNivelControle = computed(() => {
  const av = avaliacaoPrincipal.value;
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
});

const classificacaoCalculada = computed(() => {
  const av = avaliacaoPrincipal.value;
  if (!av) return 'BAIXO';
  if (av.classificacao) return av.classificacao;
  const rr = Number(av.risco_residual);
  if (isNaN(rr)) return 'BAIXO';
  if (rr <= 2.0) return 'BAIXO';
  if (rr <= 7.99) return 'MÉDIO';
  if (rr <= 14.99) return 'ALTO';
  return 'EXTREMO';
});

const isAcimaApetite = computed(() => {
  const av = avaliacaoPrincipal.value;
  if (!av) return false;
  if (av.acima_apetite !== undefined && av.acima_apetite !== null) return Boolean(av.acima_apetite);
  const rr = Number(av.risco_residual);
  return !isNaN(rr) && rr > 7.99;
});

function getClassificacaoBadge(classif: string) {
  switch (classif) {
    case 'BAIXO': return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    case 'MEDIO':
    case 'MÉDIO': return 'bg-amber-50 text-amber-800 border-amber-200';
    case 'ALTO': return 'bg-orange-50 text-orange-800 border-orange-200';
    default: return 'bg-rose-50 text-rose-800 border-rose-200';
  }
}

function getIconeSeveridadeBg(classif: string) {
  switch (classif) {
    case 'BAIXO': return 'bg-emerald-100 text-emerald-800';
    case 'MEDIO':
    case 'MÉDIO': return 'bg-amber-100 text-amber-800';
    case 'ALTO': return 'bg-orange-100 text-orange-800';
    default: return 'bg-rose-100 text-rose-800';
  }
}

function getIconeSeveridade(classif: string) {
  switch (classif) {
    case 'BAIXO': return '🟢';
    case 'MEDIO':
    case 'MÉDIO': return '🟡';
    case 'ALTO': return '🟠';
    default: return '🔴';
  }
}

function getStatusBadge(st: string) {
  switch (st) {
    case 'RASCUNHO': return 'bg-amber-50 text-amber-800 border-amber-200';
    case 'SUBMETIDO': return 'bg-blue-50 text-blue-800 border-blue-200';
    case 'HOMOLOGADO': return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    default: return 'bg-purple-50 text-purple-800 border-purple-200';
  }
}

function formatarData(dataIso?: string | null): string {
  if (!dataIso) return '-';
  try {
    const d = new Date(dataIso);
    return isNaN(d.getTime()) ? dataIso : d.toLocaleDateString('pt-BR');
  } catch {
    return dataIso;
  }
}

function formatarDataHora(dataIso?: string | null): string {
  if (!dataIso) return '-';
  try {
    const d = new Date(dataIso);
    return isNaN(d.getTime()) ? dataIso : d.toLocaleString('pt-BR');
  } catch {
    return dataIso;
  }
}

async function carregarFicha() {
  carregando.value = true;
  erroCarregamento.value = null;
  try {
    const res = await api.get(`/api/riscos/${fichaId.value}`);
    ficha.value = res.data;
  } catch (err: any) {
    console.error('Erro ao carregar ficha de risco:', err);
    erroCarregamento.value = err.response?.data?.detail || 'Ficha de risco não encontrada ou sem permissão de acesso.';
  } finally {
    carregando.value = false;
  }
}

function imprimirFicha() {
  window.print();
}

async function confirmarExclusao() {
  if (!ficha.value?.pode_excluir) {
    alert('Você não possui permissão para excluir esta ficha de risco.');
    return;
  }

  const confirmou = confirm(
    `ATENÇÃO: Você está prestes a excluir permanentemente a Ficha de Risco #${ficha.value.id}.\n\nProcesso: ${nomeProcesso.value}\nUnidade: ${nomeUnidade.value}\n\nTodos os eventos de risco, avaliações da matriz, controles e planos associados serão removidos do sistema.\n\nDeseja realmente continuar? Esta ação NÃO pode ser desfeita.`
  );
  if (!confirmou) return;

  try {
    excluindo.value = true;
    const res = await api.delete(`/api/riscos/${ficha.value.id}`);
    alert(res.data.message || `Ficha #${ficha.value.id} excluída com sucesso.`);
    router.push('/riscos/mapeados');
  } catch (err: any) {
    console.error('Erro ao excluir ficha:', err);
    alert(err.response?.data?.detail || 'Erro ao excluir ficha de risco.');
  } finally {
    excluindo.value = false;
  }
}

onMounted(() => {
  carregarFicha();
});
</script>

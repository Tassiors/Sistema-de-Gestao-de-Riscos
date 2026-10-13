<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex justify-between items-center">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Gestão de Gestores & Matriz de Visibilidade</h2>
        <p class="text-xs text-gray-500 mt-1">Controle de acessos ao sistema e atribuição de visibilidade setorial para acompanhamento de riscos.</p>
      </div>
      <div>
        <button 
          @click="abrirModalNovoUsuario" 
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition"
        >
          + Cadastrar Gestor
        </button>
      </div>
    </div>

    <!-- Tabela de Usuários Cadastrados -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-sm font-bold text-gray-800">Usuários Cadastrados ({{ usuarios.length }})</h3>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 text-left text-xs">
          <thead class="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              <th class="py-3 px-4">Nome / Login AD</th>
              <th class="py-3 px-4">E-mail Institucional</th>
              <th class="py-3 px-4 text-center">Perfil</th>
              <th class="py-3 px-4">Setor Principal</th>
              <th class="py-3 px-4">Setores com Acesso Adicional</th>
              <th class="py-3 px-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="u in usuarios" :key="u.id" class="hover:bg-gray-50 transition">
              <td class="py-3.5 px-4 font-medium text-gray-900">
                <div class="font-bold text-sm">{{ u.nome_completo }}</div>
                <div class="text-[11px] text-gray-400 font-mono">{{ u.username }}</div>
              </td>
              <td class="py-3.5 px-4 text-gray-600">{{ u.email }}</td>
              <td class="py-3.5 px-4 text-center">
                <span 
                  :class="u.perfil === 'ADMINISTRADOR' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'"
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                >
                  {{ u.perfil }}
                </span>
              </td>
              <td class="py-3.5 px-4 text-gray-700 font-medium">
                {{ u.unidade_principal?.nome || '—' }}
              </td>
              <td class="py-3.5 px-4 text-gray-600">
                <div v-if="u.visibilidades_adicionais?.length > 0" class="flex flex-wrap gap-1 max-w-md">
                  <span 
                    v-for="v in u.visibilidades_adicionais" 
                    :key="v.unidade_id" 
                    class="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-[10px]"
                  >
                    {{ v.unidade_nome }}
                  </span>
                </div>
                <span v-else class="text-gray-400 italic">Nenhum</span>
              </td>
              <td class="py-3.5 px-4 text-right">
                <button 
                  @click="editarUsuario(u)" 
                  class="text-blue-600 hover:text-blue-800 font-semibold text-xs px-2.5 py-1 rounded hover:bg-blue-50 transition"
                >
                  Editar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal de Cadastro / Edição de Gestor -->
    <div v-if="modalUsuarioAberto" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-xl max-h-[90vh] flex flex-col">
        <div class="flex justify-between items-center border-b pb-3 shrink-0">
          <h3 class="text-base font-bold text-gray-900">
            {{ usuarioForm.id ? 'Editar Gestor' : 'Cadastrar Novo Gestor' }}
          </h3>
          <button @click="modalUsuarioAberto = false" class="text-gray-400 hover:text-gray-600 text-xl font-bold">✕</button>
        </div>

        <div class="overflow-y-auto space-y-4 flex-1 pr-1">
          <!-- Consulta ao AD -->
          <div class="flex gap-2 items-end">
            <div class="flex-1">
              <label class="block text-xs font-semibold text-gray-700 mb-1">Login do AD (ex: tassio.silva) *</label>
              <input v-model="usuarioForm.username" type="text" placeholder="login.sobrenome" class="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-blue-500" />
            </div>
            <button 
              type="button" 
              @click="consultarAD" 
              :disabled="consultandoAD"
              class="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-bold rounded-lg border transition shrink-0"
            >
              {{ consultandoAD ? 'Buscando...' : 'Consultar AD' }}
            </button>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Nome Completo *</label>
            <input v-model="usuarioForm.nome_completo" type="text" class="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-blue-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">E-mail Institucional *</label>
            <input v-model="usuarioForm.email" type="email" class="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-blue-500" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Perfil de Acesso *</label>
              <select v-model="usuarioForm.perfil" class="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-blue-500">
                <option value="GESTOR_UNIDADE">Gestor de Unidade</option>
                <option value="ADMINISTRADOR">Administrador Geral</option>
                <option value="CONSULTA_SETORIAL">Consulta Somente-Leitura</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Setor Principal</label>
              <select v-model="usuarioForm.unidade_principal_id" class="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-blue-500">
                <option :value="null">Selecione o Setor...</option>
                <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nome }}</option>
              </select>
            </div>
          </div>

          <!-- Matriz de Visibilidade no Cadastro do Gestor -->
          <div class="border-t pt-4 space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <label class="block text-xs font-bold text-gray-800">
                  Matriz de Visibilidade (Setores com Acesso Adicional)
                </label>
                <p class="text-[11px] text-gray-500">
                  O gestor poderá visualizar relatórios e riscos dos setores assinalados.
                </p>
              </div>
              <button 
                type="button" 
                @click="toggleSelecionarTudo" 
                class="text-xs font-semibold px-2.5 py-1 rounded border transition"
                :class="todosSelecionados ? 'bg-blue-50 text-blue-700 border-blue-300' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-300'"
              >
                {{ todosSelecionados ? 'Desmarcar Todos' : 'Selecionar Tudo' }}
              </button>
            </div>

            <!-- Busca de Setor -->
            <input 
              v-model="filtroBuscaUnidade" 
              type="text" 
              placeholder="Pesquisar setor..." 
              class="text-xs border border-gray-300 rounded-lg p-2 w-full focus:ring-blue-500"
            />

            <!-- Lista de Setores com Checkbox -->
            <div class="overflow-y-auto space-y-1 border border-gray-200 rounded-lg p-2.5 max-h-48 bg-gray-50/50">
              <label 
                v-for="u in unidadesFiltradas" 
                :key="u.id" 
                class="flex items-center space-x-2 text-xs p-1.5 hover:bg-white rounded cursor-pointer transition border border-transparent hover:border-gray-200"
              >
                <input 
                  type="checkbox" 
                  :value="u.id" 
                  v-model="usuarioForm.visibilidades_ids" 
                  class="rounded text-blue-600 focus:ring-blue-500"
                />
                <span class="text-gray-800 flex-1">{{ u.nome }}</span>
                <span class="text-[10px] text-gray-400 font-medium">({{ u.tipo }})</span>
              </label>
              <div v-if="unidadesFiltradas.length === 0" class="text-center text-xs text-gray-400 py-3">
                Nenhum setor encontrado para "{{ filtroBuscaUnidade }}".
              </div>
            </div>

            <div class="flex justify-between items-center text-[11px] text-gray-500 px-1">
              <span>{{ usuarioForm.visibilidades_ids.length }} de {{ unidades.length }} setores selecionados</span>
              <span v-if="usuarioForm.unidade_principal_id" class="text-blue-600 font-medium">
                Setor principal tem acesso nativo garantido
              </span>
            </div>
          </div>
        </div>

        <div class="flex justify-end space-x-2 pt-3 border-t shrink-0">
          <button @click="modalUsuarioAberto = false" class="px-4 py-2 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg">Cancelar</button>
          <button @click="salvarUsuario" class="px-5 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm">Salvar Gestor</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import api from '../../services/api';

const usuarios = ref<any[]>([]);
const unidades = ref<any[]>([]);

const modalUsuarioAberto = ref(false);
const consultandoAD = ref(false);
const filtroBuscaUnidade = ref('');

const usuarioForm = reactive({
  id: null as number | null,
  username: '',
  nome_completo: '',
  email: '',
  perfil: 'GESTOR_UNIDADE',
  unidade_principal_id: null as number | null,
  ativo: true,
  visibilidades_ids: [] as number[]
});

const unidadesFiltradas = computed(() => {
  if (!filtroBuscaUnidade.value.trim()) return unidades.value;
  const q = filtroBuscaUnidade.value.toLowerCase();
  return unidades.value.filter(u => u.nome.toLowerCase().includes(q));
});

const todosSelecionados = computed(() => {
  if (unidades.value.length === 0) return false;
  return usuarioForm.visibilidades_ids.length === unidades.value.length;
});

function toggleSelecionarTudo() {
  if (todosSelecionados.value) {
    usuarioForm.visibilidades_ids = [];
  } else {
    usuarioForm.visibilidades_ids = unidades.value.map(u => u.id);
  }
}

async function carregarUsuarios() {
  try {
    const res = await api.get('/api/admin/usuarios');
    usuarios.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar usuários:', err);
  }
}

async function carregarUnidades() {
  try {
    const res = await api.get('/api/unidades');
    unidades.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar unidades:', err);
  }
}

function abrirModalNovoUsuario() {
  usuarioForm.id = null;
  usuarioForm.username = '';
  usuarioForm.nome_completo = '';
  usuarioForm.email = '';
  usuarioForm.perfil = 'GESTOR_UNIDADE';
  usuarioForm.unidade_principal_id = null;
  usuarioForm.ativo = true;
  usuarioForm.visibilidades_ids = [];
  filtroBuscaUnidade.value = '';
  modalUsuarioAberto.value = true;
}

function editarUsuario(u: any) {
  usuarioForm.id = u.id;
  usuarioForm.username = u.username;
  usuarioForm.nome_completo = u.nome_completo;
  usuarioForm.email = u.email;
  usuarioForm.perfil = u.perfil;
  usuarioForm.unidade_principal_id = u.unidade_principal?.id || null;
  usuarioForm.ativo = u.ativo;
  usuarioForm.visibilidades_ids = (u.visibilidades_adicionais || []).map((v: any) => v.unidade_id);
  filtroBuscaUnidade.value = '';
  modalUsuarioAberto.value = true;
}

async function consultarAD() {
  if (!usuarioForm.username.trim()) {
    alert('Informe o login do usuário para consultar o AD.');
    return;
  }
  consultandoAD.value = true;
  try {
    const res = await api.get(`/api/admin/ad-user-search/${usuarioForm.username.trim()}`);
    if (res.data.exists) {
      usuarioForm.nome_completo = res.data.displayName;
      usuarioForm.email = res.data.email;
    } else {
      alert('Usuário não localizado no Active Directory.');
    }
  } catch (err) {
    alert('Erro ao consultar usuário no AD.');
  } finally {
    consultandoAD.value = false;
  }
}

async function salvarUsuario() {
  if (!usuarioForm.username || !usuarioForm.nome_completo || !usuarioForm.email) {
    alert('Preencha os campos obrigatórios.');
    return;
  }
  try {
    await api.post('/api/admin/usuarios', {
      id: usuarioForm.id,
      username: usuarioForm.username,
      nome_completo: usuarioForm.nome_completo,
      email: usuarioForm.email,
      perfil: usuarioForm.perfil,
      unidade_principal_id: usuarioForm.unidade_principal_id,
      ativo: usuarioForm.ativo,
      visibilidades_ids: usuarioForm.visibilidades_ids
    });
    alert('Gestor salvo com sucesso!');
    modalUsuarioAberto.value = false;
    await carregarUsuarios();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Erro ao salvar usuário.');
  }
}

onMounted(async () => {
  await Promise.all([carregarUsuarios(), carregarUnidades()]);
});
</script>

"""
Script Idempotente para Remoção de Projetos Estratégicos do Catálogo de Processos
==================================================================================
Identifica e remove da tabela 'processos' entradas que correspondam ao padrão
de projetos estratégicos (iniciados com código entre colchetes, ex: [P1.01] "Nome").
Exibe no console a lista exata do que foi excluído para validação.
"""

import os
import re
import sqlite3

def remover_projetos_estrategicos():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "app.db"))
    if not os.path.exists(db_path):
        print(f"[AVISO] Banco de dados não encontrado em: {db_path}")
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Busca todos os processos
    cursor.execute("SELECT id, nome, macroprocesso_id FROM processos")
    todos = cursor.fetchall()

    padrao_projeto = re.compile(r"^\s*\[[^\]]+\]")
    encontrados = []
    for pid, pnome, mid in todos:
        if padrao_projeto.search(pnome):
            encontrados.append((pid, pnome, mid))

    if not encontrados:
        print("[INFO] Nenhum projeto estratégico com padrão [código] foi encontrado no catálogo de processos.")
        conn.close()
        return []

    excluidos = []
    for pid, pnome, mid in encontrados:
        # Verifica se está sendo utilizado em algum mapeamento de risco existente
        cursor.execute("SELECT COUNT(*) FROM mapeamentos_risco WHERE processo_id = ?", (pid,))
        count_map = cursor.fetchone()[0]

        if count_map > 0:
            print(f"[ALERTA] Processo ID {pid} ('{pnome}') possui {count_map} mapeamento(s) de risco associado(s). Não será excluído fisicamente para manter a integridade referencial.")
            continue

        # Remove de processos_unidades
        cursor.execute("DELETE FROM processos_unidades WHERE processo_id = ?", (pid,))
        # Remove de processos
        cursor.execute("DELETE FROM processos WHERE id = ?", (pid,))
        excluidos.append({"id": pid, "nome": pnome})
        print(f"[REMOVIDO] Processo ID {pid}: '{pnome}'")

    conn.commit()
    conn.close()

    print(f"\n[SUCESSO] Total de projetos estratégicos excluídos: {len(excluidos)}")
    return excluidos

if __name__ == "__main__":
    remover_projetos_estrategicos()

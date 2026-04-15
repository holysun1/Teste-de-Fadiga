import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import sys

def obter_caminho_externo():
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como .exe, olha para a pasta do executável
        return os.path.dirname(sys.executable)
    # Se estiver rodando como .py, olha para a pasta do script
    return os.path.dirname(os.path.abspath(__file__))

def gerar_analise(usuario_especifico=None):
    pasta = obter_caminho_externo()
    arquivo = os.path.join(pasta, "log_foco_detalhado.csv")

    # 1. Verificação de existência do arquivo
    if not os.path.exists(arquivo):
        print("Arquivo de log não encontrado. Realize um teste primeiro.")
        return

    # 2. Carga dos dados (Tratamento de Encoding)
    try:
        df = pd.read_csv(arquivo, encoding='utf-8-sig') # 'utf-8-sig' é melhor para arquivos Excel
    except Exception:
        df = pd.read_csv(arquivo, encoding='latin-1')

# 3. Tratamento inicial (Data, Ordenação e LIMPEZA)
    df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
    
    # IMPORTANTE: Limpa espaços e padroniza para MAIÚSCULO para evitar erros de busca
    df['Operador'] = df['Operador'].astype(str).str.strip().str.upper()
    
    df = df.sort_values('Data_Hora').reset_index(drop=True)

    # 4. Lógica de Seleção de Usuário
    if not usuario_especifico:
        usuarios_disponiveis = sorted(df['Operador'].unique().tolist())
        lista_str = "\n".join([f"- {u}" for u in usuarios_disponiveis])

      

    # 5. Filtragem Robusta
    # 4. Lógica de Seleção de Usuário (Versão com Lista)
    if not usuario_especifico:
        usuarios_disponiveis = sorted(df['Operador'].unique().tolist())
        
        if not usuarios_disponiveis:
            print("Nenhum operador encontrado no banco.")
            return

        # Criando a Janela de Seleção
        root = tk.Tk()
        root.title("Selecionar Operador")
        root.geometry("300x400")
        
        # Label de instrução
        tk.Label(root, text="Escolha o Operador:", font=('Arial', 10, 'bold')).pack(pady=10)

        # Criando a lista (Listbox)
        lista = tk.Listbox(root, font=('Arial', 10), selectmode=tk.SINGLE)
        lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Inserindo os nomes na lista
        for user in usuarios_disponiveis:
            lista.insert(tk.END, user)

        escolha_final = {"nome": None}

        def confirmar():
            selecao = lista.curselection()
            if selecao:
                escolha_final["nome"] = lista.get(selecao[0])
                root.destroy()

        # Botões
        tk.Button(root, text="Ver Histórico", command=confirmar, bg='#2ecc71', fg='white').pack(pady=10)
        tk.Button(root, text="Ver Geral (Equipe)", command=root.destroy, bg='#3498db', fg='white').pack(pady=5)

        root.mainloop()
        usuario_especifico = escolha_final["nome"]

    # 5. Filtragem (Continua igual)
    if usuario_especifico:
        df_plot = df[df['Operador'] == usuario_especifico].copy()
        titulo = f"PERFORMANCE: {usuario_especifico}"
    else:
        df_plot = df.copy()
        titulo = "PERFORMANCE GERAL DA EQUIPE"

    # Reajustamos o ID_Sessao para que o gráfico do usuário comece do 1, 2, 3...
    df_plot = df_plot.reset_index(drop=True)
    df_plot['ID_Sessao'] = df_plot.index + 1
    
# 6. Criação da figura
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, 
                                    gridspec_kw={'height_ratios': [2, 1]})

    # --- GRÁFICO 1: LATÊNCIA ---
    ax1.plot(df_plot['ID_Sessao'], df_plot['Media_Visual'], marker='s', color='#2ecc71', 
            label='Foco Visual (ms)', linewidth=2)
    ax1.plot(df_plot['ID_Sessao'], df_plot['Media_Sonora'], marker='^', color='#3498db', 
            label='Foco Sonoro (ms)', linewidth=2)
    
    ax1.axhspan(500, 900, facecolor='#e74c3c', alpha=0.1, label='Zona de Fadiga Crítica')
    ax1.axhline(y=450, color='#e74c3c', linestyle=':', label='Limite de Atenção (450ms)')
    
    ax1.set_ylabel('Tempo de Resposta (ms)', fontweight='bold')
    ax1.set_title(titulo, fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, axis='y', linestyle='--', alpha=0.4)

    # --- GRÁFICO 2: ERROS ---
    largura = 0.6 
    ax2.bar(df_plot['ID_Sessao'], df_plot['Erros_Impulso'], width=largura, color='#e74c3c', label='Erros de Impulso')
    ax2.bar(df_plot['ID_Sessao'], df_plot['Erros_Omissao'], width=largura, bottom=df_plot['Erros_Impulso'], 
            color='#f1c40f', alpha=0.7, label='Erros de Omissão')
    
    ax2.set_ylabel('Qtd. de Erros', fontweight='bold')
    ax2.set_xlabel('Número da Tentativa / Sessão', fontweight='bold')
    ax2.legend(loc='upper left')
    ax2.grid(True, axis='y', linestyle='--', alpha=0.4)
    
    plt.xticks(df_plot['ID_Sessao'])

    # Datas no eixo X
    for i, row in df_plot.iterrows():
        data_str = row['Data_Hora'].strftime('%d/%m %H:%M')
        ax2.text(row['ID_Sessao'], -1.2, data_str, ha='right', fontsize=7, rotation=35)

    plt.tight_layout()
    
    nome_grafico = os.path.join(pasta, f"dashboard_{usuario_especifico or 'geral'}.png")
    plt.savefig(nome_grafico)
    plt.show()

if __name__ == "__main__":
    gerar_analise()
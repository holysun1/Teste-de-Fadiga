import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Localização do arquivo

def gerar_analise():
    pasta = os.path.dirname(os.path.abspath(__file__))
    arquivo = os.path.join(pasta, "log_foco_detalhado.csv")
    
    if not os.path.exists(arquivo):
        print("Dados não encontrados.")
        return

    if os.path.exists(arquivo):
        # 2. Carga e tratamento de dados
        try:
            df = pd.read_csv(arquivo, encoding='utf-8')
        except UnicodeDecodeError:
            # Se falhar o UTF-8, tenta o Latin-1 (padrão do Excel no Brasil)
            df = pd.read_csv(arquivo, encoding='latin-1')        
            df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
            df = df.sort_values('Data_Hora').reset_index(drop=True)
        
        # Criamos uma coluna amigável para o eixo X (Ex: "Sessão 1", "Sessão 2")
        df['ID_Sessao'] = df.index + 1 

        # 3. Criação da figura
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, 
                                    gridspec_kw={'height_ratios': [2, 1]})

        # --- GRÁFICO 1: LATÊNCIA (Topo) ---
        ax1.plot(df['ID_Sessao'], df['Media_Visual'], marker='s', color='#2ecc71', 
                label='Foco Visual (ms)', linewidth=2)
        ax1.plot(df['ID_Sessao'], df['Media_Sonora'], marker='^', color='#3498db', 
                label='Foco Sonoro (ms)', linewidth=2)
        
        ax1.axhline(y=450, color='#e74c3c', linestyle=':', label='Limite de Atenção (450ms)')
        ax1.set_ylabel('Tempo de Resposta (ms)', fontweight='bold')
        ax1.set_title('DASHBOARD DE EVOLUÇÃO POR TENTATIVA', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, axis='y', linestyle='--', alpha=0.4)

        # --- GRÁFICO 2: ERROS (Base) ---
        # Agora usamos o ID_Sessao no eixo X para as barras ficarem separadas
        largura = 0.6 
        
        # Empilhamos os erros (stacked bar) para ficar mais visual
        ax2.bar(df['ID_Sessao'], df['Erros_Impulso'], width=largura, color='#e74c3c', label='Erros de Impulso')
        ax2.bar(df['ID_Sessao'], df['Erros_Omissao'], width=largura, bottom=df['Erros_Impulso'], 
                color='#f1c40f', alpha=0.7, label='Erros de Omissão')
        
        ax2.set_ylabel('Qtd. de Erros', fontweight='bold')
        ax2.set_xlabel('Número da Tentativa / Sessão', fontweight='bold', labelpad = 30)
        ax2.legend(loc='upper left')
        ax2.grid(True, axis='y', linestyle='--', alpha=0.4)
        
        # Ajustamos os ticks do eixo X para mostrar o número da sessão
        plt.xticks(df['ID_Sessao'])

        # 4. Adicionando as datas como anotações ou legendas secundárias
        # Para você não perder a noção de quando foi o teste
        for i, row in df.iterrows():
            # Coloca a data/hora bem pequena acima das barras
            data_str = row['Data_Hora'].strftime('%H:%M')
            ax2.text(row['ID_Sessao'], -0.5, data_str, ha='center', fontsize=8, rotation=45)

        plt.tight_layout()
        
        nome_grafico = os.path.join(pasta, "dashboard_por_tentativa.png")
        plt.savefig(nome_grafico)
        print(f"Gráfico gerado com sucesso: {nome_grafico}")
        plt.subplots_adjust(bottom=0.15)
        plt.show()
if __name__ == "__main__":
    gerar_analise()
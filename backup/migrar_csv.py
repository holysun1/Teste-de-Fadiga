import os
import pandas as pd
import bcrypt

# Altere para a função que você já usa no seu projeto para achar o caminho correto
def obter_caminho_externo():
    return os.path.dirname(os.path.abspath(__file__))

def migrar_banco_de_dados():
    caminho_csv = os.path.join(obter_caminho_externo(), "operadores_backup.csv")
    
    print("Iniciando a migração do operadores.csv...")
    
    try:
        # 1. Carrega o CSV antigo (garantindo que o CPF venha como string)
        df = pd.read_csv(caminho_csv, dtype={'CPF': str})
        
        # 2. Verifica se a coluna 'senha_hash' já existe para não fazer duas vezes
        if 'senha_hash' in df.columns:
            print("O arquivo já possui a coluna 'senha_hash'. Migração cancelada.")
            return

        # 3. Cria a nova coluna preenchida temporariamente com uma string vazia
        df['senha_hash'] = ""
        
        # 4. Percorre linha por linha gerando o hash a partir dos 4 primeiros dígitos do CPF
        for idx, row in df.iterrows():
            cpf = str(row['CPF']).strip()
            
            # Pega os 4 primeiros dígitos do CPF do operador
            senha_padrao = cpf[:4]
            
            # Gera o hash robusto com bcrypt
            senha_hash = bcrypt.hashpw(senha_padrao.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Guarda o hash na linha correspondente
            df.at[idx, 'senha_hash'] = senha_hash
            print(f"Hash gerado para o operador: {row['Nome']}")

        # 5. Salva o arquivo atualizado por cima do antigo, mantendo o formato correto
        df.to_csv(caminho_csv, index=False, encoding='utf-8')
        print("\n✅ Migração concluída com sucesso! O arquivo operadores.csv foi atualizado.")

    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")

if __name__ == "__main__":
    migrar_banco_de_dados()
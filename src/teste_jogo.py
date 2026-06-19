import pygame
import random
import time
import sys
import os
import csv
import numpy as np
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox
import sys
import matplotlib.pyplot as plt

def obter_caminho_externo():
    if getattr(sys, 'frozen', False): 
        # Se estiver rodando como .exe, olha para a pasta do executável
        return os.path.dirname(sys.executable)
    # Se estiver rodando como .py, olha para a pasta do script
    return os.path.dirname(os.path.abspath(__file__))

def inicializar_banco_operadores():
    caminho_base = obter_caminho_externo()
    arquivo = os.path.join(obter_caminho_externo(), "operadores.csv")
    if not os.path.exists(arquivo):
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                #Nova estrutura com CPF
                f.write("Nome,CPF,Nivel\n")
                f.write("ADMIN,00000000000,1\n") 
            print(f"Banco de Operadores criado em {arquivo}")
        except Exception as e:
            print(f"Erro ao criar {e}")
        print(f"O arquivo já existe:{arquivo}")


def resource_path(relative_path):
    """ Encontra o caminho real do arquivo, seja no VS Code ou no EXE """
    try:
        # Caminho temporário criado pelo PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CARREGAMENTO SEGURO DOS SONS ---
try:
    som_go = pygame.mixer.Sound(resource_path("assets/audio/som_go.wav"))
    som_nogo = pygame.mixer.Sound(resource_path("assets/audio/som_nogo.wav"))
    audio_on = True
except Exception as e:
    print(f"Aviso: Não foi possível carregar os sons: {e}")
    audio_on = False

def gerar_grafico_fadiga_sono():
    pasta_db = obter_caminho_externo()
    caminho_arquivo = os.path.join(pasta_db, "log_foco_detalhado.csv")
    
    if not os.path.exists(caminho_arquivo):
        print("Arquivo de log não encontrado.")
        return

    try:
        # 1. Lê o banco avisando o Pandas sobre os acentos (tenta utf-8, se falhar tenta latin1)
        try:
            df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(caminho_arquivo, encoding='latin1')
        
        # 2. Verifica se a coluna exata que criamos existe
        if 'horas_sono' not in df.columns:
            print("AVISO: A coluna 'horas_sono' não foi encontrada no arquivo.")
            return
            
        # 3. FILTRO DE LIMPEZA: Remove as linhas antigas que estão sem o dado de sono
        df_limpo = df.dropna(subset=['horas_sono'])
        
        if df_limpo.empty:
            print("Não há dados de sono suficientes para gerar o gráfico.")
            return

        # 4. Separa os dados limpos para os eixos X e Y
        horas_sono = df_limpo['horas_sono']
        media_reacao = df_limpo['Media_Geral']
        
        # Cria a Janela
        plt.figure(figsize=(10, 6))
        
        # Desenha os pontos (Dispersão)
        plt.scatter(horas_sono, media_reacao, color='purple', s=80, alpha=0.7, edgecolors='black', label='Testes Realizados')
        
        # A Linha do Teto de Segurança da Fábrica (400ms)
        plt.axhline(y=400, color='red', linestyle='--', linewidth=2, label='Teto de Bloqueio (400ms)')
        
        # Personalização do Gráfico
        plt.title("Análise Preditiva: Reflexo Biológico x Privação de Sono", fontsize=14, fontweight='bold')
        plt.xlabel("Horas de Sono Relatadas", fontsize=12)
        plt.ylabel("Tempo Médio de Reação (ms)", fontsize=12)
        
        # Inverte o Eixo X (Dormir menos = Mais perigoso, fica perto do eixo Y)
        plt.gca().invert_xaxis()
        
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend()
        
        # Mostra o gráfico na tela
        plt.show()
        
    except Exception as e:
        print(f"Erro ao gerar o gráfico de sono: {e}")


inicializar_banco_operadores()


def validar_login():
    global estado, usuario_atual, nivel_acesso, mensagem_login, input_texto, input_senha, campo_focado, proximo_evento, destino_pos_login,estado
    global limite_atual, em_calibracao, horas_sono_atual
    global campo_ativo, texto_nome, texto_sugestao,texto_critica,estado 
    caminho_csv = os.path.join(obter_caminho_externo(), "operadores.csv")
    estado = 'LOGIN'

    try:
        df = pd.read_csv(caminho_csv, dtype={'CPF': str})
        # 1. Limpeza dos dados de entrada
        nome_busca = input_texto.strip().upper()
        
        # 2. Busca o usuário
        user_row = df[df['Nome'].str.upper() == nome_busca]        
        
        if not user_row.empty:
            cpf_completo = str(user_row.iloc[0]['CPF']).strip()
            
            # 1. Checagem de Quantidade (Menos de 4 dígitos)
            if len(input_senha) < 4:
                mensagem_login = "A SENHA DEVE CONTER 4 DÍGITOS!"
                
            # 2. Checagem de Validade (Se tem 4, mas está errada)
            elif input_senha != cpf_completo[:4]:
                mensagem_login = "SENHA INCORRETA!"
                input_senha = "" 
                
            # 3. Sucesso (Tem 4 e está correta)
            else:
                usuario_atual = nome_busca
                # Pegamos o nível garantindo que seja um número inteiro
                nivel_acesso = int(user_row.iloc[0]['Nivel']) 
                
                estado = 'CARREGANDO'
                proximo_evento = time.time() + 2.0 # Timer de 2 segundos
                
                # Limpamos os campos para segurança
                input_texto = ""; input_senha = ""; campo_focado = "NOME"
                
                # FEEDBACK NO CONSOLE (Para você debugar)
                print(f"Login: {usuario_atual} | Nivel: {nivel_acesso} | Destino: {destino_pos_login}")

                            
                # --- LÓGICA DE CALIBRAÇÃO (ALINHADA CORRETAMENTE) ---
                if nivel_acesso == 0:
                    arquivo_historico = os.path.join(obter_caminho_externo(), "log_foco_detalhado.csv")
                    
                    if os.path.exists(arquivo_historico):
                        try:
                            df_historico = pd.read_csv(arquivo_historico, encoding='utf-8')
                        except UnicodeDecodeError:
                            df_historico = pd.read_csv(arquivo_historico, encoding='latin1')
                            
                        historico_usuario = df_historico[df_historico['Operador'] == usuario_atual]
                        total_sessoes = len(historico_usuario) 
                        
                        if total_sessoes >= 14:
                            media_historica = historico_usuario['Media_Geral'].mean() 
                            em_calibracao = False # Já fez 14 testes, está calibrado
                            
                            # 1. Calcula o limite pessoal dele (Margem de 30%)
                            limite_calculado = media_historica * 1.30 
                            
                            # 2. O Teto de Segurança: O limite é o limite calculado, MAS NUNCA MAIOR que 400.
                            limite_atual = min(limite_calculado, 400) 
                            
                            print(f"\n[DEBUG LOGIN] OPERADOR CALIBRADO: {usuario_atual}")
                            print(f"[DEBUG LOGIN] Sessões concluídas: {total_sessoes}")
                            print(f"[DEBUG LOGIN] Média Histórica Pessoal: {media_historica:.2f}ms")
                            print(f"[DEBUG LOGIN] Limite de Segurança Atual: {limite_atual:.2f}ms\n")

                        else:
                            # Operador com menos de 14 sessões (Novato)
                            limite_atual = 400 
                            em_calibracao = True
                            
                            print(f"\n[DEBUG LOGIN] OPERADOR EM CALIBRAÇÃO: {usuario_atual}")
                            print(f"[DEBUG LOGIN] Sessões: {total_sessoes}/14")
                            print(f"[DEBUG LOGIN] Usando Limite Padrão: {limite_atual}ms\n")
                            
                    else:
                        # Se o arquivo CSV ainda nem existir na fábrica
                        limite_atual = 400
                        em_calibracao = True
                        
                        print(f"\n[DEBUG LOGIN] PRIMEIRO ACESSO DA FÁBRICA!")
                        print(f"[DEBUG LOGIN] Usando Limite Padrão: {limite_atual}ms\n")                            
        # O else de Operador Não Cadastrado agora está alinhado com o if not user_row.empty
        else:
            mensagem_login = "OPERADOR NÃO CADASTRADO!"
            
    except Exception as e:
        print(f"ERRO REAL NO TERMINAL: {e}")
        mensagem_login = "ERRO AO ACESSAR O BANCO DE DADOS"


# --- Inicialização ---
pygame.init()
pygame.mixer.init()

# --- VARIÁVEIS DE CADASTRO NATIVO ---
input_nome_cad = ""
input_cpf_cad = ""
campo_focado = "NOME" # Pode ser "NOME" ou "CPF"
mensagem_feedback = "" # Para mostrar "Sucesso" ou "Erro" na tela
cor_feedback = (200, 50, 50) # Vermelho por padrão
lista_setores = ["OPERAÇÃO", "MANUTENÇÃO", "LOGÍSTICA", "ADMINISTRAÇÃO"]
idx_setor = 0
lista_niveis = ["0 - OPERADOR", "1 - ADMINISTRADOR"]
idx_nivel = 0
usuario_atual = ""
nivel_acesso = 0
estado = 'LOGIN'
input_texto = ""
input_senha = ""
campo_focado = "NOME"
input_ativo = True
cursor_visivel = True
tema_escuro = False
ultimo_blink = time.time()
usuario_deslogando = ""
mensagem_login = ""
input_sono = ""
horas_sono_atual = 0.0
tempo_inicio_contagem = 0


CORES = {
    'PRETO': (15, 15, 15),
    'BRANCO': (240, 240, 240),
    'VERDE': (46, 204, 113),
    'VERMELHO': (231, 76, 60),
    'AMARELO': (241, 196, 15),
    'AZUL': (52, 152, 219),
    'CINZA_ESC': (30, 30, 30),
    'CINZA_CLARO': (70, 70, 70),
    'OK': (39, 174, 96),
    'SIDEBAR': (33, 37, 41),        # Grafite quase preto
    'PRIMARIA': (0, 123, 255),      # Azul corporativo (Bootstrap)
    'SUCESSO': (40, 167, 69),       # Verde sóbrio
    'PERIGO': (220, 53, 69),        # Vermelho erro
    'TEXTO_DARK': (148,163,184),     # Texto quase preto
    'TEXTO_LIGHT': (241, 245, 249), # Texto branco
    'CAIXA_INPUT': (255, 255, 255),  # Fundo das caixas branco puro
    'FUNDO': (15, 23, 42),      # Cinza escuro de desktop antigo
    'FACE': (192, 192, 192),       # Cinza clássico do botão
    'BRILHO': (255, 255, 255),     # Borda superior/esquerda
    'SOMBRA': (128, 128, 128),     # Borda inferior/direita (primeira camada)
    'SOMBRA_FORTE': (0, 0, 0),     # Borda inferior/direita (final)
    'TEXTO': (0, 0, 0),            # Preto puro
    'AZUL_TITULO': (0, 0, 128)     # Azul marinho de barras de título
}


# 1. Lê a resolução real do monitor do usuário
info_tela = pygame.display.Info()
LARGURA = info_tela.current_w
ALTURA = info_tela.current_h

# 2. Cria a tela usando as dimensões máximas e a flag de Tela Cheia
tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)

tela = pygame.display.set_mode((LARGURA, ALTURA))
try:
    icone_imagem = pygame.image.load(resource_path("assets/icon.png"))
    pygame.display.set_icon(icone_imagem)
except Exception as e:
    print(f"Aviso: Ícone não carregado: {e}")
pygame.display.set_icon(icone_imagem)
pygame.display.set_caption("Controle de Fadiga PCP - Eng. Diego Vieira")

arquivo_fonte = os.path.join("fonte", "Montserrat-Regular.ttf") 
try:
    # Tenta carregar a fonte moderna
    fonte_p = pygame.font.Font(arquivo_fonte, 20)  # Pequena
    fonte_m = pygame.font.Font(arquivo_fonte, 32)  # Média
    fonte_g = pygame.font.Font(arquivo_fonte, 50)  # Grande
    print("Tipografia moderna carregada com sucesso da subpasta!")
except FileNotFoundError:
    # Se a pasta ou o arquivo não existirem, usa a fonte padrão
    print(f"Aviso: Arquivo em '{arquivo_fonte}' não encontrado. Usando fonte padrão.")
    fonte_p = pygame.font.SysFont("arial", 20, bold=True)
    fonte_m = pygame.font.SysFont("arial", 32, bold=True)
    fonte_g = pygame.font.SysFont("arial", 50, bold=True)
    
    # --- Variáveis de Calibração ---
checks = {"som_go": False, "som_nogo": False, "cores": False}

# --- Lógica de Diagnóstico ---
def obter_diagnostico(media_ms):
    if media_ms == 0: return "SEM DADOS", cor_texto_padrao
    if media_ms < 350: return "CONCENTRADO (ELITE)", CORES['VERDE']
    elif 350 <= media_ms < 450: return "ALERTA (NORMAL)", cor_texto_padrao
    elif 450 <= media_ms < 550: return "ATENCAO REDUZIDA", CORES['AMARELO']
    else: return "FADIGA CRITICA", CORES['VERMELHO']

# --- Funções de Dados ---
def salvar_resultados(dados, erros_i, erros_o, usuario,horas_sono):
    print(f"Dados recebidos para salvar: {len(dados)} tentativas")
    if not dados or not usuario : 
        print("DEBUG: Falha - Dados ou Usuário vazios.")
        return

    # Define o caminho para o arquivo ÚNICO na pasta do script (igual ao dash)
    pasta = obter_caminho_externo() 
    arquivo = os.path.join(pasta, "log_foco_detalhado.csv")
    existe = os.path.exists(arquivo)

    tempos_v = [d[1] for d in dados if d[0] == 'VISUAL']
    tempos_s = [d[1] for d in dados if d[0] == 'SONORO']
    todas = [d[1] for d in dados]
    
    media_v = sum(tempos_v) / len(tempos_v) if tempos_v else 0
    media_s = sum(tempos_s) / len(tempos_s) if tempos_s else 0
    media_g = sum(todas) / len(todas) if todas else 0
    status, _ = obter_diagnostico(media_g)
    
    try:
        # 'utf-8-sig' ajuda o Excel a entender os acentos e cedilhas
        with open(arquivo, 'a', newline='', encoding='utf-8-sig') as f:
            escritor = csv.writer(f)
            if not existe:
                escritor.writerow(['Operador','Data_Hora', 'Media_Visual', 'Media_Sonora', 'Media_Geral', 'Status', 'Erros_Impulso', 'Erros_Omissao','Observacoes','horas_sono'])
            
            escritor.writerow([
                usuario.upper(), #Nome do Operador
                datetime.now().strftime("%Y-%m-%d %H:%M"), 
                round(media_v, 2), 
                round(media_s, 2), 
                round(media_g, 2), 
                status, 
                erros_i, 
                erros_o,
                "", #Observação vazia
                horas_sono
            ])
            f.flush() # Força a gravação imediata no disco
        print(f"DEBUG: Dados salvos com sucesso em {arquivo}")
    except PermissionError:
        print("ERRO: O arquivo CSV está aberto em outro programa (Excel?). Feche-o e tente novamente.")
    except Exception as e:
        print(f"ERRO inesperado ao salvar: {e}")
# --- Geração de Sons ---
def gerar_beep(frequencia, duracao_ms=150):
    sample_rate = 44100
    n_samples = int(sample_rate * (duracao_ms / 1000.0))
    t = np.linspace(0, duracao_ms/1000.0, n_samples, False)
    waveform = np.sin(2 * np.pi * frequencia * t) * 0.3
    sound_array = (waveform * 32767).astype(np.int16)
    stereo_array = np.stack((sound_array, sound_array), axis=-1)
    return pygame.sndarray.make_sound(stereo_array)

som_go = pygame.mixer.Sound(resource_path("assets/audio/som_go.wav"))
som_nogo = pygame.mixer.Sound(resource_path("assets/audio/som_nogo.wav"))

# --- Variáveis Globais ---
TENTATIVAS_TOTAIS = 10
tentativa_atual = 0
dados_coletados = []
erros_impulso = 0
erros_omissao = 0
estado = 'LOGIN'
proximo_evento = 0
momento_estimulo = 0
tipo_atual = ''
subtipo_atual = ''
estado = 'HOME'           # O jogo agora começa na tela inicial do seu desenho
destino_pos_login = ''    # Vai guardar se ele clicou em TESTE ou PAINEL ADM
estado_anterior = "" # Guarda se estávamos em GO, NOGO ou ESPERA
# --- PARÂMETROS DE SEGURANÇA ---
LIMITE_PADRAO_FABRICA = 0.400  # Tempo em segundos (400ms)

def mostrar_texto(txt, cor, x, y, tamanho='m'):
    # 1. Cria um "dicionário" ligando a letrinha à fonte carregada de verdade
    dicionario_fontes = {
        'p': fonte_p, 
        'm': fonte_m, 
        'g': fonte_g
    }
    
    # 2. Pega a fonte correta com base no tamanho pedido
    fonte_escolhida = dicionario_fontes[tamanho]
    
    # 3. Agora sim, renderiza o texto (cria a imagem da palavra)
    superficie = fonte_escolhida.render(txt, True, cor)
    
    # 4. Posiciona no centro e desenha na tela
    retangulo = superficie.get_rect(center=(x, y))
    tela.blit(superficie, retangulo)


def desenhar_botao(rect, cor_base, cor_hover, texto, cor_texto, tam='m'):
    mouse_pos = pygame.mouse.get_pos()
    # Verifica se o mouse está em cima para mudar a cor de fundo
    cor_atual = cor_hover if rect.collidepoint(mouse_pos) else cor_base
    
    # 1. Desenha o corpo do botão (quadrado perfeito, sem border_radius)
    pygame.draw.rect(tela, cor_atual, rect)

    # 2. EFEITO 3D RETRO (O segredo do Windows 98)
    # Linhas de BRILHO (Superior e Esquerda) - Branco puro
    pygame.draw.line(tela, (255, 255, 255), (rect.x, rect.y), (rect.x + rect.w, rect.y), 2)
    pygame.draw.line(tela, (255, 255, 255), (rect.x, rect.y), (rect.x, rect.y + rect.h), 2)

    # Linhas de SOMBRA (Inferior e Direita) - Preto ou Cinza Escuro
    # Desenhamos um pixel para dentro para o contorno ficar perfeito
    pygame.draw.line(tela, (0, 0, 0), (rect.x + rect.w - 1, rect.y), (rect.x + rect.w - 1, rect.y + rect.h), 2)
    pygame.draw.line(tela, (0, 0, 0), (rect.x, rect.y + rect.h - 1), (rect.x + rect.w, rect.y + rect.h - 1), 2)

    # 3. TEXTO (Centralizado)
    mostrar_texto(texto, cor_texto, rect.centerx, rect.centery, tam)
def desenhar_barra_progresso():
    progresso = (tentativa_atual / TENTATIVAS_TOTAIS) * LARGURA
    pygame.draw.rect(tela, cor_caixas, (0, 0, LARGURA, 10))
    pygame.draw.rect(tela, CORES['AZUL'], (0, 0, progresso, 10))

def salvar_feedback(nome, sugestao, critica):
        pasta_db = obter_caminho_externo()
        filename = os.path.join(pasta_db, "sugestoes_criticas.csv")
        
        if not os.path.exists(filename):
            print("Arquivo de log não encontrado.")
            return

        try:
            # 1. Lê o banco avisando o Pandas sobre os acentos (tenta utf-8, se falhar tenta latin1)
            try:
                df = pd.read_csv(filename, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(filename, encoding='latin1')
            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Se o campo nome for deixado em branco ou vazio, força o padrão "Anonimo"
            nome_final = nome.strip() if nome.strip() != "" else "Anonimo"
            
            # Verifica se precisa criar o cabeçalho (caso o arquivo não exista)
            arquivo_novo = not os.path.exists(filename)
            
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if arquivo_novo:
                    # Cabeçalho do arquivo CSV
                    writer.writerow(["Data/Hora", "Nome", "Sugestao", "Critica/Reclamacao"])
                    
                # Escreve a nova linha com o feedback recebido
                writer.writerow([data_atual, nome_final, sugestao.strip(), critica.strip()])
        except Exception as e:
          print(f"Erro ao gerar o arquivo de sugestoes {e}")

# --- CONFIGURAÇÕES DE CORES E FONTES DO ESTADO 'PESQUISA' ---
COR_BG_PESQUISA = (15, 23, 42)      # Slate-900
COR_CARD_PESQUISA = (30, 41, 59)    # Slate-800
COR_TEXTO_P = (241, 245, 249)       # Slate-100
COR_MUTED_P = (148, 163, 184)       # Slate-400
COR_EMERALD_P = (52, 211, 153)      # Emerald-400
COR_BOTAO_P = (16, 185, 129)        # Emerald-500

fonte_p = pygame.font.SysFont("Arial", 18)
fonte_sub_p = pygame.font.SysFont("Arial", 16, italic=True)
fonte_btn_p = pygame.font.SysFont("Arial", 18, bold=True)

# --- VARIÁVEIS DE CONTROLE DO FORMULÁRIO ---
texto_nome = "Anonimo"
texto_sugestao = ""
texto_critica = ""
campo_ativo = None  # Pode ser: "nome", "sugestao", "critica" ou None

# --- DIMENSÕES DOS INPUTS (Ajuste o X e Y conforme a sua janela) ---
rect_nome_p = pygame.Rect(100, 180, 400, 40)
rect_sugestao_p = pygame.Rect(100, 270, 600, 60)
rect_critica_p = pygame.Rect(100, 380, 600, 60)
rect_enviar_p = pygame.Rect(100, 470, 150, 45)

clock = pygame.time.Clock()
pygame.key.set_repeat(300,50)
foi_salvo = False
etapa_login ="NOME"
input_senha = ""

btn_fechar_rect = pygame.Rect(25,ALTURA-70,150,45)

# --- Loop Principal ---
while True:
    
    
    # 1. DEFINA OS BOTÕES DA HOME AQUI (Para o clique sempre encontrá-los)
    larg_b = 300
    btn_teste_h = pygame.Rect(LARGURA/2 - larg_b/2, 250, larg_b, 50)
    btn_admin_h = pygame.Rect(LARGURA/2 - larg_b/2, 310, larg_b, 50)
    btn_config_h = pygame.Rect(LARGURA/2 - larg_b/2, 370, larg_b, 50)
    

    # --- GEOMETRIA DA TELA FIM ---
    btn_finalizar_rect = pygame.Rect(LARGURA/2 - 150, 450, 300, 50)
    
    # Ícones dos cantos
    rect_pesquisa = pygame.Rect(LARGURA - 120, 40, 80, 80)
    rect_reclamacao = pygame.Rect(LARGURA - 120, ALTURA - 120, 80, 80)

    # Geometria das Caixas
    largura_padrao = 400
    altura_padrao = 45
    pos_x_centro = LARGURA/2 - (largura_padrao / 2)
    
    # Todas as caixas usam o exato mesmo 'pos_x_centro' e 'largura_padrao'
    rect_nome  = pygame.Rect(pos_x_centro, 150, largura_padrao, altura_padrao)
    rect_cpf   = pygame.Rect(pos_x_centro, 230, largura_padrao, altura_padrao)
    rect_setor = pygame.Rect(pos_x_centro, 310, largura_padrao, altura_padrao)
    rect_nivel = pygame.Rect(pos_x_centro, 390, largura_padrao, altura_padrao)

    # O Botão de Salvar agora tem a mesma largura do formulário (bloco sólido)
    btn_salvar_cad = pygame.Rect(pos_x_centro, 470, largura_padrao, 50) 
    
    # O Botão voltar continua no canto inferior isolado
    btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)

    # Botão "X" de saída no canto superior direito (durante o teste)
    btn_x_fec_rect = pygame.Rect(LARGURA - 50, 10, 40, 40)
    
    # Janela Modal de Pausa (Centralizada)
    larg_m, alt_m = 400, 300
    modal_rect = pygame.Rect(LARGURA/2 - larg_m/2, ALTURA/2 - alt_m/2, larg_m, alt_m)
    
    # Botões da Modal
    btn_continuar = pygame.Rect(modal_rect.x + 50, modal_rect.y + 80, 300, 45)
    btn_reiniciar = pygame.Rect(modal_rect.x + 50, modal_rect.y + 140, 300, 45)
    btn_fechar_teste = pygame.Rect(modal_rect.x + 50, modal_rect.y + 200, 300, 45)


    margem_x = LARGURA / 2

        # 1. Coordenadas dos botões (Operador)
    btn_go_rect = pygame.Rect(margem_x - 240, 220, 230, 45)
    btn_nogo_rect = pygame.Rect(margem_x + 10, 220, 230, 45)
    btn_cores_rect = pygame.Rect(margem_x - 115, 290, 230, 45) 
    btn_start_rect = pygame.Rect(margem_x - 150, 460, 300, 70)
    btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)

    # --- GEOMETRIA DA TELA DE CHECKS ---
    larg_ck = 350
    btn_ck_go = pygame.Rect(LARGURA/2 - larg_ck/2, 150, larg_ck, 50)
    btn_ck_nogo = pygame.Rect(LARGURA/2 - larg_ck/2, 230, larg_ck, 50)
    btn_ck_cor = pygame.Rect(LARGURA/2 - larg_ck/2, 310, larg_ck, 50)
    
    # O botão avançar (Fica escondido até tudo estar testado)
    btn_ck_avancar = pygame.Rect(LARGURA/2 - 150, 420, 300, 50)

# ==========================================
    # GERENCIADOR DE TEMA (CLARO/ESCURO)
    # ==========================================
    if tema_escuro:
        cor_fundo = CORES['PRETO']  # O seu fundo padrão
        cor_texto_padrao = CORES['BRANCO'] # As letras ficam brancas
        cor_caixas = CORES['CINZA_ESC'] # O fundo das caixinhas de dados
    else:
        cor_fundo = (240, 245, 250) # Um branco "gelo" muito elegante para app industrial
        cor_texto_padrao = (20, 20, 20) # As letras ficam quase pretas
        cor_caixas = (200, 210, 220) # Caixinhas ficam num cinza clarinho

    # Pinta a tela com a cor escolhida pelo interruptor
    tela.fill(cor_fundo) 
    agora = time.time()
    mouse_sobre_btn = False
    mouse_pos = pygame.mouse.get_pos()
    clique = False

    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ==========================================
            # 1. LÓGICA DE CLIQUES DO MOUSE
            # ==========================================
            if event.type == pygame.MOUSEBUTTONUP:
                clique = True 
                
                if btn_fechar_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

                # --- ACIONAR PAUSA (Se estiver em qualquer fase do teste) ---
                elif estado in ['ESPERA', 'ESTIMULO', 'FEEDBACK']:
                    if btn_x_fec_rect.collidepoint(mouse_pos):
                        estado_anterior = estado # Salva onde parou
                        estado = 'PAUSA'

                # --- LÓGICA DENTRO DA PAUSA ---
                elif estado == 'PAUSA':
                    if btn_continuar.collidepoint(mouse_pos):
                        # Em vez de voltar direto, inicia a contagem
                        estado = 'CONTAGEM'
                        tempo_inicio_contagem = time.time()
                    
                    elif btn_reiniciar.collidepoint(mouse_pos):
                        # Reseta tudo e começa do zero
                        dados_coletados.clear()
                        erros_impulso = 0; erros_omissao = 0; tentativa_atual = 0
                        estado = 'CONTAGEM'
                        tempo_inicio_contagem = time.time()
                    
                    elif btn_fechar_teste.collidepoint(mouse_pos):
                        # Cancela o teste e volta pro Menu sem salvar nada
                        dados_coletados.clear()
                        checks['som_go'] = False
                        checks['som_nogo'] = False
                        checks['cores'] = False
                        estado = 'HOME'
                        

                elif estado == 'CHECKS':
                    if btn_ck_go.collidepoint(mouse_pos):
                        som_go.play(); checks['som_go'] = True
                    elif btn_ck_nogo.collidepoint(mouse_pos):
                        som_nogo.play(); checks['som_nogo'] = True
                    elif btn_ck_cor.collidepoint(mouse_pos):
                        checks['cores'] = True
                    
                    # Se os 3 forem True, o clique no Avançar funciona
                    elif all(checks.values()) and btn_ck_avancar.collidepoint(mouse_pos):
                        estado = 'PERGUNTA_SONO'
                        input_sono = ""

                elif estado == 'HOME':
                    if btn_teste_h.collidepoint(mouse_pos):
                        destino_pos_login = 'TESTE' # Ele quer fazer o teste
                        estado = 'LOGIN'           # Mas mandamos para o login primeiro
                    
                    elif btn_admin_h.collidepoint(mouse_pos):
                        destino_pos_login = 'MENU' # Ele quer ir pro painel
                        estado = 'LOGIN'
                        
                    elif rect_pesquisa.collidepoint(mouse_pos):
                        estado = 'PESQUISA' # Esse vai direto (Anônimo!)
                        campo_ativo = None
                    elif rect_reclamacao.collidepoint(mouse_pos):
                        estado = 'RECLAMACAO' # Esse vai direto (Anônimo!)
                    
                    elif btn_config_h.collidepoint(mouse_pos):
                        estado = 'CONFIGURACOES'

                elif estado == 'PESQUISA':
                        # Gerenciar focos de clique
                        if rect_nome_p.collidepoint(mouse_pos):
                            campo_ativo = "nome"
                            if texto_nome == "Anonimo": texto_nome = "" # Limpa para o usuário digitar
                        elif rect_sugestao_p.collidepoint(mouse_pos):
                            campo_ativo = "sugestao"
                        elif rect_critica_p.collidepoint(mouse_pos):
                            campo_ativo = "critica"
                        elif rect_enviar_p.collidepoint(mouse_pos):
                            # Ação do Botão Enviar
                            salvar_feedback(texto_nome, texto_sugestao, texto_critica)
                            # Reseta o formulário e volta para a tela inicial do jogo
                            texto_nome = "Anonimo"
                            texto_sugestao = ""
                            texto_critica = ""
                            campo_ativo = None
                            estado = 'HOME' # Ou o nome exato do seu estado da tela inicial
                        else:
                            campo_ativo = None
                            if texto_nome.strip() == "": texto_nome = "Anonimo"
                     
                # --- CLIQUES NA TELA DE MENU (ADMIN/OPERADOR) ---
                elif estado == 'MENU':
                     # Só verifica o botão de sair se estiver no MENU
                    # Botão Sair Comum a todos
                    if btn_voltar_rect.collidepoint(mouse_pos):
                        #Limpeza de segurança
                        usuario_atual = ""
                        input_texto = "" # Limpa o CPF digitado
                        input_senha = "" # Limpa a senha
                        nivel_acesso = -1 # Reseta o nível
                        for chave in checks: checks[chave] = False
                        estado = 'LOGIN'
                    
                    
                    # Quando o login der sucesso e for nível 0
                    elif nivel_acesso == 0:
                        estado = 'CHECKS' # Esqueça o 'MENU', jogue ele direto pro check!
                        for chave in checks: checks[chave] = False # Garante que os checks estão zerados
                    
                        # Cliques Exclusivos do ADMIN (Nível 1)
                    elif nivel_acesso == 1:
                        if btn_hist_rect.collidepoint(mouse_pos) and existe_db:
                            import dashboard
                            dashboard.gerar_analise()
                        elif btn_cad_rect.collidepoint(mouse_pos):
                            estado = 'CADASTRO' 
                            input_nome_cad = ""; input_cpf_cad = ""; mensagem_feedback = ""                
                        elif btn_config_rect.collidepoint(mouse_pos):
                            estado = 'CONFIGURACOES'  
                        elif btn_grafico_rect.collidepoint(mouse_pos) and existe_db:
                                gerar_grafico_fadiga_sono()
                        

                            # --- CLIQUES NA TELA DE CADASTRO ---
                elif estado == 'CADASTRO':
                    # Ação de Voltar (Aqui ele não vai mais conflitar com o Sair)
                    if btn_voltar_rect.collidepoint(mouse_pos):
                        estado = 'MENU'
                        input_nome_cad = ""; input_cpf_cad = ""; mensagem_feedback = ""
                    elif rect_nome.collidepoint(mouse_pos): 
                        campo_focado = "NOME"
                    elif rect_cpf.collidepoint(mouse_pos): 
                        campo_focado = "CPF"

                    # --- NOVOS CLIQUES: MENUS CÍCLICOS ---
                    elif rect_setor.collidepoint(mouse_pos): 
                        # Pula para o próximo setor da lista. Se chegar no fim, volta pro começo (0)
                        idx_setor = (idx_setor + 1) % len(lista_setores)
                        campo_focado = "" # Tira o cursor piscando do Nome/CPF
                        
                    elif rect_nivel.collidepoint(mouse_pos): 
                        # Pula entre 0 - Operador e 1 - Admin
                        idx_nivel = (idx_nivel + 1) % len(lista_niveis)
                        campo_focado = "" # Tira o cursor piscando do Nome/CPF
                        
                    # Ação de Salvar
                    elif btn_salvar_cad.collidepoint(mouse_pos):
                        if len(input_cpf_cad) == 11 and len(input_nome_cad) > 3:
                            try:
                                caminho_csv = os.path.join(obter_caminho_externo(), "..\operadores.csv")
                                df = pd.read_csv(caminho_csv, dtype={'CPF': str})
                                if input_cpf_cad in df['CPF'].values:
                                    mensagem_feedback = "ERRO: CPF JÁ CADASTRADO!"; cor_feedback = (200, 50, 50)
                                else:
                                    with open(caminho_csv, 'a', encoding='utf-8') as f:
                                        f.write(f"{input_nome_cad},{input_cpf_cad},0\n")
                                    mensagem_feedback = "CADASTRADO COM SUCESSO!"; cor_feedback = (50, 180, 50)
                                    input_nome_cad = ""; input_cpf_cad = ""
                            except Exception as e:
                                mensagem_feedback = "ERRO AO ACESSAR DB"; cor_feedback = (200, 50, 50)
                        else:
                            mensagem_feedback = "DADOS INVÁLIDOS!"; cor_feedback = (200, 50, 50)

                elif estado == 'LOGIN':
                    # 1. Clique no Botão ENTRAR
                    if btn_entrar_rect.collidepoint(mouse_pos):
                        validar_login()
                    if btn_voltar_rect.collidepoint(mouse_pos):
                        estado = 'HOME'
                        input_texto = ""; input_senha = ""; mensagem_login = ""

                    if rect_nome.collidepoint(mouse_pos): campo_focado = "NOME"

                    if rect_senha.collidepoint(mouse_pos): campo_focado = "SENHA"

            
                elif estado == 'FIM':
                    if btn_finalizar_rect.collidepoint(mouse_pos):
                        # 1. LIMPEZA DE DADOS
                        for chave in checks: checks[chave] = False
                        dados_coletados.clear()
                        erros_impulso = 0
                        erros_omissao = 0
                        input_sono = 0
                        foi_salvo = False 
                        
                        # 2. LOGOUT DO OPERADOR (Segurança Industrial)
                        usuario_atual = ""
                        input_texto = ""
                        input_senha = ""
                        nivel_acesso = -1
                        
                        # 3. VOLTA PARA A HOME (Lobby)
                        estado = 'HOME'

        
            # ==========================================
            # 2. LÓGICA DO TECLADO (KEYDOWN)
            # ==========================================
            if event.type == pygame.KEYDOWN:
                
                if estado == 'PESQUISA' and campo_ativo:
                    if event.key == pygame.K_BACKSPACE:
                        if campo_ativo == "nome": texto_nome = texto_nome[:-1]
                        elif campo_ativo == "sugestao": texto_sugestao = texto_sugestao[:-1]
                        elif campo_ativo == "critica": texto_critica = texto_critica[:-1]
                        
                    elif event.key == pygame.K_TAB:
                        if campo_ativo == "nome": campo_ativo = "sugestao"
                        elif campo_ativo == "sugestao": campo_ativo = "critica"
                        elif campo_ativo == "critica": campo_ativo = "nome"
                        
                    elif event.key == pygame.K_ESCAPE:
                        estado = 'HOME' # Cancela e volta
                        
                    else:
                        if event.unicode.isprintable():
                            if campo_ativo == "nome": texto_nome += event.unicode
                            elif campo_ativo == "sugestao": texto_sugestao += event.unicode
                            elif campo_ativo == "critica": texto_critica += event.unicode

                # --- TELA DE SONO ---
                elif estado == 'PERGUNTA_SONO':
                    if event.key == pygame.K_RETURN:
                        if input_sono != "":
                            try:
                                horas_sono_atual = float(input_sono)
                                tentativa_atual = 0; dados_coletados = []; erros_impulso = 0; erros_omissao = 0
                                lista_estimulos = (['GO']*14 + ['NOGO']*6)
                                random.shuffle(lista_estimulos)
                                estado = 'ESPERA'
                                proximo_evento = time.time() + 1.2
                            except ValueError:
                                input_sono = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_sono = input_sono[:-1]
                    else:
                        if event.unicode in '0123456789.' and len(input_sono) < 4:
                            input_sono += event.unicode

                # --- TELA DE LOGIN ---
                elif estado == 'LOGIN':
                    mensagem_login = ""
                    if event.key == pygame.K_RETURN:
                        if campo_focado == "NOME":
                            if input_texto.upper() == "ADMIN":
                                usuario_atual = "ADMIN"; nivel_acesso = 1; estado = 'MENU'; input_texto = ""
                            else:
                                campo_focado = "SENHA"
                        else:
                            validar_login()
                    elif event.key == pygame.K_BACKSPACE:
                        if campo_focado == "NOME": input_texto = input_texto[:-1]
                        else: input_senha = input_senha[:-1]
                    elif event.key == pygame.K_TAB:
                        campo_focado = "SENHA" if campo_focado == "NOME" else "NOME"
                    else:
                        if event.unicode.isprintable():
                            if campo_focado == "NOME": input_texto += event.unicode
                            elif campo_focado == "SENHA" and len(input_senha) < 4:
                                if event.unicode.isdigit(): input_senha += event.unicode


    if estado == 'HOME':
        tela.fill(CORES['FUNDO']) # Use aquele cinza empresarial que sugerimos
        
        # 1. RELÓGIO (Canto Superior Esquerdo)
        import datetime
        hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
        mostrar_texto(hora_atual, CORES['TEXTO_DARK'], 100, 50, 'm')
        
        # 2. LOGO EMPRESA (Centro Superior)
        # Por enquanto um retângulo, depois você carrega uma imagem
        rect_logo = pygame.Rect(LARGURA/2 - 100, 40, 200, 100)
        pygame.draw.rect(tela, CORES['CINZA_ESC'], rect_logo, 2)
        mostrar_texto("LOGO EMPRESA", CORES['TEXTO_DARK'], LARGURA/2, 90, 'p')
        desenhar_botao(btn_teste_h, CORES['PRIMARIA'], (0, 100, 200), "INICIAR TESTE", CORES['BRANCO'])

        desenhar_botao(btn_admin_h, (80, 80, 80), (100, 100, 100), "PAINEL ADM", CORES['BRANCO'])
        desenhar_botao(btn_config_h, (80, 80, 80), (100, 100, 100), "CONFIGURAÇÕES", CORES['BRANCO'])

        # 4. ÍCONES DOS CANTOS (Pesquisa e Reclamação)
        # Superior Direito: Pesquisa
        rect_pesquisa = pygame.Rect(LARGURA - 120, 40, 80, 80)
        pygame.draw.circle(tela, (255, 200, 0), rect_pesquisa.center, 40) # Um círculo amarelo
        mostrar_texto("SUGESTÃO", CORES['TEXTO_DARK'], LARGURA - 120, 130, 'p')
        
        # Inferior Direito: Reclamação
        rect_reclamacao = pygame.Rect(LARGURA - 120, ALTURA - 120, 80, 80)
        pygame.draw.circle(tela, (200, 50, 50), rect_reclamacao.center, 40) # Um círculo vermelho
        mostrar_texto("OCORRIDO", CORES['TEXTO_DARK'], LARGURA - 120, ALTURA - 30, 'p')

        pygame.draw.rect(tela,CORES['CINZA_ESC'], btn_fechar_rect,border_radius=5)
        mostrar_texto("SAIR",CORES['BRANCO'],btn_fechar_rect.centerx, btn_fechar_rect.centery)

    # --- Lógica de Estados ---
    elif estado == 'LOGIN':
        usuario_atual = ""
        proximo_evento = 0
        mostrar_texto("SISTEMA DE CONTROLE DE FADIGA", CORES['AMARELO'], LARGURA/2, 150, 'm')

        # --- CAMPO NOME ---
        mostrar_texto("NOME DO OPERADOR:", cor_texto_padrao, LARGURA/2, 180, 'p')
        cor_borda_nome = CORES['AZUL'] if campo_focado == "NOME" else cor_caixas
        rect_nome = pygame.Rect(LARGURA/2 - 150, 200, 300, 45)
        pygame.draw.rect(tela, (30,30,30), rect_nome, border_radius=5)
        pygame.draw.rect(tela, cor_borda_nome, rect_nome, 2, border_radius=5)
        
        txt_nome = input_texto + ("|" if cursor_visivel and campo_focado == "NOME" else "")
        mostrar_texto(txt_nome, CORES['BRANCO'], LARGURA/2, 222, 'p')

        # --- CAMPO SENHA ---
        mostrar_texto("SENHA (4 PRIMEIROS DÍGITOS DO CPF):", cor_texto_padrao, LARGURA/2, 280, 'p')
        cor_borda_senha = CORES['AZUL'] if campo_focado == "SENHA" else cor_caixas
        rect_senha = pygame.Rect(LARGURA/2 - 150, 300, 300, 45)
        pygame.draw.rect(tela, (30,30,30), rect_senha, border_radius=5)
        pygame.draw.rect(tela, cor_borda_senha, rect_senha, 2, border_radius=5)
        
        # Mostra asteriscos para a senha
        txt_senha = ("*" * len(input_senha)) + ("|" if cursor_visivel and campo_focado == "SENHA" else "")
        mostrar_texto(txt_senha, CORES['BRANCO'], LARGURA/2, 322, 'p')


        # --- NOVO BOTÃO ENTRAR ---
        btn_entrar_rect = pygame.Rect(LARGURA/2 - 75, 360, 150, 45)
        
        # desenhar_botao(retangulo, cor_normal, cor_hover, texto, cor_texto, tamanho_fonte)
        desenhar_botao(btn_entrar_rect, (100, 100, 100), CORES['VERDE'], "ENTRAR", cor_texto_padrao, 'p')

        # O Botão voltar continua no canto inferior isolado
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])

        # --- MENSAGEM DE ERRO (REPOSICIONADA ABAIXO DO BOTÃO) ---
        if mensagem_login:
            # Y ajustado para 425 para dar respiro ao botão
            mostrar_texto(mensagem_login, (255, 50, 50), LARGURA/2, 425, 'p')

    elif estado == 'CONTAGEM':
        tela.fill(CORES['FUNDO']) # Fundo padrão
        
        # Calcula quanto tempo passou desde o clique
        tempo_passado = time.time() - tempo_inicio_contagem
        
        # Lógica do cronômetro regressivo
        if tempo_passado < 1:
            numero = "3"
        elif tempo_passado < 2:
            numero = "2"
        elif tempo_passado < 3:
            numero = "1"
        else:
            # Fim da contagem: Volta para o teste (ESPERA, GO ou NOGO)
            estado = estado_anterior
            # Ajustamos o próximo evento para o operador não ser pego de surpresa
            proximo_evento = time.time() + 0.5 

        # Desenha o número na tela se ainda estiver na contagem
        if tempo_passado < 3:
            mostrar_texto("PREPARE-SE...", (0, 0, 0), LARGURA/2, ALTURA/2 - 100, 'm')
            # Desenha o número grande no centro em PRETO
            mostrar_texto(numero, (0, 0, 0), LARGURA/2, ALTURA/2, 'g')

        
    elif estado == 'LOGOUT':
        tela.fill(CORES['PRETO']) # Garante a tela preta
        
        # Mensagem de agradecimento
        mostrar_texto("Logout realizado com sucesso!", CORES['BRANCO'], LARGURA/2, ALTURA/2 - 20, 'm')
        mostrar_texto(f"Obrigado pelo seu trabalho, {usuario_deslogando}.", cor_texto_padrao, LARGURA/2, ALTURA/2 + 30, 'p')
        
        # Quando o tempo acabar, volta para o Login
        if agora >= proximo_evento:
            estado = 'LOGIN'
            etapa_login = ""

    elif estado == 'PAUSA':
        # 1. Escurece o fundo (Efeito de sobreposição)
        superficie_overlay = pygame.Surface((LARGURA, ALTURA))
        superficie_overlay.set_alpha(150) # Transparência
        superficie_overlay.fill((0, 0, 0))
        tela.blit(superficie_overlay, (0,0))

        # 2. Janela Modal (Estilo W98)
        pygame.draw.rect(tela, (192, 192, 192), modal_rect)
        pygame.draw.rect(tela, (255, 255, 255), modal_rect, 2) # Brilho
        # Barra de título da modal (Azul clássico)
        barra_titulo = pygame.Rect(modal_rect.x, modal_rect.y, modal_rect.width, 35)
        pygame.draw.rect(tela, (0, 0, 128), barra_titulo)
        mostrar_texto("TESTE INTERROMPIDO", (255, 255, 255), modal_rect.centerx, modal_rect.y + 17, 'p')

        # 3. Botões
        desenhar_botao(btn_continuar, (192, 192, 192), (210, 210, 210), "CONTINUAR", (0,0,0))
        desenhar_botao(btn_reiniciar, (192, 192, 192), (210, 210, 210), "REINICIAR", (0,0,0))
        desenhar_botao(btn_fechar_teste, (150, 50, 50), (200, 50, 50), "CANCELAR E SAIR", (255,255,255))


    elif estado == 'CADASTRO':
        
        mostrar_texto("NOVO CADASTRO DE OPERADOR", CORES['AZUL'], LARGURA/2, 100, 'g')

        # Geometria das Caixas
        largura_padrao = 400
        altura_padrao = 45
        pos_x_centro = LARGURA/2 - (largura_padrao / 2)
        
        # Todas as caixas usam o exato mesmo 'pos_x_centro' e 'largura_padrao'
        rect_nome  = pygame.Rect(pos_x_centro, 150, largura_padrao, altura_padrao)
        rect_cpf   = pygame.Rect(pos_x_centro, 230, largura_padrao, altura_padrao)
        rect_setor = pygame.Rect(pos_x_centro, 310, largura_padrao, altura_padrao)
        rect_nivel = pygame.Rect(pos_x_centro, 390, largura_padrao, altura_padrao)

        # O Botão de Salvar agora tem a mesma largura do formulário (bloco sólido)
        btn_salvar_cad = pygame.Rect(pos_x_centro, 470, largura_padrao, 50) 
        
        # O Botão voltar continua no canto inferior isolado
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)

       # --- NOME ---
        # Título agora centralizado perfeitamente com a caixa (centerx)
        mostrar_texto("NOME COMPLETO:", cor_texto_padrao, rect_nome.centerx, rect_nome.y - 20, 'p')
        cor_b_nome = CORES['AZUL'] if campo_focado == "NOME" else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_caixas, rect_nome, border_radius=8)
        pygame.draw.rect(tela, cor_b_nome, rect_nome, 2, border_radius=8)
        cursor_n = "|" if campo_focado == "NOME" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_nome_cad + cursor_n, cor_texto_padrao, rect_nome.centerx, rect_nome.centery, 'm')

        # --- CPF ---
        mostrar_texto("CPF (APENAS NÚMEROS):", cor_texto_padrao, rect_cpf.centerx, rect_cpf.y - 20, 'p')
        cor_b_cpf = CORES['AZUL'] if campo_focado == "CPF" else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_caixas, rect_cpf, border_radius=8)
        pygame.draw.rect(tela, cor_b_cpf, rect_cpf, 2, border_radius=8)
        cursor_c = "|" if campo_focado == "CPF" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_cpf_cad + cursor_c, cor_texto_padrao, rect_cpf.centerx, rect_cpf.centery, 'm')

        # --- SETOR (Menu Cíclico) ---
        mostrar_texto("DEPARTAMENTO:", cor_texto_padrao, rect_setor.centerx, rect_setor.y - 20, 'p')
        texto_setor_atual = f"{lista_setores[idx_setor]} "
        desenhar_botao(rect_setor, cor_caixas, (100, 100, 120), texto_setor_atual, cor_texto_padrao, 'm')
        # DESENHA A BORDA FINA POR CIMA (Espessura 2)
        pygame.draw.rect(tela, CORES['CINZA_ESC'], rect_setor, 2, border_radius=8)

        # --- NÍVEL (Menu Cíclico) ---
        mostrar_texto("NÍVEL DE ACESSO:", cor_texto_padrao, rect_nivel.centerx, rect_nivel.y - 20, 'p')
        texto_nivel_atual = f"{lista_niveis[idx_nivel]}  "
        desenhar_botao(rect_nivel, cor_caixas, (100, 100, 120), texto_nivel_atual, cor_texto_padrao, 'm')
        pygame.draw.rect(tela, CORES['CINZA_ESC'], rect_nivel, 2, border_radius=8)

        # ==========================================
        # 3. BOTÕES DE AÇÃO E FEEDBACK
        # ==========================================
        desenhar_botao(btn_salvar_cad, (0, 150, 0), (0, 180, 0), "SALVAR NOVO USUÁRIO", CORES['BRANCO'])
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])

        # Renderização do Texto Digitado + Cursor piscando
        cursor_n = "|" if campo_focado == "NOME" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_nome_cad + cursor_n, cor_texto_padrao, rect_nome.centerx, rect_nome.centery, 'm')

        cursor_c = "|" if campo_focado == "CPF" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_cpf_cad + cursor_c, cor_texto_padrao, rect_cpf.centerx, rect_cpf.centery, 'm')

        desenhar_botao(btn_salvar_cad, (0, 150, 0), (0, 180, 0), "SALVAR", CORES['BRANCO'])

        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])

        # Mensagem de Feedback (Erro ou Sucesso)
        if mensagem_feedback:
            mostrar_texto(mensagem_feedback, cor_feedback, LARGURA/2, 540, 'p')

    elif estado == 'CARREGANDO':
            tela.fill(CORES['FUNDO'])
            mostrar_texto("AUTENTICANDO...", CORES['PRIMARIA'], LARGURA/2, ALTURA/2, 'g')
            
            # O cronômetro acabou?
            if time.time() > proximo_evento:
                if destino_pos_login == 'TESTE':
                    estado = 'CHECKS'
                elif destino_pos_login == 'MENU':
                    # Só deixa entrar se o nível for 1
                    if nivel_acesso == 1:
                        estado = 'MENU'
                    else:
                        # Se um espertinho tentar entrar no ADM sendo nível 0
                        estado = 'HOME' 
                        mensagem_login = "ACESSO NEGADO"

    elif estado == 'PESQUISA':
        tela.fill(COR_BG_PESQUISA)
        txt_info1 = fonte_p.render("Sugestões e críticas são feitas anonimamente.", True, COR_TEXTO_P)
        txt_info2 = fonte_sub_p.render("Caso queira se identificar, preencha o campo Nome:", True, COR_MUTED_P)
        tela.blit(txt_info1, (100, 60))
        tela.blit(txt_info2, (100, 90))
        
        tela.blit(fonte_p.render("Nome:", True, COR_TEXTO_P), (100, 155))
        tela.blit(fonte_p.render("Sugestão:", True, COR_TEXTO_P), (100, 245))
        tela.blit(fonte_p.render("Crítica / Reclamação:", True, COR_TEXTO_P), (100, 355))
        
        pygame.draw.rect(tela, COR_CARD_PESQUISA, rect_nome_p, border_radius=4)
        pygame.draw.rect(tela, COR_EMERALD_P if campo_ativo == "nome" else COR_CARD_PESQUISA, rect_nome_p, 2, border_radius=4)
        
        pygame.draw.rect(tela, COR_CARD_PESQUISA, rect_sugestao_p, border_radius=4)
        pygame.draw.rect(tela, COR_EMERALD_P if campo_ativo == "sugestao" else COR_CARD_PESQUISA, rect_sugestao_p, 2, border_radius=4)
        
        pygame.draw.rect(tela, COR_CARD_PESQUISA, rect_critica_p, border_radius=4)
        pygame.draw.rect(tela, COR_EMERALD_P if campo_ativo == "critica" else COR_CARD_PESQUISA, rect_critica_p, 2, border_radius=4)
        
        # Cursor dinâmico baseado em tempo de execução
        cursor_nome = "|" if campo_ativo == "nome" and time.time() % 1 > 0.5 else ""
        cursor_sug = "|" if campo_ativo == "sugestao" and time.time() % 1 > 0.5 else ""
        cursor_crit = "|" if campo_ativo == "critica" and time.time() % 1 > 0.5 else ""

        tela.blit(fonte_p.render(texto_nome + cursor_nome, True, COR_TEXTO_P), (110, 190))
        tela.blit(fonte_p.render(texto_sugestao + cursor_sug, True, COR_TEXTO_P), (110, 290))
        tela.blit(fonte_p.render(texto_critica + cursor_crit, True, COR_TEXTO_P), (110, 400))
        
        pygame.draw.rect(tela, COR_BOTAO_P, rect_enviar_p, border_radius=5)
        txt_btn = fonte_btn_p.render("Enviar", True, COR_BG_PESQUISA)
        tela.blit(txt_btn, (rect_enviar_p.centerx - txt_btn.get_width()//2, rect_enviar_p.centery - txt_btn.get_height()//2))

    elif estado == 'MENU':

        margem_x = LARGURA / 2

        # =========================================================
        # BOTÃO COMPARTILHADO: SAIR / LOGOUT (Visível para ambos)
        # =========================================================
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])
        # =========================================================
        # SALA 1 : MENU DO OPERADOR (NÍVEL 0)
        # =========================================================
        if nivel_acesso == 0:
            mostrar_texto("CALIBRAÇÃO DE ESTÍMULOS", CORES['AMARELO'], margem_x, 50, 'g')
            mostrar_texto(f"Operador Logado: {usuario_atual}", cor_texto_padrao, margem_x, 90, 'p')
            mostrar_texto("Complete o preparo antes de iniciar:", CORES['CINZA_CLARO'], margem_x, 140, 'p')
        
      
            # 2. Desenho do Bloco 1: BIPs
            cor_go = CORES['OK'] if checks.get('som_go') else cor_caixas
            pygame.draw.rect(tela, cor_go, btn_go_rect, border_radius=8)
            mostrar_texto("BIP AGUDO (GO)", cor_texto_padrao, btn_go_rect.centerx, btn_go_rect.centery, 'p')

            cor_nogo = CORES['OK'] if checks.get('som_nogo') else cor_caixas
            pygame.draw.rect(tela, cor_nogo, btn_nogo_rect, border_radius=8)
            mostrar_texto("BIP GRAVE (NOGO)", cor_texto_padrao, btn_nogo_rect.centerx, btn_nogo_rect.centery, 'p')

            # 3. Desenho do Bloco 2: Cores
            cor_cores = CORES['OK'] if checks.get('cores') else cor_caixas
            pygame.draw.rect(tela, cor_cores, btn_cores_rect, border_radius=8)
            
            if btn_cores_rect.collidepoint(mouse_pos):      
                pygame.draw.rect(tela, CORES['VERDE'], (btn_cores_rect.centerx - 110, btn_cores_rect.centery - 10, 20, 20), border_radius=4)
                pygame.draw.rect(tela, CORES['VERMELHO'], (btn_cores_rect.centerx + 90, btn_cores_rect.centery - 10, 20, 20), border_radius=4)
                mostrar_texto("REVISAR CORES", cor_texto_padrao, btn_cores_rect.centerx, btn_cores_rect.centery, 'p')
            else:
                mostrar_texto("REVISAR CORES", cor_texto_padrao, btn_cores_rect.centerx, btn_cores_rect.centery, 'p')

            # 4. Desenho do Botão Iniciar
            pode_iniciar = all(checks.values())
            cor_start = CORES['VERDE'] if pode_iniciar else cor_caixas
            
            pygame.draw.rect(tela, cor_start, btn_start_rect, border_radius=12)
            if not pode_iniciar:
                pygame.draw.rect(tela, (150, 0, 0), btn_start_rect, 2, border_radius=12)
                mostrar_texto("BLOQUEADO", cor_texto_padrao, btn_start_rect.centerx, btn_start_rect.centery, 'm')
            else:
                mostrar_texto("INICIAR TESTE", cor_texto_padrao, btn_start_rect.centerx, btn_start_rect.centery, 'm')

            #5. Desenho botão voltar
            desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])


        # =========================================================
        # SALA 2 : PAINEL DE GESTÃO - ADMIN (NÍVEL 1)
        # =========================================================
        elif nivel_acesso == 1:
            mostrar_texto("PAINEL DE GESTÃO", CORES['AZUL'], margem_x, 80, 'g')
            mostrar_texto(f"Gestor Logado: {usuario_atual}", cor_texto_padrao, margem_x, 130, 'm')

            # 2. Verifica banco de dados
            pasta_db = obter_caminho_externo()
            existe_db = os.path.exists(os.path.join(pasta_db, "log_foco_detalhado.csv"))

           # 1. Coordenadas exatas (Espaçamento de 70px entre cada botão)
            btn_hist_rect = pygame.Rect(margem_x - 175, 180, 350, 50)
            btn_cad_rect = pygame.Rect(margem_x - 175, 250, 350, 50)
            btn_grafico_rect = pygame.Rect(margem_x - 175, 320, 350, 50)
            btn_config_rect = pygame.Rect(margem_x - 175, 390, 350, 50)

# --- DESENHO DOS BOTÕES USANDO A FUNÇÃO MESTRA ---
            
            # Botão 1: Histórico
            if existe_db:
                desenhar_botao(btn_hist_rect, CORES['AZUL'], (0, 120, 200), "HISTÓRICO", CORES['BRANCO'])
            else:
                # Botão cinza/desabilitado se não tem banco de dados
                desenhar_botao(btn_hist_rect, CORES['CINZA_ESC'], CORES['CINZA_ESC'], "HISTÓRICO VAZIO", CORES['CINZA_CLARO'])
            
            # Botão 2: Cadastro
            desenhar_botao(btn_cad_rect, (200, 100, 0), (230, 120, 0), "CADASTRO", CORES['BRANCO'])

            # Botão 3: Gráfico Fadiga x Sono
            if existe_db:
                desenhar_botao(btn_grafico_rect, (100, 0, 120), (130, 0, 150), "GRÁFICO", CORES['BRANCO'])
            else:
                desenhar_botao(btn_grafico_rect, CORES['CINZA_ESC'], CORES['CINZA_ESC'], "GRÁFICO INDISPONÍVEL", CORES['CINZA_CLARO'])

            # Botão 4: Configurações
            desenhar_botao(btn_config_rect, (80, 80, 80), (130, 100, 100), "CONFIGURAÇÕES", CORES['BRANCO'])

    elif estado == 'CHECKS':
        tela.fill(CORES['FUNDO'])
        mostrar_texto("CHECKLIST DE EQUIPAMENTO", CORES['AZUL_TITULO'], LARGURA/2, 80, 'g')
        mostrar_texto("Por favor, teste os estímulos antes de iniciar.", (0,0,0), LARGURA/2, 110, 'p')

        # Função rápida para escolher a cor: Verde se testado, Cinza se pendente
        def cor_check(testado): return (0, 150, 50) if testado else (192, 192, 192)
        def cor_txt(testado): return (255, 255, 255) if testado else (0, 0, 0)

        # Desenha os 3 botões
        desenhar_botao(btn_ck_go, cor_check(checks['som_go']), (210,210,210), "1. TESTAR SOM 'GO'", cor_txt(checks['som_go']))
        desenhar_botao(btn_ck_nogo, cor_check(checks['som_nogo']), (210,210,210), "2. TESTAR SOM 'NOGO'", cor_txt(checks['som_nogo']))
        desenhar_botao(btn_ck_cor, cor_check(checks['cores']), (210,210,210), "3. TESTAR VISUAL", cor_txt(checks['cores']))

        # --- AMOSTRAS DE CORES (Legenda Visual) ---
        # Posicionadas ao lado direito do botão de Testar Visual
        tamanho_q = 40
        pos_x_amostra = btn_ck_cor.right + 30 # 30 pixels à direita do botão
        
        # 1. Quadrado Verde (GO) - Alinhado com a parte de cima do botão
        rect_verde = pygame.Rect(pos_x_amostra, btn_ck_cor.y - 15, tamanho_q, tamanho_q)
        pygame.draw.rect(tela, (0, 200, 0), rect_verde)      # Preenchimento Verde
        pygame.draw.rect(tela, (0, 0, 0), rect_verde, 2)     # Borda W98
        mostrar_texto("GO (OK)", (0, 150, 0), rect_verde.right + 40, rect_verde.centery, 'p')

        # 2. Quadrado Vermelho (NO-GO) - Alinhado um pouco abaixo
        rect_verm = pygame.Rect(pos_x_amostra, btn_ck_cor.y + 35, tamanho_q, tamanho_q)
        pygame.draw.rect(tela, (200, 0, 0), rect_verm)       # Preenchimento Vermelho
        pygame.draw.rect(tela, (0, 0, 0), rect_verm, 2)      # Borda W98
        mostrar_texto("NO-GO (N)", (200, 0, 0), rect_verm.right + 45, rect_verm.centery, 'p')

        # Se testou tudo, libera a passagem
        if all(checks.values()):
            desenhar_botao(btn_ck_avancar, (0, 0, 128), (0, 0, 200), "AVANÇAR →", (255, 255, 255))
        else:
            mostrar_texto("Teste todos os itens para continuar", (100, 100, 100), LARGURA/2, 445, 'p')



    elif estado == 'PERGUNTA_SONO':
            mostrar_texto("PREPARAÇÃO PARA O TESTE", CORES['AMARELO'], LARGURA/2, 100, 'g')
            mostrar_texto("Quantas horas você dormiu na última noite?", cor_texto_padrao, LARGURA/2, 200, 'm')
            
            # Desenha a caixa de texto
            caixa_rect = pygame.Rect(LARGURA/2 - 60, 260, 120, 60)
            pygame.draw.rect(tela, cor_caixas, caixa_rect, border_radius=10)
            pygame.draw.rect(tela, CORES['AZUL'], caixa_rect, 2, border_radius=10)
            
            # Efeito de cursor piscando na cor certa dependendo do tema
            cor_input = CORES['BRANCO'] if tema_escuro else (20, 20, 20)
            texto_exibicao = input_sono + "|" if time.time() % 1 > 0.5 else input_sono
            mostrar_texto(texto_exibicao, cor_input, caixa_rect.centerx, caixa_rect.centery, 'g')
            
            mostrar_texto("Digite o valor (ex: 7 ou 7.5) e pressione ENTER", CORES['CINZA_CLARO'], LARGURA/2, 400, 'p')
            
    # TELA DE CONFIGURAÇÕES
    # =========================================================
    elif estado == 'CONFIGURACOES':
        
        margem_x = LARGURA / 2

        # 1. Textos do Cabeçalho
        mostrar_texto("CONFIGURAÇÕES DO SISTEMA", CORES['AZUL'], margem_x, 80, 'g')
        mostrar_texto("Ajuste as preferências visuais da interface", CORES['CINZA_CLARO'], margem_x, 130, 'p')

        # 2. Geometria dos Botões
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        btn_tema_rect = pygame.Rect(margem_x - 175, 250, 350, 60) # Botão gigante no centro

        # Geometria do botão voltar (Canto inferior esquerdo)
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)

        # Desenha o botão usando a Função Mestra
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])
        # 4. Desenho do Interruptor do Tema (Comportamento Dinâmico)
        if tema_escuro:
            cor_tema_btn = (50, 50, 50)
            texto_tema = "TEMA ATUAL: ESCURO 🌙"
            cor_texto_tema = CORES['BRANCO']
        else:
            cor_tema_btn = (200, 200, 200)
            texto_tema = "TEMA ATUAL: CLARO ☀️"
            # Precisamos de uma cor escura para ler o texto se o botão ficar branco
            cor_texto_tema = (30, 30, 30) 

        # Efeito visual de passar o mouse por cima
        if btn_tema_rect.collidepoint(mouse_pos):
            cor_tema_btn = (80, 80, 80) if tema_escuro else (220, 220, 220)

        desenhar_botao(btn_tema_rect, (80, 80, 80), (130, 100, 100), "TEMA CLARO / ESCURO", CORES['BRANCO'])

        # 5. Processamento dos Cliques
        if clique:
            if btn_voltar_rect.collidepoint(mouse_pos):
                estado = 'HOME' # Apenas volta para o painel de gestão
            
            elif btn_tema_rect.collidepoint(mouse_pos):
                # A MÁGICA: O comando "not" inverte o booleano. 
                # Se era True, vira False. Se era False, vira True.
                tema_escuro = not tema_escuro

    elif estado in ['ESPERA', 'ESTIMULO', 'FEEDBACK']:
        desenhar_barra_progresso()
        # Desenha o botão X no canto
        desenhar_botao(btn_x_fec_rect, (150, 0, 0), (200, 0, 0), "X", (255, 255, 255))
        if estado == 'ESPERA':
            if agora >= proximo_evento:
                if not lista_estimulos: estado = 'FIM'
                else:
                    mostrar_texto("Aguarde o estímulo...", CORES['CINZA_CLARO'], LARGURA/2, ALTURA/2 + 200, 'p')
                    tipo_atual = random.choice(['VISUAL', 'SONORO'])
                    subtipo_atual = lista_estimulos.pop()

                    momento_estimulo = agora;
                    estado = 'ESTIMULO';
                    proximo_evento = agora + 1.2

                    if tipo_atual == 'SONORO':
                        if subtipo_atual == 'GO':
                            som_go.play()
                        else:
                            som_nogo.play()
            

        elif estado == 'ESTIMULO':       
            if tipo_atual == 'VISUAL':
                cor = CORES['VERDE'] if subtipo_atual == 'GO' else CORES['VERMELHO']
                pygame.draw.rect(tela, cor, (LARGURA/2-80, ALTURA/2-80, 160, 160), border_radius=15)
            else:
                pygame.draw.circle(tela, CORES['AZUL'], (LARGURA/2, ALTURA/2), 40)

     
            if clique:
                if subtipo_atual == 'GO':
                    latencia = (agora - momento_estimulo) * 1000
                    if latencia > 150:
                        dados_coletados.append((tipo_atual, latencia))
                        estado = 'FEEDBACK'; proximo_evento = agora + 0.6
                else:
                    erros_impulso += 1
                    estado = 'FEEDBACK'; proximo_evento = agora + 0.6

            elif agora >= proximo_evento:
                if subtipo_atual == 'GO': erros_omissao += 1
                tentativa_atual += 1
                estado = 'ESPERA' if tentativa_atual < TENTATIVAS_TOTAIS else 'FIM'
                proximo_evento = agora + random.uniform(1.5,3.0)

        elif estado == 'FEEDBACK':
            txt = "CORRETO!" if subtipo_atual == 'GO' else "ERRO!"
            cor = CORES['VERDE'] if subtipo_atual == 'GO' else CORES['VERMELHO']
            mostrar_texto(txt, cor, LARGURA/2, ALTURA/2, 'm')
            if agora >= proximo_evento:
                tentativa_atual += 1
                estado = 'ESPERA' if tentativa_atual < TENTATIVAS_TOTAIS else 'FIM'
                proximo_evento = agora + random.uniform(1.0,3.5)

        

    elif estado == 'FIM':
            # =========================================================
            # 1. CÁLCULOS (Ocultos do Usuário)
            # =========================================================
            tempos_v = [d[1] for d in dados_coletados if d[0] == 'VISUAL']
            tempos_s = [d[1] for d in dados_coletados if d[0] == 'SONORO']
            media_v = sum(tempos_v)/len(tempos_v) if tempos_v else 0
            media_s = sum(tempos_s)/len(tempos_s) if tempos_s else 0
            pior_media = max(media_v, media_s)

            # O Sistema julga o operador
            reprovado = pior_media > limite_atual

            # =========================================================
            # 2. SALVAMENTO (Sempre salva os dados reais no banco)
            # =========================================================
            if not foi_salvo:
                print(f"Salvando os dados de: {usuario_atual}")
                salvar_resultados(dados_coletados, erros_impulso, erros_omissao, usuario_atual, horas_sono_atual)
                foi_salvo = True

            # =========================================================
            # 3. INTERFACE DE TRIAGEM CEGA (O que o Operador vê)
            # =========================================================
            tela.fill(CORES['FUNDO']) # Fundo padrão (Cinza W98 ou sua cor)

            # Painel de Aviso Central
            painel_rect = pygame.Rect(LARGURA/2 - 300, 150, 600, 200)

            if reprovado:
                # ALERTA DE REPROVAÇÃO (Amarelo industrial, sem pânico)
                pygame.draw.rect(tela, (220, 180, 0), painel_rect) # Fundo Amarelo
                pygame.draw.rect(tela, (0, 0, 0), painel_rect, 4)  # Borda Grossa Preta
                mostrar_texto("TESTE CONCLUÍDO", (0, 0, 0), LARGURA/2, 200, 'g')
                mostrar_texto("Por favor, dirija-se à sala da Supervisão", (0, 0, 0), LARGURA/2, 260, 'm')
                mostrar_texto("antes de iniciar o seu turno.", (0, 0, 0), LARGURA/2, 300, 'm')
            else:
                # SUCESSO (Verde escuro, passagem livre)
                pygame.draw.rect(tela, (0, 150, 50), painel_rect)  # Fundo Verde
                pygame.draw.rect(tela, (0, 0, 0), painel_rect, 4)  # Borda Grossa Preta
                mostrar_texto("TESTE CONCLUÍDO", (255, 255, 255), LARGURA/2, 200, 'g')
                mostrar_texto(f"Bom trabalho, {usuario_atual}.", (255, 255, 255), LARGURA/2, 260, 'm')
                mostrar_texto("Acesso Liberado. Tenha um excelente turno!", (255, 255, 255), LARGURA/2, 300, 'm')

            # Botão de Encerrar
            desenhar_botao(btn_finalizar_rect, (192, 192, 192), (210, 210, 210), "ENCERRAR SESSÃO", (0,0,0))

  # ==========================================
    # GERENCIADOR DE CURSOR (UX)
    # ==========================================
    if mouse_sobre_btn:
        # Muda para a "mãozinha"
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        # Volta para a setinha padrão
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        

    pygame.display.flip()
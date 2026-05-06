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
    som_go = pygame.mixer.Sound(resource_path("som_go.wav"))
    som_nogo = pygame.mixer.Sound(resource_path("som_nogo.wav"))
    audio_on = True
except Exception as e:
    print(f"Aviso: Não foi possível carregar os sons: {e}")
    audio_on = False


def cadastrar_novo_operador():
    
    # Prepara a janelinha suspensa
    root = tk.Tk()
    root.withdraw() # Esconde a janela principal do tkinter
    root.attributes("-topmost", True) # Garante que ela apareça na frente do Pygame

    caminho_csv = os.path.join(obter_caminho_externo(), "operadores.csv")
    nome = simpledialog.askstring("Novo Cadastro", "Digite o nome do novo operador:")
    
    if nome:
        cpf = simpledialog.askstring("Novo Cadastro", "Digite o cpf do novo operador. Apenas Números")
        if cpf and cpf.isdigit and len(cpf) == 11:
            nome_up = nome.strip().upper()        
        try:
            # 1. Verifica se já existe para não duplicar "viga sobre viga"
            df = pd.read_csv(caminho_csv, dtype={'CPF': str})
            # Use o nome da coluna EXATAMENTE como está no seu f.write ("Nome")
            if cpf in df['CPF'].values:
                messagebox.showwarning("Aviso", f"CPF já cadastrado")
            else:
                # 2. Adiciona ao arquivo (Nível 0 = Operador)
                with open(caminho_csv, 'a', encoding='utf-8') as f:
                    f.write(f"{nome_up},{cpf},0\n")
                messagebox.showinfo("Sucesso", f"Operador {nome_up} cadastrado com sucesso!")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao acessar banco de dados: {e}")
    else:
        messagebox.showerror("ERRO")
        messagebox.showinfo("CPF INVÁLIDO, DIGITE OS 11 DIGITOS NUMÉRICOS")
    
    root.destroy() # Fecha a janelinha para não travar o Pygame



inicializar_banco_operadores()

def validar_login():
    global estado, usuario_atual, nivel_acesso, mensagem_login, input_texto, input_senha, campo_focado, proximo_evento
    global limite_atual, em_calibracao
    caminho_csv = os.path.join(obter_caminho_externo(), "operadores.csv")
    estado = 'LOGIN'
    tema_escuro = True

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
                nivel_acesso = int(user_row.iloc[0]['Nivel'])
                estado = 'CARREGANDO'
                proximo_evento = time.time() + 2.0
                input_texto = ""; input_senha = ""; campo_focado = "NOME"
                
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

CORES = {
    'PRETO': (15, 15, 15),
    'BRANCO': (240, 240, 240),
    'VERDE': (46, 204, 113),
    'VERMELHO': (231, 76, 60),
    'AMARELO': (241, 196, 15),
    'AZUL': (52, 152, 219),
    'CINZA_ESC': (30, 30, 30),
    'CINZA_CLARO': (70, 70, 70),
    'OK': (39, 174, 96)
}

LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
try:
    icone_imagem = pygame.image.load(resource_path("icon.png"))
    pygame.display.set_icon(icone_imagem)
except Exception as e:
    print(f"Aviso: Ícone não carregado: {e}")
pygame.display.set_icon(icone_imagem)
pygame.display.set_caption("Controle de Fadiga PCP - Eng. Diego Vieira")

fontes = {
    'p': pygame.font.SysFont("Segoe UI", 18),
    'm': pygame.font.SysFont("Segoe UI", 28, bold=True),
    'g': pygame.font.SysFont("Segoe UI", 50, bold=True)
}

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
def salvar_resultados(dados, erros_i, erros_o, usuario):
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
                escritor.writerow(['Operador','Data_Hora', 'Media_Visual', 'Media_Sonora', 'Media_Geral', 'Status', 'Erros_Impulso', 'Erros_Omissao','Observacoes'])
            
            escritor.writerow([
                usuario.upper(), #Nome do Operador
                datetime.now().strftime("%Y-%m-%d %H:%M"), 
                round(media_v, 2), 
                round(media_s, 2), 
                round(media_g, 2), 
                status, 
                erros_i, 
                erros_o,
                "" #Observação vazia
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

som_go = pygame.mixer.Sound(resource_path("som_go.wav"))
som_nogo = pygame.mixer.Sound(resource_path("som_nogo.wav"))

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
# --- PARÂMETROS DE SEGURANÇA ---
LIMITE_PADRAO_FABRICA = 0.400  # Tempo em segundos (400ms)

def mostrar_texto(txt, cor, x, y, fonte='p', centro=True):
    superficie = fontes[fonte].render(txt, True, cor)
    if centro:
        rect = superficie.get_rect(center=(x, y))
    else:
        rect = superficie.get_rect(topleft=(x, y))
    tela.blit(superficie, rect)

def desenhar_barra_progresso():
    progresso = (tentativa_atual / TENTATIVAS_TOTAIS) * LARGURA
    pygame.draw.rect(tela, cor_caixas, (0, 0, LARGURA, 10))
    pygame.draw.rect(tela, CORES['AZUL'], (0, 0, progresso, 10))

clock = pygame.time.Clock()
pygame.key.set_repeat(300,50)
foi_salvo = False
etapa_login ="NOME"
input_senha = ""

# --- Loop Principal ---
while True:
#LIMPEZA INICIAL
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
    mouse_pos = pygame.mouse.get_pos()
    clique = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            clique = True     
        
        # Lógica de teclado APENAS se estiver no LOGIN
        if event.type == pygame.KEYDOWN and estado == 'LOGIN':
            mensagem_login = ""
            #LÓGICA DE AUTENTICAÇÃO
            if event.key == pygame.K_RETURN:
            
                if campo_focado == "NOME":
                    if input_texto.upper() == "ADMIN":
                        usuario_atual = "ADMIN"
                        nivel_acesso = 1
                        estado = 'MENU'
                        input_texto = ""
                    else:
                        campo_focado = "SENHA"
                else:
                    validar_login()

            elif event.key == pygame.K_BACKSPACE:
                if campo_focado == "NOME": input_texto = input_texto[:-1]
                else: input_senha = input_senha[:-1]

            elif event.key == pygame.K_TAB: # Facilitador: TAB troca de campo
                campo_focado = "SENHA" if campo_focado == "NOME" else "NOME"

            else:
                if event.unicode.isprintable():
                    if campo_focado == "NOME":
                        input_texto += event.unicode
                    elif campo_focado == "SENHA" and len(input_senha) < 4:
                        if event.unicode.isdigit(): # Garante que senha seja só número
                            input_senha += event.unicode

                
    # --- Lógica de Estados ---
    if estado == 'LOGIN':
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


        # Clique com o mouse para trocar de campo
        if clique:
            if rect_nome.collidepoint(mouse_pos): campo_focado = "NOME"
            elif rect_senha.collidepoint(mouse_pos): campo_focado = "SENHA"

        # --- NOVO BOTÃO ENTRAR ---
        btn_entrar_rect = pygame.Rect(LARGURA/2 - 75, 360, 150, 45)
        
        # Hover: Cinza (100,100,100) para Verde
        cor_btn = CORES['VERDE'] if btn_entrar_rect.collidepoint(mouse_pos) else (100, 100, 100)
        
        pygame.draw.rect(tela, cor_btn, btn_entrar_rect, border_radius=10)
        mostrar_texto("ENTRAR", cor_texto_padrao, btn_entrar_rect.centerx, btn_entrar_rect.centery, 'p')

        # --- MENSAGEM DE ERRO (REPOSICIONADA ABAIXO DO BOTÃO) ---
        if mensagem_login:
            # Y ajustado para 425 para dar respiro ao botão
            mostrar_texto(mensagem_login, (255, 50, 50), LARGURA/2, 425, 'p')

        # Lógica de Clique no Botão
        if clique and btn_entrar_rect.collidepoint(mouse_pos):
            validar_login()

        
    elif estado == 'LOGOUT':
        tela.fill(CORES['PRETO']) # Garante a tela preta
        
        # Mensagem de agradecimento
        mostrar_texto("Logout realizado com sucesso!", CORES['BRANCO'], LARGURA/2, ALTURA/2 - 20, 'm')
        mostrar_texto(f"Obrigado pelo seu trabalho, {usuario_deslogando}.", cor_texto_padrao, LARGURA/2, ALTURA/2 + 30, 'p')
        
        # Quando o tempo acabar, volta para o Login
        if agora >= proximo_evento:
            estado = 'LOGIN'
            etapa_login = ""

    elif estado == 'CARREGANDO':
        tela.fill(CORES['PRETO'])
        
        # Centraliza o texto de carregamento
        mostrar_texto("AUTENTICANDO OPERADOR...", CORES['AMARELO'], LARGURA/2, ALTURA/2 - 20, 'p')
        
        # Opcional: Uma barra de progresso simples
        progresso = 1.0 - (proximo_evento - agora) / 2.0 # Vai de 0 a 1
        largura_barra = 300 * max(0, min(1, progresso))
        pygame.draw.rect(tela, (50, 50, 50), (LARGURA/2 - 150, ALTURA/2 + 20, 300, 10), border_radius=5)
        pygame.draw.rect(tela, CORES['VERDE'], (LARGURA/2 - 150, ALTURA/2 + 20, largura_barra, 10), border_radius=5)

        if agora >= proximo_evento:
            estado = 'MENU'

    elif estado == 'MENU':

        margem_x = LARGURA / 2

        # =========================================================
        # BOTÃO COMPARTILHADO: SAIR / LOGOUT (Visível para ambos)
        # =========================================================
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        cor_voltar = (100, 30, 30) if btn_voltar_rect.collidepoint(mouse_pos) else (60, 60, 60)

        pygame.draw.rect(tela, cor_voltar, btn_voltar_rect, border_radius=10)
        pygame.draw.rect(tela, CORES['CINZA_CLARO'], btn_voltar_rect, 1, border_radius=10)
        mostrar_texto("← SAIR", CORES['BRANCO'], btn_voltar_rect.centerx, btn_voltar_rect.centery, 'p')


        # =========================================================
        # SALA 1 : MENU DO OPERADOR (NÍVEL 0)
        # =========================================================
        if nivel_acesso == 0:
            mostrar_texto("CALIBRAÇÃO DE ESTÍMULOS", CORES['AMARELO'], margem_x, 50, 'g')
            mostrar_texto(f"Operador Logado: {usuario_atual}", cor_texto_padrao, margem_x, 90, 'p')
            mostrar_texto("Complete o preparo antes de iniciar:", CORES['CINZA_CLARO'], margem_x, 140, 'p')

            # 1. Coordenadas dos botões (Operador)
            btn_go_rect = pygame.Rect(margem_x - 240, 220, 230, 45)
            btn_nogo_rect = pygame.Rect(margem_x + 10, 220, 230, 45)
            btn_cores_rect = pygame.Rect(margem_x - 115, 290, 230, 45) 
            btn_start_rect = pygame.Rect(margem_x - 150, 460, 300, 70)

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


        # =========================================================
        # SALA 2 : PAINEL DE GESTÃO - ADMIN (NÍVEL 1)
        # =========================================================
        elif nivel_acesso == 1:
            mostrar_texto("PAINEL DE GESTÃO", CORES['AZUL'], margem_x, 80, 'g')
            mostrar_texto(f"Gestor Logado: {usuario_atual}", cor_texto_padrao, margem_x, 130, 'm')

            # 1. Coordenadas dos botões (Admin) - Alinhados no Centro
            btn_hist_rect = pygame.Rect(margem_x - 175, 220, 350, 60)
            btn_cad_rect = pygame.Rect(margem_x - 175, 300, 350, 60)
            btn_grafico_rect = pygame.Rect(margem_x - 175, 320, 350, 50)
            btn_config_rect = pygame.Rect(margem_x - 175, 380, 350, 60) 

            # 2. Verifica banco de dados
            pasta_db = obter_caminho_externo()
            existe_db = os.path.exists(os.path.join(pasta_db, "log_foco_detalhado.csv"))

            # 3. Desenha os Botões do Admin com Hover (efeito visual)
            # Botão Histórico
            cor_h = (0, 120, 200) if btn_hist_rect.collidepoint(mouse_pos) and existe_db else (CORES['AZUL'] if existe_db else cor_caixas)
            pygame.draw.rect(tela, cor_h, btn_hist_rect, border_radius=10)
            mostrar_texto("HISTÓRICO ", cor_texto_padrao, btn_hist_rect.centerx, btn_hist_rect.centery, 'm')
            
            # Botão Cadastro
            cor_c = (230, 120, 0) if btn_cad_rect.collidepoint(mouse_pos) else (200, 100, 0)
            pygame.draw.rect(tela, cor_c, btn_cad_rect, border_radius=10)
            mostrar_texto("CADASTRO", cor_texto_padrao, btn_cad_rect.centerx, btn_cad_rect.centery, 'm')

            # Botão Configurações (Prepara para o Tema)
            cor_cfg = (100, 100, 100) if btn_config_rect.collidepoint(mouse_pos) else (80, 80, 80)
            pygame.draw.rect(tela, cor_cfg, btn_config_rect, border_radius=10)
            mostrar_texto("CONFIGURAÇÕES", cor_texto_padrao, btn_config_rect.centerx, btn_config_rect.centery, 'm')


        # =========================================================
        # LÓGICA GERAL DE CLIQUES DA TELA DE MENU
        # =========================================================
        if clique:
            agora = time.time()
            
            # 1. Clique Comum (Sair)
            if btn_voltar_rect.collidepoint(mouse_pos):
                usuario_deslogando = usuario_atual 
                estado = 'LOGOUT'
                proximo_evento = agora + 2 
                usuario_atual = ""
                input_texto = ""
                for chave in checks: checks[chave] = False 
            
            # 2. Cliques Exclusivos do Operador
            elif nivel_acesso == 0:
                if btn_go_rect.collidepoint(mouse_pos):
                    som_go.play(); checks['som_go'] = True
                elif btn_nogo_rect.collidepoint(mouse_pos):
                    som_nogo.play(); checks['som_nogo'] = True
                elif btn_cores_rect.collidepoint(mouse_pos):
                    checks['cores'] = True
                elif btn_start_rect.collidepoint(mouse_pos) and pode_iniciar:
                    tentativa_atual = 0
                    dados_coletados = []
                    erros_impulso = 0
                    erros_omissao = 0
                    lista_estimulos = (['GO']*14 + ['NOGO']*6)
                    random.shuffle(lista_estimulos)
                    estado = 'ESPERA'
                    proximo_evento = agora + 1.2

            # 3. Cliques Exclusivos do Administrador
            elif nivel_acesso == 1:
                if btn_hist_rect.collidepoint(mouse_pos) and existe_db:
                    import dashboard
                    dashboard.gerar_analise()
                elif btn_cad_rect.collidepoint(mouse_pos):
                    cadastrar_novo_operador()
                elif btn_config_rect.collidepoint(mouse_pos):
                    # Aqui vamos jogar ele para a tela de configurações!
                    estado = 'CONFIGURACOES'  

    # =========================================================
    # TELA DE CONFIGURAÇÕES (Admin)
    # =========================================================
    elif estado == 'CONFIGURACOES':
        
        margem_x = LARGURA / 2

        # 1. Textos do Cabeçalho
        mostrar_texto("CONFIGURAÇÕES DO SISTEMA", CORES['AZUL'], margem_x, 80, 'g')
        mostrar_texto("Ajuste as preferências visuais da interface", CORES['CINZA_CLARO'], margem_x, 130, 'p')

        # 2. Geometria dos Botões
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        btn_tema_rect = pygame.Rect(margem_x - 175, 250, 350, 60) # Botão gigante no centro

        # 3. Desenho do Botão Voltar (Idêntico ao do Menu)
        cor_voltar = (100, 30, 30) if btn_voltar_rect.collidepoint(mouse_pos) else (60, 60, 60)
        pygame.draw.rect(tela, cor_voltar, btn_voltar_rect, border_radius=10)
        pygame.draw.rect(tela, CORES['CINZA_CLARO'], btn_voltar_rect, 1, border_radius=10)
        mostrar_texto("← VOLTAR", CORES['BRANCO'], btn_voltar_rect.centerx, btn_voltar_rect.centery, 'p')

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

        pygame.draw.rect(tela, cor_tema_btn, btn_tema_rect, border_radius=10)
        pygame.draw.rect(tela, CORES['AZUL'], btn_tema_rect, 2, border_radius=10) # Borda azul fixa
        mostrar_texto(texto_tema, cor_texto_tema, btn_tema_rect.centerx, btn_tema_rect.centery, 'm')

        # 5. Processamento dos Cliques
        if clique:
            if btn_voltar_rect.collidepoint(mouse_pos):
                estado = 'MENU' # Apenas volta para o painel de gestão
            
            elif btn_tema_rect.collidepoint(mouse_pos):
                # A MÁGICA: O comando "not" inverte o booleano. 
                # Se era True, vira False. Se era False, vira True.
                tema_escuro = not tema_escuro

    elif estado in ['ESPERA', 'ESTIMULO', 'FEEDBACK']:
        desenhar_barra_progresso()
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
        # 1. Salva os dados brutos primeiro (Sempre o mais importante)
        if not foi_salvo:
            print(f"Salvando os dados de: {usuario_atual}")
            # Lembre-se de depois colocar o status_geral no seu salvar_resultados!
            salvar_resultados(dados_coletados, erros_impulso, erros_omissao, usuario_atual)
            foi_salvo = True

        # 2. Cálculos de Médias
        tempos_v = [d[1] for d in dados_coletados if d[0] == 'VISUAL']
        tempos_s = [d[1] for d in dados_coletados if d[0] == 'SONORO']
        media_v = sum(tempos_v)/len(tempos_v) if tempos_v else 0
        media_s = sum(tempos_s)/len(tempos_s) if tempos_s else 0
        
        # O pior resultado (mais lento) dita a segurança da fábrica
        pior_media = max(media_v, media_s)

        # =========================================================
        # 3. O NOVO MOTOR DE DIAGNÓSTICO (Limite Dinâmico)
        # =========================================================
        # Limite global vem do Login (limite_atual). A zona amarela é 10% mais rigorosa.
        limite_alerta = limite_atual * 0.90 

        # Função interna rápida para julgar as parciais e o geral
        def avaliar_tempo(media_teste):
            if media_teste <= limite_alerta:
                return "NORMAL", CORES['VERDE']
            elif media_teste <= limite_atual:
                return "ATENÇÃO", CORES['AMARELO']
            else:
                return "FADIGA", CORES['VERMELHO']

        # Diagnósticos individuais das caixinhas
        status_v, cor_v = avaliar_tempo(media_v)
        status_s, cor_s = avaliar_tempo(media_s)

        # Diagnóstico Geral (A Catraca)
        if pior_media <= limite_alerta:
            status_linha1 = "APROVADO"
            status_linha2 = "FOCO NORMAL"
            cor_geral = CORES['VERDE']
        elif pior_media <= limite_atual:
            status_linha1 = "ATENÇÃO REDUZIDA"
            status_linha2 = "ACESSO LIBERADO"
            cor_geral = CORES['AMARELO']
        else:
            status_linha1 = "FADIGA CRÍTICA"
            status_linha2 = "OPERADOR BLOQUEADO"
            cor_geral = CORES['VERMELHO']        # =========================================================

        # --- Interface Refinada ---
        mostrar_texto("DADOS POR MODALIDADE", CORES['AMARELO'], LARGURA/2, 80, 'm')
        
        # Bloco Visual
        pygame.draw.rect(tela, cor_caixas, (100, 130, 280, 100), border_radius=10)
        mostrar_texto(f"VISUAL: {media_v:.1f} ms", cor_texto_padrao, 240, 160, 'm')
        mostrar_texto(status_v, cor_v, 240, 200, 'p')

        # Bloco Sonoro
        pygame.draw.rect(tela, cor_caixas, (420, 130, 280, 100), border_radius=10)
        mostrar_texto(f"SONORO: {media_s:.1f} ms", cor_texto_padrao, 560, 160, 'm')
        mostrar_texto(status_s, cor_s, 560, 200, 'p')

# Status Unificado (O Veredito Final)
        pygame.draw.line(tela, CORES['CINZA_CLARO'], (100, 270), (700, 270), 2)
        mostrar_texto("VEREDITO GERAL:", cor_texto_padrao, LARGURA/2, 295, 'p') # Subi um pouco
        
        # Desenha as duas linhas separadas
        mostrar_texto(status_linha1, cor_geral, LARGURA/2, 335, 'g')
        mostrar_texto(status_linha2, cor_geral, LARGURA/2, 375, 'g')

        # --- NOVIDADE: Transparência de Segurança ---
        if em_calibracao:
             mostrar_texto("(Sistema em Fase de Calibração Pessoal - Padrão Fábrica)", CORES['AMARELO'], LARGURA/2, 440, 'p')
        else:
             mostrar_texto(f"(Sua margem de corte hoje é de: {limite_atual:.0f} ms)", cor_texto_padrao, LARGURA/2, 440, 'p')

        # Botão de retorno
        mostrar_texto("Clique para voltar ao menu", CORES['CINZA_CLARO'], LARGURA/2, 550, 'p')          
        if clique:
                #reset de variáveis
            checks = {
                    "som_L": False, 
                    "som_R": False, 
                    "som_go": False, 
                    "som_nogo": False, 
                    "cores": False
                }
                
            # 3. LIMPEZA DE DADOS (Zera as estatísticas do teste que acabou)
            dados_coletados.clear()
            erros_impulso = 0
            erros_omissao = 0
            
            # 4. RESET DA TRAVA DE SALVAMENTO
            # Se você usou a variável 'foi_salvo' que sugeri:
            foi_salvo = False 
            # RESET DE ESTADO
            estado = 'MENU'

    pygame.display.flip()
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
    """ Retorna o caminho absoluto para o recurso, seja no modo script ou .exe """
    try:
        # Caminho da pasta temporária do PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
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
    global estado, usuario_atual, nivel_acesso, mensagem_login, input_texto, input_senha, campo_focado    
    caminho_csv = os.path.join(obter_caminho_externo(), "operadores.csv")
    
    if len(input_senha) < 4:
        mensagem_login = "A SENHA DEVE TER 4 DÍGITOS!"
        return

    try:
        df = pd.read_csv(caminho_csv, dtype={'CPF': str})
        # 1. Limpeza dos dados de entrada
        nome_busca = input_texto.strip().upper()
        
        # 2. Busca o usuário
        user_row = df[df['Nome'].str.upper() == nome_busca]        
        if not user_row.empty:
            cpf_completo = str(user_row.iloc[0]['CPF']).strip()
            # Compara os 4 últimos do CPF com o que foi digitado
            if input_senha == cpf_completo[-4:]:
                usuario_atual = nome_busca
                nivel_acesso = int(user_row.iloc[0]['Nivel'])
                estado = 'MENU'
                # Limpa tudo para a próxima vez
                input_texto = ""; input_senha = ""; campo_focado = "NOME"
                print(f"✅ Login realizado: {usuario_atual}")
            else:
                mensagem_login = "SENHA INCORETA!"
                input_senha = ""
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
pygame.display.set_caption("Controle de Fadiga PCP - Eng. Diego Vieira")

fontes = {
    'p': pygame.font.SysFont("Segoe UI", 18),
    'm': pygame.font.SysFont("Segoe UI", 28, bold=True),
    'g': pygame.font.SysFont("Segoe UI", 50, bold=True)
}

# --- Variáveis de Calibração ---
checks = {"som_L": False,"som_R":False ,"som_go": False, "som_nogo": False, "cores": False}

# --- Lógica de Diagnóstico ---
def obter_diagnostico(media_ms):
    if media_ms == 0: return "SEM DADOS", CORES['BRANCO']
    if media_ms < 350: return "CONCENTRADO (ELITE)", CORES['VERDE']
    elif 350 <= media_ms < 450: return "ALERTA (NORMAL)", CORES['BRANCO']
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

def mostrar_texto(txt, cor, x, y, fonte='p', centro=True):
    superficie = fontes[fonte].render(txt, True, cor)
    if centro:
        rect = superficie.get_rect(center=(x, y))
    else:
        rect = superficie.get_rect(topleft=(x, y))
    tela.blit(superficie, rect)

def desenhar_barra_progresso():
    progresso = (tentativa_atual / TENTATIVAS_TOTAIS) * LARGURA
    pygame.draw.rect(tela, CORES['CINZA_ESC'], (0, 0, LARGURA, 10))
    pygame.draw.rect(tela, CORES['AZUL'], (0, 0, progresso, 10))

clock = pygame.time.Clock()
pygame.key.set_repeat(300,50)
foi_salvo = False
etapa_login ="NOME"
input_senha = ""

# --- Loop Principal ---
while True:
    #LIMPEZA INICIAL
    tela.fill(CORES['PRETO'])
    agora = time.time()
    mouse_pos = pygame.mouse.get_pos()
    clique = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            clique = True     
        # Lógica de digitação
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
        mostrar_texto("SISTEMA DE CONTROLE DE FADIGA", CORES['AMARELO'], LARGURA/2, 150, 'm')

        # --- CAMPO NOME ---
        mostrar_texto("NOME DO OPERADOR:", CORES['BRANCO'], LARGURA/2, 180, 'p')
        cor_borda_nome = CORES['AZUL'] if campo_focado == "NOME" else CORES['CINZA_ESC']
        rect_nome = pygame.Rect(LARGURA/2 - 150, 200, 300, 45)
        pygame.draw.rect(tela, (30,30,30), rect_nome, border_radius=5)
        pygame.draw.rect(tela, cor_borda_nome, rect_nome, 2, border_radius=5)
        
        txt_nome = input_texto + ("|" if cursor_visivel and campo_focado == "NOME" else "")
        mostrar_texto(txt_nome, CORES['BRANCO'], LARGURA/2, 222, 'p')

        # --- CAMPO SENHA ---
        mostrar_texto("SENHA (4 DÍGITOS DO CPF):", CORES['BRANCO'], LARGURA/2, 280, 'p')
        cor_borda_senha = CORES['AZUL'] if campo_focado == "SENHA" else CORES['CINZA_ESC']
        rect_senha = pygame.Rect(LARGURA/2 - 150, 300, 300, 45)
        pygame.draw.rect(tela, (30,30,30), rect_senha, border_radius=5)
        pygame.draw.rect(tela, cor_borda_senha, rect_senha, 2, border_radius=5)
        
        # Mostra asteriscos para a senha
        txt_senha = ("*" * len(input_senha)) + ("|" if cursor_visivel and campo_focado == "SENHA" else "")
        mostrar_texto(txt_senha, CORES['VERDE'], LARGURA/2, 322, 'p')

        # --- MENSAGEM DE ERRO ---
        if mensagem_login:
            mostrar_texto(mensagem_login, (255, 50, 50), LARGURA/2, 380, 'p')

        # Clique com o mouse para trocar de campo
        if clique:
            if rect_nome.collidepoint(mouse_pos): campo_focado = "NOME"
            elif rect_senha.collidepoint(mouse_pos): campo_focado = "SENHA"
        
    elif estado == 'LOGOUT':
        tela.fill(CORES['PRETO']) # Garante a tela preta
        
        # Mensagem de agradecimento
        mostrar_texto("Logout realizado com sucesso!", CORES['VERDE'], LARGURA/2, ALTURA/2 - 20, 'm')
        mostrar_texto(f"Obrigado pelo seu trabalho, {usuario_deslogando}.", CORES['BRANCO'], LARGURA/2, ALTURA/2 + 30, 'p')
        
        # Quando o tempo acabar, volta para o Login
        if agora >= proximo_evento:
            estado = 'LOGIN'
            etapa_login = ""

    elif estado == 'MENU':
        # --- 1. CONFIGURAÇÃO DE COORDENADAS (DEFINIR UMA VEZ SÓ) ---
        margem_x = LARGURA / 2
        
        # Linha 1: Áudio L/R
        btn_L_rect = pygame.Rect(margem_x - 240, 140, 230, 45)
        btn_R_rect = pygame.Rect(margem_x + 10, 140, 230, 45)

        # Linha 2: BIPs (Abaixo da linha divisória)
        btn_go_rect = pygame.Rect(margem_x - 240, 260, 230, 45)
        btn_nogo_rect = pygame.Rect(margem_x + 10, 260, 230, 45)

        # Linha 3: Cores
        btn_cores_rect = pygame.Rect(margem_x - 115, 320, 230, 45) # Centralizado

        # Painel Admin (Canto inferior direito)
        btn_hist_rect = pygame.Rect(LARGURA - 210, 420, 180, 45)
        btn_cad_rect = pygame.Rect(LARGURA - 210, 480, 180, 45)

        # Botão Iniciar (Centro Inferior)
        btn_start_rect = pygame.Rect(margem_x - 150, 480, 300, 70)

        # --- NOVA DEFINIÇÃO: BOTÃO VOLTAR (Canto Inferior Esquerdo) ---
        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        # --- APLICAÇÃO DO HOVER ---
        # A cor muda para um tom avermelhado se o mouse estiver em cima
        cor_voltar = (100, 30, 30) if btn_voltar_rect.collidepoint(mouse_pos) else (60, 60, 60)

        pygame.draw.rect(tela, cor_voltar, btn_voltar_rect, border_radius=10)
        pygame.draw.rect(tela, CORES['CINZA_CLARO'], btn_voltar_rect, 1, border_radius=10)
        mostrar_texto("← SAIR", CORES['BRANCO'], btn_voltar_rect.centerx, btn_voltar_rect.centery, 'p')

        
        # --- 3. DESENHO DA INTERFACE ---
        
        # Cabeçalho
        mostrar_texto("CALIBRAÇÃO DE ESTÍMULOS", CORES['AMARELO'], margem_x, 50, 'g')
        mostrar_texto(f"BEM-VINDO, {usuario_atual}", CORES['BRANCO'], margem_x, 90, 'p')
        mostrar_texto("Complete o preparo antes de iniciar:", CORES['CINZA_CLARO'], margem_x, 120, 'p')

        # Desenho Bloco 1: Áudio
        cor_l = CORES['OK'] if checks.get('som_L') else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_l, btn_L_rect, border_radius=8)
        mostrar_texto("TESTAR ESQUERDO (L)", CORES['BRANCO'], btn_L_rect.centerx, btn_L_rect.centery, 'p')

        cor_r = CORES['OK'] if checks.get('som_R') else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_r, btn_R_rect, border_radius=8)
        mostrar_texto("TESTAR DIREITO (R)", CORES['BRANCO'], btn_R_rect.centerx, btn_R_rect.centery, 'p')

        # Divisor Central
        pygame.draw.line(tela, CORES['CINZA_ESC'], (100, 220), (LARGURA-100, 220), 2)
        mostrar_texto("RECONHECIMENTO DE SINAIS", CORES['AMARELO'], margem_x, 220, 'p')

        # Desenho Bloco 2: BIPs
        cor_go = CORES['OK'] if checks.get('som_go') else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_go, btn_go_rect, border_radius=8)
        mostrar_texto("BIP AGUDO (GO)", CORES['BRANCO'], btn_go_rect.centerx, btn_go_rect.centery, 'p')

        cor_nogo = CORES['OK'] if checks.get('som_nogo') else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_nogo, btn_nogo_rect, border_radius=8)
        mostrar_texto("BIP GRAVE (NOGO)", CORES['BRANCO'], btn_nogo_rect.centerx, btn_nogo_rect.centery, 'p')

        # Desenho Bloco 3: Cores
        cor_cores = CORES['OK'] if checks.get('cores') else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_cores, btn_cores_rect, border_radius=8)
        mostrar_texto("REVISAR CORES", CORES['BRANCO'], btn_cores_rect.centerx, btn_cores_rect.centery, 'p')
        if btn_cores_rect.collidepoint(mouse_pos):      
            # Amostra VERDE (GO) - Posicionada relativa ao botão
            pygame.draw.rect(tela, CORES['VERDE'], (btn_cores_rect.centerx + -110, btn_cores_rect.centery - 10, 20, 20), border_radius=4)
            
            # Amostra VERMELHA (NOGO) - Posicionada relativa ao botão
            pygame.draw.rect(tela, CORES['VERMELHO'], (btn_cores_rect.centerx + 90, btn_cores_rect.centery - 10, 20, 20), border_radius=4)
            
            if clique:
                checks['cores'] = True
        else:
            # Texto centralizado normal quando o mouse não está em cima
            mostrar_texto("REVISAR CORES", CORES['BRANCO'], btn_cores_rect.centerx, btn_cores_rect.centery, 'p')
 
   

        # --- 4. ZONA ADMIN (SÓ SE FOR NÍVEL 1) ---
        if nivel_acesso == 1:
            # Histórico
            pasta_db = obter_caminho_externo()
            existe_db = os.path.exists(os.path.join(pasta_db, "log_foco_detalhado.csv"))
            cor_hist = CORES['AZUL'] if existe_db else (100, 100, 100)
            
            pygame.draw.rect(tela, cor_hist, btn_hist_rect, border_radius=8)
            mostrar_texto("HISTÓRICO GERAL", CORES['BRANCO'], btn_hist_rect.centerx, btn_hist_rect.centery, 'p')
            
            # Novo Operador
            pygame.draw.rect(tela, (200, 100, 0), btn_cad_rect, border_radius=8)
            mostrar_texto("NOVO OPERADOR", CORES['BRANCO'], btn_cad_rect.centerx, btn_cad_rect.centery, 'p')

        # --- 5. BOTÃO INICIAR / BLOQUEADO ---
        pode_iniciar = all(checks.values())
        cor_start = CORES['VERDE'] if pode_iniciar else CORES['CINZA_ESC']
        
        pygame.draw.rect(tela, cor_start, btn_start_rect, border_radius=12)
        if not pode_iniciar:
            pygame.draw.rect(tela, (150, 0, 0), btn_start_rect, 2, border_radius=12)
            mostrar_texto("BLOQUEADO", CORES['BRANCO'], btn_start_rect.centerx, btn_start_rect.centery, 'm')
        else:
            mostrar_texto("INICIAR TESTE", CORES['BRANCO'], btn_start_rect.centerx, btn_start_rect.centery, 'm')

        # 2. BOTÃO DE INICIAR (Separado, para todos os níveis!)
        # Tirei do 'elif' e deixei como um 'if' próprio para garantir a execução
        if btn_start_rect.collidepoint(mouse_pos) and pode_iniciar:
            print("Iniciando o teste...")
            tentativa_atual = 0
            dados_coletados = []
            erros_impulso = 0
            erros_omissao = 0
            lista_estimulos = (['GO']*14 + ['NOGO']*6)
            random.shuffle(lista_estimulos)
            estado = 'ESPERA'
            proximo_evento = time.time() + 1.2

# --- 6. PROCESSAMENTO DOS CLIQUES ---
        if clique:
            # 1. BOTÕES DE CALIBRAÇÃO (Independentes)
            if btn_L_rect.collidepoint(mouse_pos):
                canal = som_go.play()
                if canal: canal.set_volume(1.0, 0.0)
                checks['som_L'] = True
            elif btn_R_rect.collidepoint(mouse_pos):
                canal = som_go.play()
                if canal: canal.set_volume(0.0, 1.0)
                checks['som_R'] = True
            elif btn_go_rect.collidepoint(mouse_pos):
                som_go.play(); checks['som_go'] = True
            elif btn_nogo_rect.collidepoint(mouse_pos):
                som_nogo.play(); checks['som_nogo'] = True
            elif btn_cores_rect.collidepoint(mouse_pos):
                checks['cores'] = True
        
            
            # 3. BOTÕES DE ADMIN (Apenas se for Admin)
            if nivel_acesso == 1:
                if btn_hist_rect.collidepoint(mouse_pos) and existe_db:
                    import dashboard
                    dashboard.gerar_analise()
                elif btn_cad_rect.collidepoint(mouse_pos):
                    cadastrar_novo_operador()    

            if clique and btn_voltar_rect.collidepoint(mouse_pos):
                usuario_deslogando = usuario_atual # Guarda o nome para o agradecimento
                estado = 'LOGOUT'
                proximo_evento = agora + 2 # A tela vai durar 2 segundos
                # Limpa os dados da sessão
                usuario_atual = ""
                input_texto = ""
                for chave in checks: checks[chave] = False        

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
        if not foi_salvo:
            print(f"Salvando os dados de: {usuario_atual}")
            salvar_resultados(dados_coletados,erros_impulso,erros_omissao,usuario_atual)
            foi_salvo = True

        # Indentação corrigida aqui
        tempos_v = [d[1] for d in dados_coletados if d[0] == 'VISUAL']
        tempos_s = [d[1] for d in dados_coletados if d[0] == 'SONORO']
        media_v = sum(tempos_v)/len(tempos_v) if tempos_v else 0
        media_s = sum(tempos_s)/len(tempos_s) if tempos_s else 0
        
        
        # Diagnósticos individuais
        status_v, cor_v = obter_diagnostico(media_v)
        status_s, cor_s = obter_diagnostico(media_s)

        # Diagnóstico Geral (Pelo pior resultado - Conservador)
        pior_media = max(media_v, media_s)
        status_geral, cor_geral = obter_diagnostico(pior_media)

        # --- Interface Refinada ---
        mostrar_texto("DADOS POR MODALIDADE", CORES['AMARELO'], LARGURA/2, 80, 'm')
        
        # Bloco Visual
        pygame.draw.rect(tela, CORES['CINZA_ESC'], (100, 130, 280, 100), border_radius=10)
        mostrar_texto(f"VISUAL: {media_v:.1f} ms", CORES['BRANCO'], 240, 160, 'm')
        mostrar_texto(status_v, cor_v, 240, 200, 'p')

        # Bloco Sonoro
        pygame.draw.rect(tela, CORES['CINZA_ESC'], (420, 130, 280, 100), border_radius=10)
        mostrar_texto(f"SONORO: {media_s:.1f} ms", CORES['BRANCO'], 560, 160, 'm')
        mostrar_texto(status_s, cor_s, 560, 200, 'p')

        # Status Unificado (O veredito do Engenheiro)
        pygame.draw.line(tela, CORES['CINZA_CLARO'], (100, 270), (700, 270), 2)
        mostrar_texto("VEREDITO GERAL:", CORES['BRANCO'], LARGURA/2, 310, 'p')
        mostrar_texto(status_geral, cor_geral, LARGURA/2, 360, 'g')

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
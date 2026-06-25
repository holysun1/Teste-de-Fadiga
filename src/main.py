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
import config
import sys
import matplotlib.pyplot as plt
import bcrypt

RECTS = config.RECTS
TEMAS = config.TEMAS
CORES = config.CORES

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
                f.write("ADMIN,$$2b$12$K89b9hGZ0lY2U37tF1W1WeY7Y0z9zS6rR7xV7vY9yZ9zS6rR7xV7v$$,1\n") 
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
        user_row = df[df['Nome'].str.upper() == nome_busca]      
        
        # 2. Busca o usuário
        
        if not user_row.empty:
            # 1. Checagem de Quantidade (Menos de 4 dígitos)
            if len(input_senha) < 4:
                mensagem_login = "A SENHA DEVE CONTER 4 DÍGITOS!"
            
            hash_armazenado = str(user_row.iloc[0]['senha_hash']).strip()
            senha_correta = bcrypt.checkpw(input_senha.encode('utf-8'),hash_armazenado.encode('utf-8'))

            # 2. Checagem de Validade (Se tem 4, mas está errada)
            if not senha_correta:
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
                    estado = 'MENU'
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

info_tela = pygame.display.Info()
LARGURA = info_tela.current_w
ALTURA = info_tela.current_h

# Abre a tela cheia real
tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)

# AQUI: Você APENAS CHAMA a função para preencher os botões com a tela aberta!
config.inicializar_config(LARGURA, ALTURA)

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
    if media_ms == 0: return "SEM DADOS", TEMAS[tema_atual]['texto']
    if media_ms < 350: return "CONCENTRADO (ELITE)", CORES['VERDE']
    elif 350 <= media_ms < 450: return "ALERTA (NORMAL)", TEMAS[tema_atual]['texto']
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
# 2. Cria a tela usando as dimensões máximas e a flag de Tela Cheia
tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)

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
    pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], (0, 0, LARGURA, 10))
    pygame.draw.rect(tela, CORES['AZUL'], (0, 0, progresso, 10))

def salvar_feedback(nome, sugestao, critica):

    
    pasta_db = obter_caminho_externo()
    filename = os.path.join(pasta_db, "sugestoes_criticas.csv")
    
    try:
        # 1. Verifica se o arquivo é novo ANTES de abrir em modo append ('a')
        arquivo_novo = not os.path.exists(filename)
        
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Se o campo nome for deixado em branco ou vazio, força o padrão "Anonimo"
        nome_final = nome.strip() if nome.strip() != "" else "Anonimo"
        
        # 2. Abrimos com 'utf-8-sig' para que o Excel e o Pandas leiam os acentos perfeitamente
        with open(filename, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            
            if arquivo_novo:
                # Se o arquivo acabou de ser criado, adiciona o cabeçalho primeiro
                writer.writerow(["Data/Hora", "Nome", "Sugestao", "Critica/Reclamacao"])
                print(f"[DEBUG] Novo arquivo criado com cabeçalhos em: {filename}")
            
            # Escreve a nova linha com o feedback recebido
            writer.writerow([data_atual, nome_final, sugestao.strip(), critica.strip()])
            
        print(f"[DEBUG] Feedback gravado com sucesso para o operador: {nome_final}")
        
    except Exception as e:
        print(f"Erro ao salvar o arquivo de sugestoes: {e}")



fonte_p = pygame.font.SysFont("Arial", 18)
fonte_sub_p = pygame.font.SysFont("Arial", 16, italic=True)
fonte_btn_p = pygame.font.SysFont("Arial", 18, bold=True)

# --- VARIÁVEIS DE CONTROLE DO FORMULÁRIO ---
texto_nome = "Anonimo"
texto_sugestao = ""
texto_critica = ""
campo_ativo = None  # Pode ser: "nome", "sugestao", "critica" ou None


clock = pygame.time.Clock()
pygame.key.set_repeat(300,50)
foi_salvo = False
etapa_login ="NOME"
input_senha = ""
tema_atual = 'escuro'

btn_fechar_rect = pygame.Rect(25,ALTURA-70,150,45)
# --- Loop Principal ---
while True:
    mouse_pos = pygame.mouse.get_pos()
    mouse_sobre_btn = False

     
    for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ==========================================
            # 1. LÓGICA DE CLIQUES DO MOUSE
            # ==========================================
            if event.type == pygame.MOUSEBUTTONUP:
                clique = True 
                
                if estado == 'HOME' and btn_fechar_rect.collidepoint(mouse_pos): #CORRIGIDO BUG DE HIERARQUIA ( CLIQUE FANTASMA)
                    pygame.quit()
                    sys.exit()

                # --- ACIONAR PAUSA (Se estiver em qualquer fase do teste) ---
                elif estado in ['ESPERA', 'ESTIMULO', 'FEEDBACK']:
                    if RECTS['comum']['btn_x_fec_rect'].collidepoint(mouse_pos):
                        estado_anterior = estado # Salva onde parou
                        estado = 'PAUSA'
                
                    elif estado == 'ESTIMULO':
                        if subtipo_atual == 'GO':
                            latencia = (time.time() - momento_estimulo) * 1000
                            if latencia > 150: # Evita cliques antecipados/falsos
                                dados_coletados.append((tipo_atual, latencia))
                                estado = 'FEEDBACK'
                                proximo_evento = time.time() + 0.6
                        else:
                            # Se clicou no NOGO (estímulo vermelho), conta erro de impulso
                            erros_impulso += 1
                            estado = 'FEEDBACK'
                            proximo_evento = time.time() + 0.6


                # --- LÓGICA DENTRO DA PAUSA ---
                elif estado == 'PAUSA':
                    if RECTS['modal_pausa']['btn_continuar'].collidepoint(mouse_pos):
                        # Em vez de voltar direto, inicia a contagem
                        estado = 'CONTAGEM'
                        tempo_inicio_contagem = time.time()
                    
                    elif RECTS['modal_pausa']['btn_reiniciar'].collidepoint(mouse_pos):
                        # Reseta tudo e começa do zero
                        dados_coletados.clear()
                        erros_impulso = 0; erros_omissao = 0; tentativa_atual = 0
                        estado = 'CONTAGEM'
                        tempo_inicio_contagem = time.time()
                    
                    elif RECTS['modal_pausa']['btn_fechar_teste'].collidepoint(mouse_pos):
                        # Cancela o teste e volta pro Menu sem salvar nada
                        dados_coletados.clear()
                        checks['som_go'] = False
                        checks['som_nogo'] = False
                        checks['cores'] = False
                        estado = 'HOME'
                        

                    # Se os 3 forem True, o clique no Avançar funciona
                    elif all(checks.values()) and RECTS['teste_operador']['btn_start_rect'].collidepoint(mouse_pos):
                        estado = 'PERGUNTA_SONO'
                        input_sono = ""

                elif estado == 'HOME':
                    if RECTS['home']['btn_teste_h'].collidepoint(mouse_pos):
                        destino_pos_login = 'TESTE' # Ele quer fazer o teste
                        estado = 'LOGIN'           # Mas mandamos para o login primeiro
                    
                    elif RECTS['home']['btn_admin_h'].collidepoint(mouse_pos):
                        destino_pos_login = 'MENU' # Ele quer ir pro painel
                        estado = 'LOGIN'
                        
                    elif RECTS['home']['rect_pesquisa'].collidepoint(mouse_pos):
                        estado = 'PESQUISA' # Esse vai direto (Anônimo!)
                        campo_ativo = None
                    elif RECTS['home']['rect_reclamacao'].collidepoint(mouse_pos):
                        estado = 'RECLAMACAO' # Esse vai direto (Anônimo!)
                    
                    elif RECTS['home']['btn_config_h'].collidepoint(mouse_pos):
                        estado = 'CONFIG'

                elif estado == 'PESQUISA':
                    # Gerenciar focos de clique
                    if RECTS['pesquisa_sugestao']['rect_nome_p'].collidepoint(mouse_pos):
                        campo_ativo = "nome"
                        if texto_nome == "Anonimo": texto_nome = "" # Limpa para o usuário digitar
                    elif RECTS['pesquisa_sugestao']['rect_sugestao_p'].collidepoint(mouse_pos):
                        campo_ativo = "sugestao"
                    elif RECTS['pesquisa_sugestao']['rect_critica_p'].collidepoint(mouse_pos):
                        campo_ativo = "critica"
                    elif RECTS['pesquisa_sugestao']['rect_enviar_p'].collidepoint(mouse_pos):
                        # Ação do Botão Enviar
                        salvar_feedback(texto_nome, texto_sugestao, texto_critica)
                        # Reseta o formulário e volta para a tela inicial do jogo
                        texto_nome = "Anonimo"
                        texto_sugestao = ""
                        texto_critica = ""
                        campo_ativo = None
                        estado = 'HOME' # Ou o nome exato do seu estado da tela inicial
                    elif RECTS['comum']['btn_voltar_rect'].collidepoint(mouse_pos):
                        estado = 'HOME'  # Cancela a pesquisa e volta para a HOME
                        campo_ativo = None
                        if texto_nome.strip() == "": texto_nome = "Anonimo"
                    else:
                        campo_ativo = None
                        if texto_nome.strip() == "": texto_nome = "Anonimo"
                elif estado == 'CONFIG':
                    if RECTS['comum']['btn_voltar_rect'].collidepoint(mouse_pos):
                        estado = 'HOME'
                    elif RECTS['configuracoes']['btn_tema_rect'].collidepoint(mouse_pos):
                        tema_atual = 'claro' if tema_atual == 'escuro' else 'escuro'
                     
                # --- CLIQUES NA TELA DE MENU (ADMIN/OPERADOR) ---
                elif estado == 'MENU':
                     # Só verifica o botão de sair se estiver no MENU
                    # Botão Sair Comum a todos
                    if RECTS['comum']['btn_voltar_rect'].collidepoint(mouse_pos):
                        #Limpeza de segurança
                        usuario_atual = ""
                        input_texto = "" # Limpa o CPF digitado
                        input_senha = "" # Limpa a senha
                        nivel_acesso = -1 # Reseta o nível
                        for chave in checks: checks[chave] = False
                        estado = 'LOGIN' 
                    
                    
                    # Quando o login der sucesso e for nível 0
                    elif nivel_acesso == 0:
                        if RECTS['teste_operador']['btn_cores_rect'].collidepoint(mouse_pos):
                            checks['cores'] = True
                        if RECTS['teste_operador']['btn_go_rect'].collidepoint(mouse_pos):
                            som_go.play(); checks['som_go'] = True
                        if RECTS['teste_operador']['btn_nogo_rect'].collidepoint(mouse_pos):
                            som_nogo.play(); checks['som_nogo'] = True      

                        elif all(checks.values()) and RECTS['teste_operador']['btn_start_rect'].collidepoint(mouse_pos):
                            estado = 'PERGUNTA_SONO'
                            input_sono = ""                    
                        # Cliques Exclusivos do ADMIN (Nível 1)
                    elif nivel_acesso == 1:

                        if RECTS['cadastro']['btn_hist_rect'].collidepoint(mouse_pos) and existe_db:
                            import dashboard
                            dashboard.gerar_analise()
                        elif RECTS['cadastro']['btn_cad_rect'].collidepoint(mouse_pos):
                            estado = 'CADASTRO' 
                            input_nome_cad = ""; input_cpf_cad = ""; mensagem_feedback = ""                
                        elif RECTS['cadastro']['btn_config_rect'].collidepoint(mouse_pos):
                            estado = 'CONFIG'  
                        elif RECTS['cadastro']['btn_grafico_rect'].collidepoint(mouse_pos) and existe_db:
                                gerar_grafico_fadiga_sono()
                        

                            # --- CLIQUES NA TELA DE CADASTRO ---
                elif estado == 'CADASTRO':
                    # Ação de Voltar (Aqui ele não vai mais conflitar com o Sair)
                    if RECTS['comum']['btn_voltar_rect'].collidepoint(mouse_pos):
                        estado = 'MENU'
                        input_nome_cad = ""; input_cpf_cad = ""; mensagem_feedback = ""
                    elif RECTS['cadastro']['rect_nome'].collidepoint(mouse_pos): 
                        campo_focado = "NOME"
                    elif RECTS['cadastro']['rect_cpf'].collidepoint(mouse_pos): 
                        campo_focado = "CPF"

                    # --- NOVOS CLIQUES: MENUS CÍCLICOS ---
                    elif RECTS['cadastro']['rect_setor'].collidepoint(mouse_pos): 
                        # Pula para o próximo setor da lista. Se chegar no fim, volta pro começo (0)
                        idx_setor = (idx_setor + 1) % len(lista_setores)
                        campo_focado = "" # Tira o cursor piscando do Nome/CPF
                        
                    elif RECTS['cadastro']['rect_nivel'].collidepoint(mouse_pos): 
                        # Pula entre 0 - Operador e 1 - Admin
                        idx_nivel = (idx_nivel + 1) % len(lista_niveis)
                        campo_focado = "" # Tira o cursor piscando do Nome/CPF
                        
                    # Ação de Salvar
                    elif RECTS['cadastro']['btn_salvar_cad'].collidepoint(mouse_pos):
                        if len(input_cpf_cad) == 11 and len(input_nome_cad) > 3:
                            try:
                                caminho_csv = os.path.join(obter_caminho_externo(), "..\operadores.csv")
                                df = pd.read_csv(caminho_csv, dtype={'CPF': str})
                                if input_cpf_cad in df['CPF'].values:
                                    mensagem_feedback = "ERRO: CPF JÁ CADASTRADO!"; cor_feedback = (200, 50, 50)
                                else:
                                    #GERAR HASH DA SENHA PADRÃO
                                    senha_padrao = input_cpf_cad[:4]
                                    senha_hash = bcrypt.hashpw(senha_padrao.encode('utf-8'), bcrypt.gensalt().decode('utf-8'))
                                    with open(caminho_csv, 'a', encoding='utf-8') as f:
                                        f.write(f"{input_nome_cad},{input_cpf_cad},0,{senha_hash}\n")
                                    mensagem_feedback = "CADASTRADO COM SUCESSO!"; cor_feedback = (50, 180, 50)
                                    input_nome_cad = ""; input_cpf_cad = ""
                            except Exception as e:
                                mensagem_feedback = "ERRO AO ACESSAR DB"; cor_feedback = (200, 50, 50)
                        else:
                            mensagem_feedback = "DADOS INVÁLIDOS!"; cor_feedback = (200, 50, 50)

                elif estado == 'LOGIN':
                    # 1. Clique no Botão ENTRAR
                    if RECTS['login']['btn_entrar_rect'].collidepoint(mouse_pos):
                        validar_login()
                    if RECTS['comum']['btn_voltar_rect'].collidepoint(mouse_pos):
                        estado = 'HOME'
                        input_texto = ""; input_senha = ""; mensagem_login = ""

                    if RECTS['login']['rect_nome'].collidepoint(mouse_pos): campo_focado = "NOME"

                    if RECTS['login']['rect_senha'].collidepoint(mouse_pos): campo_focado = "SENHA"

            
                elif estado == 'FIM':
                    if RECTS['home']['btn_finalizar_rect'].collidepoint(mouse_pos):
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
        cores_tema = TEMAS[tema_atual]
        tela.fill(cores_tema['fundo']) 
        # 3. RELÓGIO (Mantém dinâmico)
        hora_atual = datetime.now().strftime("%H:%M:%S")
        mostrar_texto(hora_atual, cores_tema['texto'], 100, 50, 'm')
        
        # 4. LOGO EMPRESA
        pygame.draw.rect(tela, cores_tema['caixas'], RECTS['home']['rect_logo'], 2)
        mostrar_texto("LOGO EMPRESA", cores_tema['texto'], RECTS['home']['rect_logo'].centerx,RECTS['home']['rect_logo'].centery, 'p')
        
        # 5. DESENHO DOS BOTÕES PRINCIPAIS
        desenhar_botao(RECTS['home']['btn_teste_h'],cores_tema['caixas'], (0, 100, 200), "INICIAR TESTE", cores_tema['texto'])
        desenhar_botao(RECTS['home']['btn_admin_h'], cores_tema['caixas'], (100, 100, 100), "PAINEL ADM", cores_tema['texto'])
        desenhar_botao(RECTS['home']['btn_config_h'], cores_tema['caixas'], (100, 100, 100), "CONFIGURAÇÕES", cores_tema['texto'])

        # 6. ÍCONES DOS CANTOS (Utilizando os centros dos Rects do config)
        # Superior Direito: Sugestão/Pesquisa
        pygame.draw.circle(tela, (255, 200, 0), RECTS['home']['rect_pesquisa'].center, 40)
        mostrar_texto("SUGESTÃO", cores_tema['texto'], RECTS['home']['rect_pesquisa'].centerx, RECTS['home']['rect_pesquisa'].centery + 50, 'p')
        
        # Inferior Direito: Ocorrido/Reclamação
        pygame.draw.circle(tela, (200, 50, 50), RECTS['home']['rect_reclamacao'].center, 40)
        mostrar_texto("OCORRIDO", cores_tema['texto'], RECTS['home']['rect_reclamacao'].centerx, RECTS['home']['rect_reclamacao'].centery + 50, 'p')

        # 7. BOTÃO SAIR
        pygame.draw.rect(tela, cores_tema['caixas'], RECTS['home']['btn_finalizar_rect'], border_radius=5)
        mostrar_texto("SAIR", cores_tema['texto'], RECTS['home']['btn_finalizar_rect'].centerx, RECTS['home']['btn_finalizar_rect'].centery)

        # --- Lógica de Estados ---
    elif estado == 'LOGIN':
            cores_tema = TEMAS[tema_atual]
            tela.fill(cores_tema['fundo'])
            
            usuario_atual = ""
            proximo_evento = 0
            
            # Título centralizado no topo da tela dinamicamente
            mostrar_texto("SISTEMA DE CONTROLE DE FADIGA", CORES['AMARELO'], LARGURA/2, 100, 'm')

            # --- CAMPO NOME ---
            rect_nome = RECTS['login']['rect_nome']
            # Texto posicionado exatamente 20 pixels ACIMA da caixa de texto correspondente
            mostrar_texto("OPERADOR:", cores_tema['texto'], rect_nome.centerx, rect_nome.top - 20, 'p')
            cor_borda_nome = CORES['AZUL'] if campo_focado == "NOME" else cores_tema['caixas']
            
            pygame.draw.rect(tela, (30, 30, 30), rect_nome, border_radius=5)
            pygame.draw.rect(tela, cor_borda_nome, rect_nome, 2, border_radius=5)
            
            txt_nome = input_texto + ("|" if cursor_visivel and campo_focado == "NOME" else "")
            # Texto digitado alinhado perfeitamente no centro geométrico da caixa
            mostrar_texto(txt_nome, CORES['BRANCO'], rect_nome.centerx, rect_nome.centery, 'p')

            # --- CAMPO SENHA ---
            rect_senha = RECTS['login']['rect_senha']
            # Texto posicionado exatamente 20 pixels ACIMA da caixa de senha
            mostrar_texto("SENHA:", cores_tema['texto'], rect_senha.centerx, rect_senha.top - 20, 'p')
            cor_borda_senha = CORES['AZUL'] if campo_focado == "SENHA" else cores_tema['caixas']
            
            pygame.draw.rect(tela, (30, 30, 30), rect_senha, border_radius=5)
            pygame.draw.rect(tela, cor_borda_senha, rect_senha, 2, border_radius=5)
            
            txt_senha = ("*" * len(input_senha)) + ("|" if cursor_visivel and campo_focado == "SENHA" else "")
            # Texto da senha centralizado no meio da caixa
            mostrar_texto(txt_senha, CORES['BRANCO'], rect_senha.centerx, rect_senha.centery, 'p')

            # --- DESENHO DOS BOTÕES (Usando os rects calculados do config) ---
            desenhar_botao(RECTS['login']['btn_entrar_rect'], (100, 100, 100), CORES['VERDE'], "ENTRAR", cores_tema['texto'], 'p')
            desenhar_botao(RECTS['comum']['btn_voltar_rect'], (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])

            # --- MENSAGEM DE ERRO ---
            if mensagem_login:
                # Posiciona a mensagem de erro logo abaixo do botão de entrar
                btn_entrar = RECTS['login']['btn_entrar_rect']
                mostrar_texto(mensagem_login, (255, 50, 50), btn_entrar.centerx, btn_entrar.bottom + 30, 'p')
    elif estado == 'CONTAGEM':
        cores_tema = TEMAS[tema_atual]
        tela.fill(cores_tema['fundo'])
        
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
        cores_tema = TEMAS[tema_atual]
        tela.fill(CORES['FUNDO']) # Garante a tela preta
        
        # Mensagem de agradecimento
        mostrar_texto("Logout realizado com sucesso!", CORES['BRANCO'], LARGURA/2, ALTURA/2 - 20, 'm')
        mostrar_texto(f"Obrigado pelo seu trabalho, {usuario_deslogando}.", TEMAS[tema_atual]['texto'], LARGURA/2, ALTURA/2 + 30, 'p')
        
        # Quando o tempo acabar, volta para o Login
        if time.time() >= proximo_evento:
            estado = 'LOGIN'
            etapa_login = ""

    elif estado == 'PAUSA':
        # 1. Escurece o fundo (Efeito de sobreposição)
        superficie_overlay = pygame.Surface((LARGURA, ALTURA))
        superficie_overlay.set_alpha(150) # Transparência
        superficie_overlay.fill((0, 0, 0))
        tela.blit(superficie_overlay, (0,0))

        # 2. Janela Modal (Estilo W98)
        pygame.draw.rect(tela, (192, 192, 192), RECTS['modal_pausa']['modal_rect'])
        pygame.draw.rect(tela, (255, 255, 255), RECTS['modal_pausa']['modal_rect'], 2) # Brilho
        # Barra de título da modal (Azul clássico)
        barra_titulo = pygame.Rect(RECTS['modal_pausa']['modal_rect'].x, RECTS['modal_pausa']['modal_rect'].y, RECTS['modal_pausa']['modal_rect'].width, 35)
        pygame.draw.rect(tela, (0, 0, 128), barra_titulo)
        mostrar_texto("TESTE INTERROMPIDO", (255, 255, 255), RECTS['modal_pausa']['modal_rect'].centerx, RECTS['modal_pausa']['modal_rect'].y + 17, 'p')

        # 3. Botões
        desenhar_botao(RECTS['modal_pausa']['btn_continuar'], (192, 192, 192), (210, 210, 210), "CONTINUAR", (0,0,0))
        desenhar_botao(RECTS['modal_pausa']['btn_reiniciar'], (192, 192, 192), (210, 210, 210), "REINICIAR", (0,0,0))
        desenhar_botao(RECTS['modal_pausa']['btn_fechar_teste'], (150, 50, 50), (200, 50, 50), "CANCELAR E SAIR", (255,255,255))


    elif estado == 'CADASTRO':
        cores_tema = TEMAS[tema_atual]
        tela.fill(cores_tema['fundo'])
        
        mostrar_texto("NOVO CADASTRO DE OPERADOR", CORES['AZUL'], LARGURA/2, 100, 'g')

       # --- NOME ---
        # Título agora centralizado perfeitamente com a caixa (centerx)
        mostrar_texto("NOME COMPLETO:", TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_nome'].centerx, RECTS['cadastro']['rect_nome'].y - 20, 'p')
        cor_b_nome = CORES['AZUL'] if campo_focado == "NOME" else CORES['CINZA_ESC']
        pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], RECTS['cadastro']['rect_nome'], border_radius=8)
        pygame.draw.rect(tela, cor_b_nome, RECTS['cadastro']['rect_nome'], 2, border_radius=8)
        cursor_n = "|" if campo_focado == "NOME" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_nome_cad + cursor_n, TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_nome'].centerx, RECTS['cadastro']['rect_nome'].centery, 'm')

        # --- CPF ---
        mostrar_texto("CPF (APENAS NÚMEROS):", TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_cpf'].centerx, RECTS['cadastro']['rect_cpf'].y - 20, 'p')
        cor_b_cpf = CORES['AZUL'] if campo_focado == "CPF" else CORES['CINZA_ESC']
        pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], RECTS['cadastro']['rect_cpf'], border_radius=8)
        pygame.draw.rect(tela, cor_b_cpf, RECTS['cadastro']['rect_cpf'], 2, border_radius=8)
        cursor_c = "|" if campo_focado == "CPF" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_cpf_cad + cursor_c, TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_cpf'].centerx, RECTS['cadastro']['rect_cpf'].centery, 'm')

        # --- SETOR (Menu Cíclico) ---
        mostrar_texto("DEPARTAMENTO:", TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_setor'].centerx, RECTS['cadastro']['rect_setor'].y - 20, 'p')
        texto_setor_atual = f"{lista_setores[idx_setor]} "
        desenhar_botao(RECTS['cadastro']['rect_setor'], TEMAS[tema_atual]['caixas'], (100, 100, 120), texto_setor_atual, TEMAS[tema_atual]['texto'], 'm')
        # DESENHA A BORDA FINA POR CIMA (Espessura 2)
        pygame.draw.rect(tela, CORES['CINZA_ESC'], RECTS['cadastro']['rect_setor'], 2, border_radius=8)

        # --- NÍVEL (Menu Cíclico) ---
        mostrar_texto("NÍVEL DE ACESSO:", TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_nivel'].centerx, RECTS['cadastro']['rect_nivel'].y - 20, 'p')
        texto_nivel_atual = f"{lista_niveis[idx_nivel]}  "
        desenhar_botao(RECTS['cadastro']['rect_nivel'], TEMAS[tema_atual]['caixas'], (100, 100, 120), texto_nivel_atual, TEMAS[tema_atual]['texto'], 'm')
        pygame.draw.rect(tela, CORES['CINZA_ESC'], RECTS['cadastro']['rect_nivel'], 2, border_radius=8)

        # ==========================================
        # 3. BOTÕES DE AÇÃO E FEEDBACK
        # ==========================================
        desenhar_botao(RECTS['cadastro']['btn_salvar_cad'], (0, 150, 0), (0, 180, 0), "SALVAR NOVO USUÁRIO", CORES['BRANCO'])
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])

        # Renderização do Texto Digitado + Cursor piscando
        cursor_n = "|" if campo_focado == "NOME" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_nome_cad + cursor_n, TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_nome'].centerx, RECTS['cadastro']['rect_nome'].centery, 'm')

        cursor_c = "|" if campo_focado == "CPF" and time.time() % 1 > 0.5 else ""
        mostrar_texto(input_cpf_cad + cursor_c, TEMAS[tema_atual]['texto'], RECTS['cadastro']['rect_cpf'].centerx, RECTS['cadastro']['rect_cpf'].centery, 'm')

        desenhar_botao(RECTS['cadastro']['btn_salvar_cad'], (0, 150, 0), (0, 180, 0), "SALVAR", CORES['BRANCO'])

        btn_voltar_rect = pygame.Rect(30, ALTURA - 75, 150, 45)
        desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])

        # Mensagem de Feedback (Erro ou Sucesso)
        if mensagem_feedback:
            mostrar_texto(mensagem_feedback, cor_feedback, LARGURA/2, 540, 'p')

    elif estado == 'CARREGANDO':
            cores_tema = TEMAS[tema_atual]
            tela.fill(CORES['FUNDO'])
            mostrar_texto("AUTENTICANDO...", CORES['PRIMARIA'], LARGURA/2, ALTURA/2, 'g')
            
            # O cronômetro acabou?
            if time.time() > proximo_evento:
                if destino_pos_login == 'TESTE':
                    estado = 'MENU'
                    if nivel_acesso == 1:
                        estado = 'MENU'
                    else:
                        # Se um espertinho tentar entrar no ADM sendo nível 0
                        estado = 'HOME' 
                        mensagem_login = "ACESSO NEGADO"

    elif estado == 'PESQUISA':
        cores_tema = TEMAS[tema_atual]
        tela.fill(cores_tema['fundo']) 
        
        # Textos de Instrução adaptados ao tema atual
        mostrar_texto("Sugestões e críticas são feitas anonimamente.", TEMAS[tema_atual]['texto'], 100 + 180, 60, 'p')
        mostrar_texto("Caso queira se identificar, preencha o campo Nome:", CORES['TEXTO_DARK'] if tema_escuro else CORES['CINZA_CLARO'], 100 + 200, 90, 'p')
        
        # Labels alinhados com o tema
        mostrar_texto("Nome:", TEMAS[tema_atual]['texto'], 130, 155, 'p')
        mostrar_texto("Sugestão:", TEMAS[tema_atual]['texto'], 140, 245, 'p')
        mostrar_texto("Crítica / Reclamação:", TEMAS[tema_atual]['texto'], 185, 355, 'p')
        
        # Caixas de Input usando a cor padrão de caixas (TEMAS[tema_atual]['caixas'])
        pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], RECTS['pesquisa_sugestao']['rect_nome_p'], border_radius=4)
        pygame.draw.rect(tela, CORES['AZUL'] if campo_ativo == "nome" else CORES['CINZA_ESC'], RECTS['pesquisa_sugestao']['rect_nome_p'], 2, border_radius=4)
        
        pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], RECTS['pesquisa_sugestao']['rect_sugestao_p'], border_radius=4)
        pygame.draw.rect(tela, CORES['AZUL'] if campo_ativo == "sugestao" else CORES['CINZA_ESC'], RECTS['pesquisa_sugestao']['rect_sugestao_p'], 2, border_radius=4)
        
        pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], RECTS['pesquisa_sugestao']['rect_critica_p'], border_radius=4)
        pygame.draw.rect(tela, CORES['AZUL'] if campo_ativo == "critica" else CORES['CINZA_ESC'], RECTS['pesquisa_sugestao']['rect_critica_p'], 2, border_radius=4)
        
        # Letras internas dos inputs mudam de cor para dar contraste com o fundo da caixa
        cor_letra_input = CORES['BRANCO'] if tema_escuro else CORES['TEXTO']
        
        cursor_nome = "|" if campo_ativo == "nome" and time.time() % 1 > 0.5 else ""
        cursor_sug = "|" if campo_ativo == "sugestao" and time.time() % 1 > 0.5 else ""
        cursor_crit = "|" if campo_ativo == "critica" and time.time() % 1 > 0.5 else ""

        # Usando a função mostrar_texto padrão para manter consistência tipográfica
        mostrar_texto(texto_nome + cursor_nome, cor_letra_input, RECTS['pesquisa_sugestao']['rect_nome_p'].x + 80, RECTS['pesquisa_sugestao']['rect_nome_p'].centery, 'p')
        mostrar_texto(texto_sugestao + cursor_sug, cor_letra_input, RECTS['pesquisa_sugestao']['rect_sugestao_p'].x + 120, RECTS['pesquisa_sugestao']['rect_sugestao_p'].centery, 'p')
        mostrar_texto(texto_critica + cursor_crit, cor_letra_input, RECTS['pesquisa_sugestao']['rect_critica_p'].x + 120, RECTS['pesquisa_sugestao']['rect_critica_p'].centery, 'p')
        
        # Botão Enviar com visual padrão do sistema
        desenhar_botao(RECTS['pesquisa_sugestao']['rect_enviar_p'], CORES['PRIMARIA'], CORES['AZUL'], "ENVIAR", CORES['BRANCO'], 'p')
        desenhar_botao(RECTS['comum']['btn_voltar_rect'], (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])
    elif estado == 'MENU':
        cores_tema = TEMAS[tema_atual]
        tela.fill(CORES['FUNDO'])

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
            mostrar_texto(f"Operador Logado: {usuario_atual}", TEMAS[tema_atual]['texto'], margem_x, 90, 'p')
            mostrar_texto("Complete o preparo antes de iniciar:", CORES['CINZA_CLARO'], margem_x, 140, 'p')
        
      
            # 2. Desenho do Bloco 1: BIPs
            cor_go = CORES['OK'] if checks.get('som_go') else TEMAS[tema_atual]['caixas']
            pygame.draw.rect(tela, cor_go, RECTS['teste_operador']['btn_go_rect'], border_radius=8)
            mostrar_texto("BIP AGUDO (GO)", TEMAS[tema_atual]['texto'], RECTS['teste_operador']['btn_go_rect'].centerx, RECTS['teste_operador']['btn_go_rect'].centery, 'p')

            cor_nogo = CORES['OK'] if checks.get('som_nogo') else TEMAS[tema_atual]['caixas']
            pygame.draw.rect(tela, cor_nogo, RECTS['teste_operador']['btn_nogo_rect'], border_radius=8)
            mostrar_texto("BIP GRAVE (NOGO)", TEMAS[tema_atual]['texto'], RECTS['teste_operador']['btn_nogo_rect'].centerx, RECTS['teste_operador']['btn_nogo_rect'].centery, 'p')

            # 3. Desenho do Bloco 2: Cores
            cor_cores = CORES['OK'] if checks.get('cores') else TEMAS[tema_atual]['caixas']
            pygame.draw.rect(tela, cor_cores, RECTS['teste_operador']['btn_cores_rect'], border_radius=8)
            
            if RECTS['teste_operador']['btn_cores_rect'].collidepoint(mouse_pos):      
                pygame.draw.rect(tela, CORES['VERDE'], (RECTS['teste_operador']['btn_cores_rect'].centerx - 110, RECTS['teste_operador']['btn_cores_rect'].centery - 10, 20, 20), border_radius=4)
                pygame.draw.rect(tela, CORES['VERMELHO'], (RECTS['teste_operador']['btn_cores_rect'].centerx + 90, RECTS['teste_operador']['btn_cores_rect'].centery - 10, 20, 20), border_radius=4)
                mostrar_texto("REVISAR CORES", TEMAS[tema_atual]['texto'], RECTS['teste_operador']['btn_cores_rect'].centerx, RECTS['teste_operador']['btn_cores_rect'].centery, 'p')
            else:
                mostrar_texto("REVISAR CORES", TEMAS[tema_atual]['texto'], RECTS['teste_operador']['btn_cores_rect'].centerx, RECTS['teste_operador']['btn_cores_rect'].centery, 'p')

            # 4. Desenho do Botão Iniciar
            pode_iniciar = all(checks.values())
            cor_start = CORES['VERDE'] if pode_iniciar else TEMAS[tema_atual]['caixas']
            
            pygame.draw.rect(tela, cor_start, RECTS['teste_operador']['btn_start_rect'], border_radius=12)
            if not pode_iniciar:
                pygame.draw.rect(tela, (150, 0, 0), RECTS['teste_operador']['btn_start_rect'], 2, border_radius=12)
                mostrar_texto("BLOQUEADO", TEMAS[tema_atual]['texto'], RECTS['teste_operador']['btn_start_rect'].centerx, RECTS['teste_operador']['btn_start_rect'].centery, 'm')
            else:
                mostrar_texto("INICIAR TESTE", TEMAS[tema_atual]['texto'], RECTS['teste_operador']['btn_start_rect'].centerx, RECTS['teste_operador']['btn_start_rect'].centery, 'm')

            #5. Desenho botão voltar
            desenhar_botao(btn_voltar_rect, (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])


        # =========================================================
        # SALA 2 : PAINEL DE GESTÃO - ADMIN (NÍVEL 1)
        # =========================================================
        elif nivel_acesso == 1:
            cores_tema = TEMAS[tema_atual]
            tela.fill(cores_tema['fundo'])

            mostrar_texto("PAINEL DE GESTÃO", CORES['AZUL'], margem_x, 80, 'g')
            mostrar_texto(f"Gestor Logado: {usuario_atual}", TEMAS[tema_atual]['texto'], margem_x, 130, 'm')

            # 2. Verifica banco de dados
            pasta_db = obter_caminho_externo()
            existe_db = os.path.exists(os.path.join(pasta_db, "log_foco_detalhado.csv"))
            
            # Botão 1: Histórico
            if existe_db:
                desenhar_botao(RECTS['cadastro']['btn_hist_rect'], CORES['AZUL'], (0, 120, 200), "HISTÓRICO", CORES['BRANCO'])
            else:
                # Botão cinza/desabilitado se não tem banco de dados
                desenhar_botao(RECTS['cadastro']['btn_hist_rect'], CORES['CINZA_ESC'], CORES['CINZA_ESC'], "HISTÓRICO VAZIO", CORES['CINZA_CLARO'])
            
            # Botão 2: Cadastro
            desenhar_botao(RECTS['cadastro']['btn_cad_rect'], (200, 100, 0), (230, 120, 0), "CADASTRO", CORES['BRANCO'])

            # Botão 3: Gráfico Fadiga x Sono
            if existe_db:
                desenhar_botao(RECTS['cadastro']['btn_grafico_rect'], (100, 0, 120), (130, 0, 150), "GRÁFICO", CORES['BRANCO'])
            else:
                desenhar_botao(RECTS['cadastro']['btn_grafico_rect'], CORES['CINZA_ESC'], CORES['CINZA_ESC'], "GRÁFICO INDISPONÍVEL", CORES['CINZA_CLARO'])

            # Botão 4: Configurações
            desenhar_botao(RECTS['cadastro']['btn_config_rect'], (80, 80, 80), (130, 100, 100), "CONFIGURAÇÕES", CORES['BRANCO'])


    elif estado == 'PERGUNTA_SONO':
        cores_tema = TEMAS[tema_atual]
        tela.fill(CORES['FUNDO'])

        
        mostrar_texto("PREPARAÇÃO PARA O TESTE", CORES['AMARELO'], LARGURA/2, 100, 'g')
        mostrar_texto("Quantas horas você dormiu na última noite?", TEMAS[tema_atual]['texto'], LARGURA/2, 200, 'm')
        
        # Desenha a caixa de texto
        caixa_rect = pygame.Rect(LARGURA/2 - 60, 260, 120, 60)
        pygame.draw.rect(tela, TEMAS[tema_atual]['caixas'], caixa_rect, border_radius=10)
        pygame.draw.rect(tela, CORES['AZUL'], caixa_rect, 2, border_radius=10)
        
        # Efeito de cursor piscando na cor certa dependendo do tema
        cor_input = CORES['BRANCO'] if tema_escuro else (20, 20, 20)
        texto_exibicao = input_sono + "|" if time.time() % 1 > 0.5 else input_sono
        mostrar_texto(texto_exibicao, cor_input, caixa_rect.centerx, caixa_rect.centery, 'g')
        
        mostrar_texto("Digite o valor (ex: 7 ou 7.5) e pressione ENTER", CORES['CINZA_CLARO'], LARGURA/2, 400, 'p')
            
    # TELA DE CONFIGURAÇÕES
    # =========================================================
    elif estado == 'CONFIG':
        cores_tema = TEMAS[tema_atual]
        tela.fill(cores_tema['fundo'])
        
        # 2. Textos do Cabeçalho centralizados
        mostrar_texto("CONFIGURAÇÕES DO SISTEMA", CORES['AZUL'], LARGURA / 2, 80, 'g')
        mostrar_texto("Ajuste as preferências visuais da interface", cores_tema['caixas'], LARGURA / 2, 130, 'p')

        # 4. Definição dinâmica do visual do botão de tema
        if tema_atual == 'escuro':
            cor_tema_btn = (50, 50, 50)
            cor_hover_btn = (80, 80, 80)
            texto_tema = "TEMA ATUAL: ESCURO 🌙"
            cor_texto_tema = CORES['BRANCO']
        else:
            cor_tema_btn = (200, 210, 220)
            cor_hover_btn = (220, 230, 240)
            texto_tema = "TEMA ATUAL: CLARO ☀️"
            cor_texto_tema = (30, 30, 30)

        # Efeito visual de hover (passar o mouse por cima)
        cor_final_btn = cor_hover_btn if RECTS['configuracoes']['btn_tema_rect'].collidepoint(mouse_pos) else cor_tema_btn

        # 5. Desenho dos Botões usando a Função Mestra
        desenhar_botao(RECTS['comum']['btn_voltar_rect'], (60, 60, 60), (100, 30, 30), "←", CORES['BRANCO'])
        desenhar_botao(RECTS['configuracoes']['btn_tema_rect'], cor_final_btn, cor_final_btn, texto_tema, cor_texto_tema, 'p')
    elif estado in ['ESPERA', 'ESTIMULO', 'FEEDBACK']:
        cores_tema = TEMAS[tema_atual]
        tela.fill(cores_tema['fundo'])

        desenhar_barra_progresso()
        # Desenha o botão X no canto
        desenhar_botao(RECTS['comum']['btn_x_fec_rect'], (150, 0, 0), (200, 0, 0), "X", (255, 255, 255))
        if estado == 'ESPERA':
            mostrar_texto("Aguarde o estímulo...", CORES['CINZA_CLARO'], LARGURA/2, ALTURA/2 + 200, 'p')
            if time.time() >= proximo_evento:
                if not lista_estimulos: estado = 'FIM'
                else:
                    tipo_atual = random.choice(['VISUAL', 'SONORO'])
                    subtipo_atual = lista_estimulos.pop()

                    momento_estimulo = time.time();
                    estado = 'ESTIMULO';
                    proximo_evento = time.time() + 1.2

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
     
            if time.time() >= proximo_evento:
                if subtipo_atual == 'GO':
                    erros_omissao += 1
                tentativa_atual += 1
                estado = 'ESPERA' if tentativa_atual < TENTATIVAS_TOTAIS else 'FIM'
                proximo_evento = time.time() + random.uniform(1.5,3.0)

        elif estado == 'FEEDBACK':
            if time.time() >= proximo_evento:
                tentativa_atual += 1
                estado = 'ESPERA' if tentativa_atual < TENTATIVAS_TOTAIS else 'FIM'
                proximo_evento = time.time() + random.uniform(1.0,3.5)


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

            cores_tema = TEMAS[tema_atual]
            tela.fill(CORES['FUNDO']) 

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
            desenhar_botao(RECTS['home']['btn_finalizar_rect'], (192, 192, 192), (210, 210, 210), "ENCERRAR SESSÃO", (0,0,0))

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
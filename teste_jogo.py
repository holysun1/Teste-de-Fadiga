import pygame
import random
import time
import sys
import os
import csv
import numpy as np
from datetime import datetime

def obter_caminho_externo():
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como .exe, olha para a pasta do executável
        return os.path.dirname(sys.executable)
    # Se estiver rodando como .py, olha para a pasta do script
    return os.path.dirname(os.path.abspath(__file__))


import sys
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, seja no modo script ou .exe """
    try:
        # Caminho da pasta temporária do PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)




# --- Inicialização ---
pygame.init()
pygame.mixer.init()

usuario_atual = ""
input_ativo = True
cursor_visivel = True
ultimo_blink = time.time()

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
            if event.key == pygame.K_RETURN:
                if len(usuario_atual) > 2: 
                    estado = 'MENU'
            elif event.key == pygame.K_BACKSPACE:
                usuario_atual = usuario_atual[:-1]
            elif event.key != pygame.K_ESCAPE:
                if len(usuario_atual) < 15:
                    if event.unicode.isprintable() and event.unicode != '\r':
                        usuario_atual += event.unicode

    # --- Lógica de Estados ---
    if estado == 'LOGIN':
        mostrar_texto("SISTEMA DE CONTROLE DE FADIGA", CORES['AMARELO'], LARGURA/2, 150, 'm')
        mostrar_texto("Digite o nome do operador e aperte ENTER:", CORES['BRANCO'], LARGURA/2, 220, 'p')
        
        # Desenho da caixa de texto
        box_rect = pygame.Rect(LARGURA/2 - 150, 260, 300, 50)
        pygame.draw.rect(tela, CORES['CINZA_ESC'], box_rect, border_radius=5)
        pygame.draw.rect(tela, CORES['AZUL'], box_rect, 2, border_radius=5)
        
        # Lógica do Cursor piscante
        if time.time() - ultimo_blink > 0.5:
            cursor_visivel = not cursor_visivel
            ultimo_blink = time.time()
            
        txt_display = usuario_atual + ("|" if cursor_visivel else "")
        mostrar_texto(txt_display, CORES['BRANCO'], LARGURA/2, 285, 'm')
        pass
            
# Lógica de cliques (para o resto do sistema)
    elif estado == 'MENU':
        btn_L_rect = pygame.Rect(150, 160, 230, 45)
        btn_R_rect = pygame.Rect(420, 160, 230, 45)
        btn_go_rect = pygame.Rect(150, 260, 230, 45)
        btn_nogo_rect = pygame.Rect(420, 260, 230, 45)
        btn_cores_rect = pygame.Rect(150, 330, 230, 45)
        btn_hist_rect = pygame.Rect(420, 330, 230, 45)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
                clique = True
        mostrar_texto("CALIBRAÇÃO DE ESTÍMULOS", CORES['AMARELO'], LARGURA/2, 80, 'g')
        mostrar_texto("Complete o preparo antes de iniciar:", CORES['BRANCO'], LARGURA/2, 150, 'p')
        # --- BOTÕES DE ÁUDIO (L/R) ---
        # Canal Esquerdo
        pygame.draw.rect(tela, CORES['OK'] if checks['som_L'] else CORES['CINZA_ESC'], btn_L_rect, border_radius=8)
        mostrar_texto("TESTAR ESQUERDO (L)", CORES['BRANCO'], 265, 182, 'p')

        # Canal Direito
        pygame.draw.rect(tela, CORES['OK'] if checks['som_R'] else CORES['CINZA_ESC'], btn_R_rect, border_radius=8)
        mostrar_texto("TESTAR DIREITO (R)", CORES['BRANCO'], 535, 182, 'p')

        # --- 2. REVISÃO DE ESTÍMULOS (GO/NOGO) ---
        mostrar_texto("2. Reconheça os sinais do teste:", CORES['BRANCO'], LARGURA/2, 235, 'p')
        btn_go_rect = pygame.Rect(150, 260, 230, 45) 
        btn_nogo_rect = pygame.Rect(420, 260, 230, 45)
        
        pygame.draw.rect(tela, CORES['OK'] if checks.get('som_go') else CORES['CINZA_ESC'], btn_go_rect, border_radius=8)
        mostrar_texto("BIP AGUDO (GO)", CORES['BRANCO'], 265, 282, 'p')

        pygame.draw.rect(tela, CORES['OK'] if checks.get('som_nogo') else CORES['CINZA_ESC'], btn_nogo_rect, border_radius=8)
        mostrar_texto("BIP GRAVE (NOGO)", CORES['BRANCO'], 535, 282, 'p')        
        # --- BOTÃO: REVISAR CORES ---
        btn_cores_rect = pygame.Rect(150, 300, 230, 50)
        cor_cores = CORES['OK'] if checks['cores'] else CORES['CINZA_ESC']
        pygame.draw.rect(tela, cor_cores, btn_cores_rect,  border_radius=8)
        
        # Se o mouse estiver em cima, desenha os exemplos de cores ao lado do texto
        if btn_cores_rect.collidepoint(mouse_pos):
            mostrar_texto("REVISAR CORES", CORES['BRANCO'], 245, 325, 'p') # Texto um pouco para a esquerda
            pygame.draw.rect(tela, CORES['VERDE'], (330, 315, 20, 20))    # Exemplo Verde
            pygame.draw.rect(tela, CORES['VERMELHO'], (355, 315, 20, 20)) # Exemplo Vermelho
            if clique:
                checks['cores'] = True
        else:
            mostrar_texto("REVISAR CORES", CORES['BRANCO'], 265, 325, 'p') # Texto centralizado normal

        # --- BOTÃO: VER HISTÓRICO ---
        # --- Lógica de Verificação de Banco de Dados ---
        pasta_db = obter_caminho_externo()
        arquivo_db = os.path.join(pasta_db, "log_foco_detalhado.csv")
        existe_db = os.path.exists(arquivo_db)

        # --- Desenho do Botão de Histórico ---
        # Se não existe banco, desenha em cinza, se existe, desenha na cor normal
        cor_btn_hist = CORES['AZUL'] if existe_db else (100, 100, 100) # Cinza se vazio
        
        # (Aqui vai o seu código de desenhar o retângulo do botão de histórico)
        pygame.draw.rect(tela, cor_btn_hist, btn_hist_rect, border_radius=5)
        mostrar_texto("HISTÓRICO", CORES['BRANCO'], btn_hist_rect.centerx, btn_hist_rect.centery, 'p')

# --- LÓGICA DE CLIQUE ATUALIZADA ---
        if clique:
            if btn_L_rect.collidepoint(mouse_pos):
                canal = som_go.play()
                if canal: # Proteção extra: só ajusta volume se o canal foi criado
                    canal.set_volume(1.0, 0.0)
                checks['som_L'] = True
                
            elif btn_R_rect.collidepoint(mouse_pos):
                canal = som_go.play()
                if canal:
                    canal.set_volume(0.0, 1.0)
                checks['som_R'] = True
                
            elif btn_go_rect.collidepoint(mouse_pos):
                som_go.play()
                checks['som_go'] = True
                
            elif btn_nogo_rect.collidepoint(mouse_pos):
                som_nogo.play()
                checks['som_nogo'] = True            
                
            elif btn_cores_rect.collidepoint(mouse_pos): 
                checks['cores'] = True
                
            elif btn_hist_rect.collidepoint(mouse_pos):
                if existe_db:
                    import dashboard
                    dashboard.gerar_analise()
                else:
                    # Opcional: Avisar o usuário que não tem dados
                    print("Banco de dados vazio. Faça um teste primeiro.")

        # --- BOTÃO INICIAR ---
        pode_iniciar = all(checks.values())
        btn_start_rect = pygame.Rect(LARGURA/2 - 120, 450, 240, 70)
        cor_start = CORES['VERDE'] if pode_iniciar else CORES['CINZA_ESC']
        if pode_iniciar and btn_start_rect.collidepoint(mouse_pos): cor_start = CORES['AZUL']
        
        pygame.draw.rect(tela, cor_start, btn_start_rect, border_radius=15)
        txt_btn = "INICIAR TESTE" if pode_iniciar else "BLOQUEADO"
        mostrar_texto(txt_btn, CORES['BRANCO'], LARGURA/2, 485, 'm')

        if not pode_iniciar:
            mostrar_texto("Complete todos os testes acima para liberar", CORES['VERMELHO'], LARGURA/2, 430, 'p')

        if btn_start_rect.collidepoint(mouse_pos) and clique and pode_iniciar:
            tentativa_atual = 0
            dados_coletados = []
            erros_impulso = 0
            erros_omissao = 0
            if 'salvo' in locals(): del salvo
            estado = 'ESPERA'
            proximo_evento = 0

    elif estado in ['ESPERA', 'ESTIMULO', 'FEEDBACK']:
        desenhar_barra_progresso()
        if estado == 'ESPERA':
            mostrar_texto("Aguarde o estímulo...", CORES['CINZA_CLARO'], LARGURA/2, ALTURA/2 + 200, 'p')
            if proximo_evento == 0: proximo_evento = agora + random.uniform(1.5, 3.5)
            if agora >= proximo_evento:
                tipo_atual = random.choice(['VISUAL', 'SONORO'])
                subtipo_atual = 'GO' if random.random() < 0.7 else 'NOGO'
                estado = 'ESTIMULO'; momento_estimulo = agora; proximo_evento = agora + 1.2
                if tipo_atual == 'SONORO': som_go.play() if subtipo_atual == 'GO' else som_nogo.play()

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
                proximo_evento = 0

        elif estado == 'FEEDBACK':
            txt = "CORRETO!" if subtipo_atual == 'GO' else "ERRO!"
            cor = CORES['VERDE'] if subtipo_atual == 'GO' else CORES['VERMELHO']
            mostrar_texto(txt, cor, LARGURA/2, ALTURA/2, 'm')
            if agora >= proximo_evento:
                tentativa_atual += 1
                estado = 'ESPERA' if tentativa_atual < TENTATIVAS_TOTAIS else 'FIM'
                proximo_evento = 0

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
            
            # 2. O SEGREDO: Resetar os checks de calibração
            # Ao colocar tudo como False, o botão "INICIAR" do Menu desaparece
            # e o programa é obrigado a parar no Menu e esperar você testar tudo de novo.
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
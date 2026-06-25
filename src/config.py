# config.py
import pygame

LARGURA = 0
ALTURA = 0
RECTS = {}
TEMAS = {}
CORES = {}

def inicializar_config(largura_real, altura_real):
    global LARGURA, ALTURA, RECTS, TEMAS
    
    LARGURA = largura_real
    ALTURA = altura_real
    CORES.update({
        'PRETO': (0, 0, 0),
        'BRANCO': (255, 255, 255),
        'CINZA_ESC': (50, 50, 50),
        'CINZA_CLARO': (200, 210, 220),
        'FUNDO_GELO': (240, 245, 250),
        'VERDE': (50, 150, 50),
        'VERMELHO': (200, 50, 50),
        'AMARELO': (255, 220, 0),
        'AZUL': (0, 100, 200),
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
    })

    TEMAS.update({
        'escuro': {
            'fundo': CORES['FUNDO'],
            'texto': CORES['BRANCO'],
            'caixas': CORES['CINZA_ESC']
        },
        'claro': {
            'fundo': CORES['FUNDO_GELO'],
            'texto': CORES['CINZA_ESC'],
            'caixas': CORES['CINZA_CLARO']
        }
    })

    larg_b = 300
    largura_padrao = 400
    altura_padrao = 45
    pos_x_centro = LARGURA/2 - (largura_padrao / 2)
    margem_x = LARGURA / 2

    RECTS.update({
        'home': {
            'btn_teste_h': pygame.Rect(LARGURA/2 - larg_b/2, 250, larg_b, 50),
            'btn_admin_h': pygame.Rect(LARGURA/2 - larg_b/2, 310, larg_b, 50),
            'btn_config_h': pygame.Rect(LARGURA/2 - larg_b/2, 370, larg_b, 50),
            'btn_finalizar_rect': pygame.Rect(30, ALTURA -80,100,50),
            'rect_pesquisa': pygame.Rect(LARGURA - 120, 40, 80, 80),
            'rect_reclamacao': pygame.Rect(LARGURA - 120, ALTURA - 120, 80, 80),
            'rect_logo': pygame.Rect(LARGURA/2 - 100, 40, 200, 100)
        },
        'login': {
            'rect_nome': pygame.Rect(LARGURA/2 - 150, 200, 300, 45),
            'rect_senha': pygame.Rect(LARGURA/2 - 150, 300, 300, 45),
            'btn_entrar_rect': pygame.Rect(LARGURA/2 - 75, 360, 150, 45)
        },
        'cadastro': {
            'rect_nome': pygame.Rect(pos_x_centro, 150, largura_padrao, altura_padrao),
            'rect_cpf': pygame.Rect(pos_x_centro, 230, largura_padrao, altura_padrao),
            'rect_setor': pygame.Rect(pos_x_centro, 310, largura_padrao, altura_padrao),
            'rect_nivel': pygame.Rect(pos_x_centro, 390, largura_padrao, altura_padrao),
            'btn_cad_rect' : pygame.Rect(margem_x - 175, 250, largura_padrao, altura_padrao),
            'btn_hist_rect' : pygame.Rect(margem_x - 175, 180, largura_padrao, altura_padrao),
            'btn_grafico_rect' : pygame.Rect(margem_x - 175, 320, largura_padrao, altura_padrao),
            'btn_config_rect' : pygame.Rect(margem_x - 175, 390, largura_padrao, altura_padrao),
            'btn_salvar_cad': pygame.Rect(pos_x_centro, 470, largura_padrao, 50)
        },
        'comum': {
            'btn_voltar_rect': pygame.Rect(30, ALTURA - 75, 150, 45),
            'btn_x_fec_rect': pygame.Rect(LARGURA - 50, 10, 40, 40)
        },
        'pesquisa_sugestao': {
            'rect_nome_p': pygame.Rect(100, 180, 400, 40),
            'rect_sugestao_p': pygame.Rect(100, 270, 600, 60),
            'rect_critica_p': pygame.Rect(100, 380, 600, 60),
            'rect_enviar_p': pygame.Rect(100, 470, 150, 45)
        },
        'teste_operador': {
            'btn_go_rect': pygame.Rect(margem_x - 240, 220, 230, 45),
            'btn_nogo_rect': pygame.Rect(margem_x + 10, 220, 230, 45),
            'btn_cores_rect': pygame.Rect(margem_x - 115, 290, 230, 45), 
            'btn_start_rect': pygame.Rect(margem_x - 150, 460, 300, 70)
        },
        'configuracoes': {
            'btn_tema_rect': pygame.Rect(LARGURA/2 - 175, 250, 350, 60) # Centralizado dinamicamente
        }
    })
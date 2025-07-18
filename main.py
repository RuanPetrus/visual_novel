# Example file showing a circle moving on screen
import os
from copy import copy
from dataclasses import dataclass, field
from enum import Enum
import pygame
from pygame.font import Font
from pygame import Surface, Color, Rect, K_RETURN, K_UP, K_DOWN, K_s
import pygame.mixer

SEP = os.path.sep
IMAGES_FOLDER = "images" +SEP
FONTS_FOLDER = "fonts" + SEP
CARACTER_FOLDER = IMAGES_FOLDER + "caracters" + SEP
BG_FOLDER = IMAGES_FOLDER + "backgrounds" + SEP
MUSIC_FOLDER = "music" + SEP
# SCREEN_WIDTH = 1920
# SCREEN_HEIGHT = 1080
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
DIALOG_PADDING = 25
DIALOG_CORNER_RADIUS = 10
DIALOG_OPPACITY = 0.8

STATUS_PADDING = SCREEN_HEIGHT // 60
MINI_STATUS_PADDING = SCREEN_HEIGHT // 600

MENU_WIDTH = 3/4 * SCREEN_WIDTH
MENU_HEIGHT = 3/4 * SCREEN_HEIGHT

DIALOG_WIDTH = 9/10 * SCREEN_WIDTH
DIALOG_HEIGHT = 1/3 * SCREEN_HEIGHT

STATS_WIDTH = 3/4 * SCREEN_WIDTH
STATS_HEIGHT = 3/4 * SCREEN_HEIGHT

MINI_STATS_WIDTH = 1/6 * SCREEN_WIDTH
MINI_STATS_HEIGHT = 1/4 * SCREEN_HEIGHT

CARACTER_HEIGHT = 3/4 * SCREEN_HEIGHT

CARACTER_SEP_SIZE = 20
FONT_SIZE = 40
TITLE_FONT_SIZE = 50
STATS_TITLE_FONT_SIZE = 70
STATS_MINI_FONT_SIZE = 10

WHITE = Color(255, 255, 255, 255)
BLACK = Color(0, 0, 0, 255)
BLUE = Color(79, 70, 228, 255)
GREEN = Color(0, 255, 0, 255)

MENU_FG_COLOR = Color(48, 55, 62, 255)
MENU_BG_COLOR = Color(245, 247, 250, 255)

STATS_COLORS = [
    BLUE, 
    Color(22, 163, 74, 255),
    Color(14, 165, 233, 255),
    Color(236, 72, 153, 255),
    Color(245, 158, 11, 255),
    Color(220, 38, 38, 255),
    Color(16, 185, 129, 255),
    Color(139, 92, 246, 255),
]

# class syntax

class Pos(Enum):
    LEFT = 0
    RIGHT = 2
    CENTER = 1

@dataclass
class Caracter:
    name: str
    sprite: pygame.Surface
    pos: Pos

class ActionType(Enum):
    ShowCaracter = 0
    HideCaracter = 1
    ChangeDialog = 2
    ShowMenu = 3
    ShowStats = 4
    ChangeBackGround = 5

@dataclass
class Option:
    text: str
    status: dict[str, int] = field(default_factory=dict)

@dataclass
class Action:
    type: ActionType
    caracter: Caracter | None = None
    dialog: str | None = None
    menu: list[Option] | None = None
    background: Surface | None = None

@dataclass
class Game:
    screen: Surface
    caracter_surface: Surface
    dialog_surface: Surface
    menu_surface: Surface
    stats_surface: Surface
    stats_mini_surface: Surface
    font: Font
    menu_font: Font
    dialog_title_font: Font
    stats_font: Font
    stats_title_font: Font
    stats_mini_font: Font
    running: bool = True
    dt: float = 0
    caracters: list[Caracter] = field(default_factory=list)
    dialog: str = ""
    dialog_title: str = ""
    actions: list[Action] = field(default_factory=list)
    action_idx: int = 0
    last_keys: dict[int, bool] = field(default_factory=dict)
    useful_keys: list[int] = field(default_factory=list)
    player_status: dict[str, int] = field(default_factory=dict)
    menu: list[Option] | None = None
    menu_idx: int = 0
    background: Surface | None = None
    show_stats: bool = False
    stats_colors: list[Color] = field(default_factory=list)


def scale_uniform(s: Surface, scalar: float) -> Surface:
    w, h = s.get_size()
    return pygame.transform.smoothscale(s, (w * scalar, h * scalar))

def draw_caracters(game: Game) -> None:
    left_cs = [c for c in game.caracters if c.pos == Pos.LEFT]
    right_cs = [c for c in game.caracters if c.pos == Pos.RIGHT]
    center_cs = [c for c in game.caracters if c.pos == Pos.CENTER]

    region_width = game.caracter_surface.get_width() / 3

    def draw_region(cs: list[Caracter]):
        if len(cs) == 0: return
        caracter_width = region_width / len(cs)
        for i, c in enumerate(cs):
            game.caracter_surface.blit(c.sprite, (c.pos.value * region_width + i * caracter_width, 0))


    draw_region(left_cs)
    draw_region(right_cs)
    draw_region(center_cs)

def dialog_to_surface(text: str, dialog_width: int, font: Font, color: Color) -> Surface:
    lines: list[list[str]] = []
    curr_line: list[str] = []

    for w in text.split():
        if font.size(" ".join(curr_line + [w]))[0] <= dialog_width:
            curr_line.append(w)
        else:
            lines.append(curr_line)
            curr_line = [w]
    if len(curr_line) > 0:
        lines.append(curr_line)

    total_height = 0
    for i, line_words in enumerate(lines):
        line_text = " ".join(line_words)
        _, font_height = font.size(line_text)
        total_height += font_height

    dialog_surface = Surface((dialog_width, total_height), pygame.SRCALPHA, 32)

    for i, line_words in enumerate(lines):
        line_text = " ".join(line_words)
        _, font_height = font.size(line_text)

        line_surf = font.render(line_text, False, color)
        line_rect = line_surf.get_rect(topleft = (0, i * font_height))
        dialog_surface.blit(line_surf, line_rect)

    return dialog_surface

def draw_borded_rectangle(surface: Surface, rect: Rect, color: Color, border_color: Color, 
                          corner_radius: int, border_thickness: int =2):
    # Inner rectangle
    inner_rect = pygame.Rect(
        rect.x + border_thickness, 
        rect.y + border_thickness, 
        rect.width - 2*border_thickness, 
        rect.height - 2*border_thickness
    )
    
    # Draw border
    pygame.draw.rect(surface, border_color, rect, border_radius=corner_radius)
    
    # Draw inner filled rectangle
    pygame.draw.rect(surface, color, inner_rect, border_radius=corner_radius)

def draw_dialog(game: Game) -> None:
    vertical_padding = DIALOG_PADDING

    menu_fg = copy(MENU_FG_COLOR)
    menu_bg = copy(MENU_BG_COLOR)
    menu_bg_transp = copy(menu_bg)
    menu_bg_transp.a = int(menu_bg_transp.a * DIALOG_OPPACITY)
    menu_fg_transp = copy(menu_fg)
    menu_fg_transp.a = int(menu_fg_transp.a * DIALOG_OPPACITY)

    option_surface = Surface(game.dialog_surface.get_size(), pygame.SRCALPHA, 32)
    draw_borded_rectangle(option_surface, option_surface.get_rect(), menu_bg_transp, menu_fg_transp, DIALOG_CORNER_RADIUS)

    if game.dialog_title:
        vertical_padding += game.dialog_title_font.size(game.dialog_title)[1]
        option_surface.blit(
            dialog_to_surface(game.dialog_title, option_surface.get_width() * DIALOG_PADDING, game.dialog_title_font, menu_fg), 
            (DIALOG_PADDING, DIALOG_PADDING)
        )

    option_surface.blit(
        dialog_to_surface(game.dialog, game.dialog_surface.get_width()-2 * DIALOG_PADDING, game.font, menu_fg), 
        (DIALOG_PADDING, vertical_padding)
    )
    game.dialog_surface.blit(option_surface, (0, 0))

def draw_menu(game: Game):
    if game.menu is None: return
    option_height = game.menu_surface.get_height() / len(game.menu)
    for i, opt in enumerate(game.menu):
        option_width = game.menu_surface.get_width()
        option_surface = Surface((option_width, option_height), pygame.SRCALPHA, 32)
        menu_fg = copy(MENU_FG_COLOR)
        menu_bg = copy(MENU_BG_COLOR)

        if game.menu_idx == i:
            menu_fg, menu_bg = menu_bg, menu_fg

        menu_bg_transp = copy(menu_bg)
        menu_bg_transp.a = int(menu_bg_transp.a * DIALOG_OPPACITY)

        menu_fg_transp = copy(menu_fg)
        menu_fg_transp.a = int(menu_fg_transp.a * DIALOG_OPPACITY)

        draw_borded_rectangle(option_surface, option_surface.get_rect(), menu_bg_transp, menu_fg_transp, DIALOG_CORNER_RADIUS)

        option_surface.blit(
            dialog_to_surface(opt.text, option_width - 2* DIALOG_PADDING, game.menu_font, menu_fg), 
            (DIALOG_PADDING, DIALOG_PADDING)
        )
        game.menu_surface.blit(option_surface, (0, i * option_height))

def draw_background(game: Game):
    if game.background is None: return
    if game.show_stats: return
    background = pygame.transform.scale(game.background, game.screen.get_size())
    game.screen.blit(background, (0, 0))

def draw_stats(game: Game):
    text_width = 0
    text_height = 0
    for k in game.player_status:
        width, height = game.stats_font.size(k)
        text_width = max(text_width, width)
        text_height += height

    value_width = game.stats_surface.get_width() - text_width - DIALOG_PADDING

    text_sur = Surface((text_width, text_height), pygame.SRCALPHA, 32)
    value_sur = Surface((value_width, text_height), pygame.SRCALPHA, 32)

    vertical_offset = 0
    for i, k in enumerate(game.player_status):
        width, height = game.stats_font.size(k)
        stat_color = game.stats_colors[i % len(game.stats_colors)]
        stat_value_width = game.player_status[k] / 100 * value_width
        text_sur.blit(
            dialog_to_surface(k, text_width, game.stats_font, stat_color), 
            (0, vertical_offset)
        )
        # Drawing empty bar
        pygame.draw.rect(value_sur, MENU_FG_COLOR, Rect(0, vertical_offset+STATUS_PADDING, value_width, height - 2*STATUS_PADDING), border_radius=10)

        # Drawing colored bar
        pygame.draw.rect(value_sur, stat_color, Rect(0, vertical_offset+STATUS_PADDING, stat_value_width, height - 2*STATUS_PADDING), border_radius=10)

        vertical_offset += height

    title = "Status"
    title_sur = dialog_to_surface(title, game.stats_title_font.size(title)[0], game.stats_font, MENU_FG_COLOR)
    game.stats_surface.blit(
        title_sur, 
        ((game.stats_surface.get_width() - title_sur.get_width())/2, 0)
    )

    title_height = title_sur.get_height()
    d_height = title_height + (game.stats_surface.get_height() - text_height - title_height)/2

    game.stats_surface.blit(text_sur, (0, d_height))
    game.stats_surface.blit(value_sur, (text_width + DIALOG_PADDING, d_height))

def draw_mini_status(game: Game):
    text_width = 0
    text_height = 0
    for k in game.player_status:
        width, height = game.stats_mini_font.size(k)
        text_width = max(text_width, width)
        text_height += height

    value_width = game.stats_mini_surface.get_width()
    value_sur = Surface((value_width, text_height), pygame.SRCALPHA, 32)

    vertical_offset = 0
    for i, k in enumerate(game.player_status):
        width, height = game.stats_mini_font.size(k)
        stat_color = game.stats_colors[i % len(game.stats_colors)]
        stat_value_width = game.player_status[k] / 100 * value_width
        # Drawing empty bar
        pygame.draw.rect(value_sur, MENU_FG_COLOR, Rect(0, vertical_offset+MINI_STATUS_PADDING, value_width, height - 2*MINI_STATUS_PADDING), border_radius=10)

        # Drawing colored bar
        pygame.draw.rect(value_sur, stat_color, Rect(0, vertical_offset+MINI_STATUS_PADDING, stat_value_width, height - 2*MINI_STATUS_PADDING), border_radius=3)

        vertical_offset += height

    game.stats_mini_surface.blit(value_sur, (game.stats_mini_surface.get_width() - value_width, 0))

def update_game(game: Game):
    if game.action_idx < len(game.actions):
        action = game.actions[game.action_idx]
        type = action.type
        match type:
            case type.ShowCaracter:
                if action.caracter is None:
                    print("Unreacheable Path")
                    exit(1)
                else:
                    game.caracters.append(action.caracter)
                    game.action_idx += 1
            case type.HideCaracter:
                if action.caracter is None:
                    print("Unreacheable Path")
                    exit(1)
                else:
                    game.caracters.remove(action.caracter)
                    game.action_idx += 1
            case type.ChangeDialog:
                if action.dialog is None:
                    print("Unreacheable Path")
                    exit(1)
                else:
                    game.dialog = action.dialog
                    if action.caracter:
                        game.dialog_title =action.caracter.name
                    else:
                        game.dialog_title = ""
            case type.ShowMenu:
                if action.menu is None:
                    print("Unreacheable Path")
                    exit(1)
                else:
                    game.menu = action.menu
                    game.dialog = ""
                    game.dialog_title = ""
            case type.ChangeBackGround:
                if action.background is None:
                    print("Unreacheable Path")
                    exit(1)
                else:
                    game.background = action.background
                    game.action_idx += 1
            case type.ShowStats:
                pygame.mixer.music.fadeout(2000) 
                pygame.mixer.music.load(MUSIC_FOLDER + "end.mp3") 
                pygame.mixer.music.set_volume(0.7)
                pygame.mixer.music.play(-1,0.0)
                game.show_stats = True
                game.action_idx += 1
    else:
        pass

def game_script(game: Game) -> None:
    def show(c: Caracter, pos: Pos = Pos.LEFT):
        c.pos = pos
        game.actions.append(Action(type=ActionType.ShowCaracter, caracter=c))

    def hide(c: Caracter, pos: Pos = Pos.LEFT):
        c.pos = pos
        game.actions.append(Action(type=ActionType.HideCaracter, caracter=c))

    def dialog(s: str, c: Caracter | None = None):
        game.actions.append(Action(type=ActionType.ChangeDialog, dialog=s, caracter=c))

    def menu(v: list[Option]):
        game.actions.append(Action(type=ActionType.ShowMenu, menu=v))

    def scene(b: Surface):
        game.actions.append(Action(type=ActionType.ChangeBackGround, background=b))

    def script() -> None:
        status = {
            "bem_estar": 50,
            "privacidade": 50,
            "integridade": 50,
            "inclusao": 50,
            "respeito_com_equipe": 50,
            "respeito_com_chefe" : 50,
            "respeito_na_empresa": 50,
        }
        game.player_status = status

        bg_office = pygame.image.load(BG_FOLDER + 'gigahard_office.png').convert()
        bg_reception = pygame.image.load(BG_FOLDER + 'gigahard_entrance.png').convert()
        bg_office_tour = pygame.image.load(BG_FOLDER + 'gigahard_tour.png').convert()
        bg_meeting_room = pygame.image.load(BG_FOLDER + 'gigahard_office.png').convert()
        happy_hour = pygame.image.load(BG_FOLDER + 'happy_hour.png').convert()
        carlos_office = pygame.image.load(BG_FOLDER + 'carlos_office.png').convert()
        boarding = pygame.image.load(BG_FOLDER + 'boarding_room.png').convert()

        thiago = Caracter(
            name="Thiago", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'thiago.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )
        alissa = Caracter(
            name="Alissa", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'alissa.png').convert_alpha(), 0.3), 
            pos=Pos.LEFT
        )
        maria = Caracter(
            name="Maria Clara", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'maria_clara.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )
        recepcionista = Caracter(
            name="Recepcionista", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'recepcionist.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )
        carlos = Caracter(
            name="Carlos", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'carlos.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )
        wellington = Caracter(
            name="Wellington", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'wellington.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )

        julio = Caracter(
            name="Júlio", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'julio.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )

        leticia = Caracter(
            name="Letícia", 
            sprite=scale_uniform(pygame.image.load(CARACTER_FOLDER + 'leticia.png').convert_alpha(), 0.5), 
            pos=Pos.LEFT
        )

        def capitulo_1():
            scene(bg_reception)
            # Dia 0 - Contexto
            dialog("Thiago era programador pleno numa empresa de médio porte, onde nunca se sentiu realizado profissionalmente.")
            dialog("Recentemente, ele decidiu dar um passo ousado: aceitou uma vaga júnior na MicroHard - a empresa dos seus sonhos desde a época da faculdade.")
            dialog("Apesar da queda na senioridade e na remuneração, Thiago viu na MicroHard uma oportunidade única:  sempre admirou os produtos da empresa e sabe que, além da boa  reputação, ela oferece ótimas perspectivas de crescimento e bons salários no longo prazo.")
            dialog("Com este contexto, Thiago está determinado (e um pouco pressionado) a ascender profissionalmente e conquistar seu espaço na  MicroHard. Para isso, ele planeja ser participativo e empenhado nas atividades dentro da MicroHard")

            # Dia 1
            dialog("Dia 1")

            show(thiago, Pos.LEFT)
            dialog("Olá… meu nome é Thiago. Recebi um e-mail de confirmação dizendo que hoje seria meu primeiro dia de trabalho.", thiago)

            show(alissa, Pos.RIGHT)
            dialog("Oi… eu sou a Alissa. Também recebi um e-mail assim.", alissa)

            hide(alissa)
            hide(thiago)
            show(recepcionista, Pos.CENTER)
            dialog("Ah, claro! Vocês devem fazer parte da nova leva de contratados. Vou ligar para o andar de cima, alguém já deve vir recebê-los.", recepcionista)

            hide(recepcionista)
            show(carlos, Pos.CENTER)
            dialog("Olá! Meu nome é Carlos. Provavelmente serei o gerente de vocês. Gostariam de conhecer o prédio?", carlos)
            hide(carlos)

            show(alissa, Pos.RIGHT)
            show(thiago,Pos.CENTER)

            dialog("Sim, claro.", thiago)
            dialog("Sim!", alissa)

            hide(alissa)
            hide(thiago)

            scene(bg_office_tour)
            show(thiago)
            dialog("Uau… a estrutura aqui é realmente impressionante.", thiago)

            show(carlos, Pos.CENTER)
            dialog("Então… vocês já devem ter ouvido um pouco sobre a área de atuação. Foram designados para trabalhar no InsightPro, uma ferramenta que pretende reunir dados de várias fontes - redes sociais, marketplaces, indicadores econômicos, entre outros - para oferecer insights a pequenos comércios.", carlos )
            dialog("Como devem saber, nossa concorrente, a Gluglu, anunciou há alguns meses o desenvolvimento de uma ferramenta semelhante, com previsão de lançamento até novembro deste ano."                                                                                                                    , carlos )
            dialog("Estamos desconfiados de um possível vazamento de informações. Por isso, precisamos acelerar nosso processo."                                                                                                                                                                                   , carlos )
            dialog("Queremos lançar algo melhor, e antes de novembro. Essa urgência motivou a contratação de vocês dois e de muitos outros profissionais."                                                                                                                                                         , carlos )

            dialog("Entendi… o clima deve estar bem intenso aqui…", thiago)

            dialog("Ainda não começamos os trabalhos, mas acredito que em breve as coisas estarão bem intensas sim.", carlos)
            hide(thiago)
            hide(carlos)
            show(alissa, Pos.CENTER)
            
            dialog("...", alissa)
            hide(alissa)
            show(carlos,Pos.CENTER)
            dialog("Bem… deixe-me apresentar os colegas de squad de vocês.", carlos)
            

            show(maria,Pos.LEFT)    
            dialog("Essa é a Maria, a funcionária mais antiga e esforçada do squad.", carlos)
            dialog("Prazer, eu sou a Maria.", maria)
            hide(maria)

            show(wellington,Pos.LEFT)   
            dialog("E este é o Wellington, também trabalha há uns anos na empresa.", carlos)
            dialog("Oi, eu sou o Wellington.", wellington)

            hide(wellington)
            dialog("Bem, para hoje devemos focar em buscar as nossas fontes de dados. Foquem em confiabilidade. Precisamos de dados robustos e de boa qualidade.", carlos)
            dialog("Amanhã, nesta mesma sala, às 16h teremos nossa primeira reunião.", carlos)

            dialog("Todos: Ok")
            hide(carlos)

            # Dia 2
            scene(bg_meeting_room)
            dialog("Dia 2")

            show(carlos, Pos.CENTER)
            dialog("Então… todos trouxeram as fontes de dados que se comprometeram a trazer?", carlos)
            hide(carlos)

            show(thiago, Pos.CENTER)
            dialog("Encontrei uma fonte de dados financeiros mantida por uma empresa privada. O acesso é pago, mas parece bastante promissora.", thiago)
            hide(thiago)

            show(alissa, Pos.CENTER)
            dialog("Eu achei duas fontes… não são muito abrangentes, mas eu achei os dados bem estruturados e robustos.", alissa)
            hide(alissa)

            show(wellington,Pos.CENTER)
            dialog("Consegui encontrar uma API feita por uma associação de produtores rurais. Esses dados são ótimos, oferecem informações únicas sobre um nicho que é muito importante para nós.", wellington )
            dialog("Estarmos de posse desses dados nos colocaria em uma posição muito privilegiada, mas o problema é que não encontrei a licença atrelada ao serviço.", wellington )
            dialog("Temo que, se entrarmos em contato diretamente, por se tratar de um produto com fins lucrativos, eles possam negar o acesso.", wellington )

            dialog("E o que vocês acham que devemos fazer com essa API? Lembrem-se: se não tivermos acesso a esses dados, e a Gluglu conseguir, ficaremos em desvantagem.", carlos)

            menu([
                Option("Mesmo sem encontrar uma licença explícita, a organização pode ter diretrizes internas sobre o uso da API. O correto é entrar em contato antes de utilizar qualquer dado. Enquanto não houver autorização formal, não devemos acessar nem armazenar essas informações", 
                       {"integridade": 10, "respeito_com_equipe": -10}),
                Option("A API está aberta, e conseguimos baixar os dados sem obstáculos. Podemos coletar tudo agora e só depois perguntar sobre a licença. Se houver uma negativa futura, ao menos já teremos uma base histórica valiosa salva para trabalhar.a", 
                       {"integridade": -5, "respeito_com_equipe": 10}),
                Option("Enquanto não houver uma restrição clara, devemos aproveitar. Se deixarmos passar, a Gluglu pode sair na frente. Vamos extrair o máximo possível agora - depois vemos como lidar com a parte legal.", 
                       {"integridade": -10, "respeito_com_equipe": 0}),
            ])


            hide(wellington)
            show(maria, Pos.CENTER)
            dialog("Consegui montar um script simples para extrair dados das conversas entre usuários de outros aplicativos nossos.", maria)
            dialog("Ainda é algo básico, mas no futuro dá para otimizar e estruturar melhor. Como se trata de um chat, conseguimos informações praticamente em tempo real.", maria)
            hide(maria)

            dialog("Esses dados parecem extremamente valiosos, Maria. Excelente trabalho. Como sempre, você se destaca nas entregas.", carlos)

            show(alissa, Pos.CENTER)
            dialog("Mas… os usuários desses apps sabem que as conversas deles podem ser utilizadas para treinar modelos como o do InsightPro?", alissa)
            hide(alissa)
            show(maria,Pos.CENTER)

            dialog("Algo nesse sentido está mencionado no rodapé dos termos de uso, mas é um texto bem genérico. Não tenho certeza se está claro para os usuários.", maria)

            menu([
                Option("Mesmo sem encontrar uma licença explícita, a organização pode ter diretrizes internas sobre o uso da API. O correto é entrar em contato antes de utilizar qualquer dado. Enquanto não houver autorização formal, não devemos acessar nem armazenar essas informações", 
                       {"integridade": 10, "respeito_com_equipe": +10}),
                Option("A API está aberta, e conseguimos baixar os dados sem obstáculos. Podemos coletar tudo agora e só depois perguntar sobre a licença. Se houver uma negativa futura, ao menos já teremos uma base histórica valiosa salva para trabalhar.a", 
                       {"integridade": -5, "respeito_com_equipe": +5}),
                Option("Enquanto não houver uma restrição clara, devemos aproveitar. Se deixarmos passar, a Gluglu pode sair na frente. Vamos extrair o máximo possível agora - depois vemos como lidar com a parte legal.", 
                       {"integridade": -10, "respeito_com_equipe": -5}),
            ])
            hide(maria)

        def capitulo_2():
            scene(boarding)
            dialog("Desde a coleta inicial dos dados, dias se passaram, com todos os membros do squad trabalhando intensamente…")

            dialog("Durante a reunião")

            show(alissa, Pos.RIGHT)
            dialog("Thiago… acabei de perceber que o último PR que você subiu pro repositório aberto estava com dados reais no commit.", alissa)
            hide(alissa)

            show(maria, Pos.CENTER)
            dialog("Sério? Informações pessoais de centenas de usuários estão expostas!", maria)
            hide(maria)

            show(carlos, Pos.LEFT)
            dialog("Precisamos agir rápido, mas se alguém perguntar, melhor dizer que foi uma falha genérica de configuração. Se gerarmos pânico interno, nosso squad inteiro perderá credibilidade com a diretoria.", carlos)
            show(thiago,Pos.RIGHT)

            dialog("O que fazer após o vazamento acidental?")
            menu([
                Option("Entendo, Carlos…Vou seguir sua orientação, minimizar o ocorrido para a diretoria e apagar os rastros", 
                    {"privacidade": -20, "integridade": -10}),
                Option("Acho importante reportar imediatamente o erro ao setor jurídico e de compliance da empresa. Isso pode gerar represálias mas devemos estar abertos a isso", 
                    {"privacidade": 20, "respeito_com_equipe": -10, "respeito_com_chefe": -10, "respeito_na_empresa": 20}),
                Option("Vou tentar corrigir o problema, mas só falarei do assunto com algum superior se me perguntarem", 
                    {"integridade": -5, "privacidade": -5, "respeito_com_equipe": 10, "respeito_com_chefe": 10}),
                Option("Posso tentar entrar em contato com os usuários afetados, mesmo sem aval oficial", 
                    {"privacidade": 15, "respeito_na_empresa": -40})
            ])
            hide(thiago)
            hide(carlos)
            show(maria)
            dialog("Ah, e antes que eu esqueça, tem outro ponto. Revendo os testes, notei que o nosso algoritmo entrega resultados menos precisos e com menor relevância para usuários da região Norte. Ainda não descobri por quê, mas me parece algo estrutural nos dados de entrada.", maria)

            show(wellington)
            dialog("Você não acha isso problemático?", wellington)
           

            dialog("Tecnicamente sim, mas é uma região que representa uma fatia bem pequena da nossa base de clientes. Não sei se vale a pena atrasar o projeto por isso.", maria)
            hide(wellington)
            hide(maria)
            show(carlos,Pos.CENTER)

            dialog("O tempo está contra nós. Precisamos decidir rápido o que fazer com esse modelo.", carlos)
            
            dialog("O que sugerir que seja feito?")
            menu([
                Option("Podemos lançar o modelo como está e planejar melhorias depois", 
                    {"integridade": -10, "respeito_com_equipe": +5}),
                Option("Acho que devemos reportar o problema para os superiores, e se sentirmos que esse problema vai demorar para ser resolvido, devemos sugerir o adiamento", 
                    {"integridade": 10, "respeito_com_chefe": -10, "respeito_com_equipe": -10, "respeito_na_empresa": -10}),
                Option("Podemos tentar 'compensar' o viés manualmente, ajustando os pesos de forma empírica", 
                    {"integridade": -5}),
                Option("Podemos tentar lançar aquela versão antiga que fizemos, que era menos precisa mas não tinha vieses tão gritantes", 
                    {"integridade": 5,})
            ])


            dialog("Certo. Ainda temos muito a fazer nesta sprint. Thiago, além de lidar com o problema do vazamento e revisar a parte de análise preditiva, vou precisar que você contribua com a documentação da nossa API.", carlos)
            hide(carlos)

            show(thiago, Pos.RIGHT)
            dialog("Carlos, eu entendo, mas estou acumulando tarefas das duas últimas sprints. Nem consegui revisar os testes que ficaram pendentes da semana passada…", thiago)
            hide(thiago)
            show(carlos)

            dialog("Infelizmente, o cronograma está apertado. Contamos com você.", carlos)

            menu([
                Option("Okay… Assim farei, posso trabalhar até tarde por uns dias", 
                    {"bem_estar": -15, "respeito_com_chefe": 10, "respeito_com_equipe": 10}),
                Option("Carlos, eu entendo que o cronograma está apertado, mas infelizmente eu estou sobrecarregado. O que acha de re-priorizar as tarefas então?", 
                    {"respeito_com_chefe": -10, "bem_estar": 10}),
                Option("Certo, chefe (depois tentarei passar a tarefa discretamente pro Wellington)", 
                    {"integridade": -10, "respeito_com_equipe": -5,"bem_estar": 5}),
                Option("Certo chefe (semana que vem entregarei apenas uma versão parcial da documentação)", 
                    {"respeito_com_chefe": -5, "integridade": -5, "respeito_com_equipe": -10})
            ])

            dialog("De fato eu ando percebendo que todos estão cansados. O que acham de sairmos para um happy hour quinta, para distrairmos do trabalho?", carlos)
            hide(carlos)


        def capitulo_3():
            scene(happy_hour)
           
            dialog("No happy hour")

            show(julio, Pos.LEFT)
            dialog("Opa, eai Thiago!", julio)

            show(thiago, Pos.RIGHT)
            dialog("Júlio! Como está! Que coisa boa te ver aqui! Veio com os amigos?", thiago)

            dialog("Não, vim com o pessoal do trabalho.", julio)

            dialog("Que coincidência, eu também! Vou ali me sentar à mesa, já conversamos!", thiago)

            hide(julio)
            hide(thiago)

            show(wellington, Pos.LEFT)
            dialog("Acho que o pessoal da Gluglu também está fazendo happy hour aqui hoje. Reconheço aquele rapaz sentado na ponta, trabalhamos juntos no passado.", wellington)

            show(maria, Pos.CENTER)
            dialog("O Thiago também conhece alguém ali pelo visto.", maria)

            show(thiago, Pos.RIGHT)
            dialog("Ah sim… é o Júlio, estudamos juntos na faculdade.", thiago)

            dialog("Imagina a vantagem se soubéssemos o estado do app que eles estão fazendo para concorrer com o InsightPro… Uma conversa entre amigos... não custa, né?", wellington)

            menu([
                Option("Ah.. não acho certo usar uma relação pessoal para obter vantagem competitiva. Contem comigo pra melhorar o InsightPro do jeito certo.", 
                    {"integridade": 10, "respeito_com_equipe": -10}),
                Option("Posso puxar assunto e tentar entender o que ele anda fazendo... se ele comentar algo naturalmente, não é problema nosso, né?", 
                    {"integridade": -5, "respeito_com_equipe": 10}),
                Option("Vou conversar com ele depois e ver se consigo algo. Mas isso fica só entre nós.", 
                    {"integridade": -15, "respeito_com_equipe": 10}),
                Option("hahaha….essa batata está boa, né? (jamais vou fazer isso)", 
                    {})
            ])
            hide(thiago)
            hide(maria)
            hide(wellington)

        def capitulo_4():
            scene(bg_office_tour)

            show(carlos, Pos.CENTER)
            dialog("Pessoal, essa é a Letícia. Ela foi realocada de outro time e vai trabalhar com a gente a partir de hoje.", carlos)

            show(leticia, Pos.LEFT)
            dialog("Oi, gente. Prazer em conhecer vocês. Estou animada pra contribuir no que puder.", leticia)

            dialog("Todos: Prazer, Letícia")

            dialog("A Letícia tem bastante experiência com engenharia de dados, então gostaria que vocês se organizassem e atribuíssem a ela alguma tarefa da sprint atual para que ela possa começar a se integrar.", carlos)
            hide(carlos)
            hide(leticia)

            show(wellington, Pos.CENTER)
            dialog("(sussurrando) Trabalhei com a Letícia num projeto no passado. Ela é gente boa, mas tem algumas limitações… é PcD, e às vezes leva mais tempo nas entregas.", wellington)

            show(maria)
            
            dialog("Logo agora que estamos com prazos tão apertados? Talvez pudéssemos passar para ela a refatoração das páginas da interface do usuário. Não é bem da área dela, mas pelo menos se atrasar, não afeta tanto o cronograma.", maria)
            hide(maria)

            show(alissa)        
            dialog("Também temos que terminar o pipeline da ingestão de dados externos, que é algo mais voltado para a área de atuação dela.", alissa)

            menu([
                Option("A Letícia tem experiência com engenharia de dados. Vamos colocá-la no pipeline, onde ela pode mostrar seu valor de verdade.", 
                    {"inclusao": 25, "integridade": 5, "respeito_com_equipe": -10}),
                Option("Acho melhor ela começar pela interface. Não é a área dela, mas evita riscos enquanto avaliamos o ritmo dela.", 
                    {"inclusao": -35, "respeito_com_equipe": 10}),
                Option("Podemos passar a documentação de pipeline. Assim ela participa, mas sem afetar código de produção.", 
                    {"inclusao": -20, "integridade": -10, "respeito_com_equipe": 10}),
                Option("Talvez devêssemos expor a situação dos prazos para ela e perguntar diretamente para ela qual tarefa ela prefere. Assim a gente respeita o tempo e o perfil dela.", 
                    {"inclusao": 30, "integridade": 5})
            ])
            show(thiago)
            hide(thiago)
            hide(wellington)
            hide(alissa)

        def capitulo_5():
            scene(bg_office)
            dialog("Semanas de trabalho intenso chegaram ao fim. Com o código estabilizado, as funcionalidades testadas e a interface final aprovada, o InsightPro estava finalmente pronto para ser entregue. A equipe estava exausta - mas também orgulhosa. Agora, restava apresentar os resultados, escrever os relatórios finais… e lidar com os detalhes que não apareciam nos dashboards.")

            show(carlos, Pos.CENTER)
            dialog("Gente, estamos prestes a receber o bônus de performance. Cumprimos os prazos, entregamos tudo o que estava previsto… mas temos que garantir que o relatório esteja 'alinhado' com isso.", carlos)
            hide(carlos)
            
            show(wellington, Pos.CENTER)
            dialog("Alinhado como?", wellington)
            hide(wellington)

            show(carlos, Pos.CENTER)
            dialog("Não precisamos falar tudo sobre os testes de viés regional? A gente só começou a tratar isso, então não precisa entrar nos detalhes. Um relatório técnico demais pode dar margem para problemas com a diretoria.", carlos)
            hide(carlos)

            show(maria, Pos.RIGHT)
            dialog("Mas se formos muito vagos, não soa como manipulação?", maria)
            hide(maria)

            show(carlos, Pos.CENTER)
            dialog("Nada disso. Só precisamos focar no que funcionou. O objetivo é garantir o bônus de todos aqui.", carlos)

            hide(carlos)
            show(thiago,Pos.CENTER)

            dialog("Como agir diante da proposta de omissão no relatório técnico?")
            menu([
                Option("Devemos incluir os pontos críticos, mesmo que isso comprometa o bônus. A transparência importa.", 
                    {"integridade": 10, "respeito_com_chefe": -10, "respeito_com_equipe": -5, "respeito_na_empresa": 20}),
                Option("Vamos citar os problemas, mas de forma bem superficial. Assim mostramos algo sem criar alarde.", 
                    {"integridade": 5, "respeito_com_equipe": 10}),
                Option("Concordo com Carlos. O foco é a entrega. Ser transparente demais pode sair caro.", 
                    {"integridade": -10, "respeito_com_chefe": 10, "respeito_com_equipe": 10})
            ])
            hide(thiago)

        def capitulo_6():
            scene(bg_meeting_room)
            dialog("Dias depois, durante a apresentação oficial do projeto para os diretores da MicroHard, Carlos conduz a reunião com entusiasmo, destacando os pontos fortes da entrega e agradecendo nominalmente a alguns membros da equipe.")

            show(carlos, Pos.CENTER)
            dialog("...E o sistema de recomendação de fontes, integrado à API de parceiros, foi brilhantemente construído. Wellington foi peça-chave nessa parte.", carlos)
            hide(carlos)

            show(alissa, Pos.RIGHT)
            dialog("Poxa…isso foi literalmente minha feature. Foi muito trabalhoso fazer essa parte e ele sabe disso.", alissa)

            show(thiago, Pos.LEFT)

            menu([  
                Option("Na hora das perguntas, destaco que você cuidou da arquitetura, Alissa. É o certo a fazer.", 
                    {"integridade": 10, "respeito_com_equipe": 10, "respeito_com_chefe": -10}),
                Option("Depois eu converso com Carlos e sugiro que ele corrija a informação no Slack.", 
                    {"integridade": 5, "respeito_com_equipe": 10}),
                Option("Vamos deixar essa passar, Alissa. Não é o melhor momento para criar desconforto com a diretoria.", 
                    {"integridade": -10, "respeito_com_equipe": -10})
            ])
        
            hide(thiago)
            hide(alissa)

        def capitulo_7():
            scene(carlos_office)
            dialog("Com o InsightPro oficialmente lançado, a equipe recebe feedbacks positivos, propostas de integração… e algumas solicitações inesperadas.")

            show(carlos,Pos.CENTER)
            dialog("Surgiram consultas externas inesperadas sobre o uso da plataforma. Algumas prefeituras estão interessadas, e também chegou um pedido informal de um partido político - querem testar o InsightPro para levantar tendências de opinião pública em campanhas eleitorais.", carlos)
            hide(carlos)

            show(maria,Pos.LEFT)
            dialog("Isso é bem diferente do que pensamos no início. Não sei se me sinto confortável com esse tipo de uso.", maria)

            show(wellington, Pos.RIGHT)
            dialog("Tecnicamente, o sistema está pronto pra qualquer domínio. Mas usar isso para fins eleitorais…não sei se esse é o mais correto a se fazer. E se ele for usado para manipulação?", wellington)
            hide(maria)
            hide(wellington)

            show(carlos,Pos.CENTER)

            dialog("Olha… não somos responsáveis pelo uso. Entregamos a ferramenta. Cabe a outras áreas decidirem.", carlos)

            menu([
                Option("Devemos estabelecer diretrizes claras de uso ético e sugerir a criação de restrições de acesso.", 
                    {"integridade": 10, "respeito_com_chefe": -5}),
                Option("Podemos liberar o uso, desde que assinem termos deixando claro que é por conta e risco deles.", 
                    {"integridade": 5, "respeito_com_chefe": 5}),
                Option("Se querem usar para fins políticos, que usem. Nosso trabalho está entregue.", 
                    {"integridade": -10, "respeito_com_chefe": 10})
            ])
            hide(carlos)
            show(thiago)
            dialog("Fim da jornada de Thiago na MicroHard. Suas escolhas moldaram não apenas sua carreira, mas também o impacto ético do projeto InsightPro.")
            hide(thiago)

        capitulo_1()
        capitulo_2()
        capitulo_3()
        capitulo_4()
        capitulo_5()
        capitulo_6()
        capitulo_7()
        # TODO: Chamar aqui mais capitulos

        game.actions.append(Action(type=ActionType.ShowStats))

    script()


def main():
    pygame.init()

    game = Game(
        screen=pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)),
        caracter_surface=Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32),
        dialog_surface=Surface((DIALOG_WIDTH, DIALOG_HEIGHT), pygame.SRCALPHA, 32),
        menu_surface=Surface((MENU_WIDTH, MENU_HEIGHT), pygame.SRCALPHA, 32),
        stats_surface=Surface((STATS_WIDTH, STATS_HEIGHT), pygame.SRCALPHA, 32),
        stats_mini_surface=Surface((MINI_STATS_WIDTH, MINI_STATS_HEIGHT), pygame.SRCALPHA, 32),
        font=Font(FONTS_FOLDER + "Oswaldt.ttf", FONT_SIZE),
        menu_font=Font(FONTS_FOLDER + "Oswaldt.ttf", FONT_SIZE),
        stats_font=Font(FONTS_FOLDER + "Oswaldt.ttf", FONT_SIZE),
        stats_mini_font=Font(FONTS_FOLDER + "Oswaldt.ttf", STATS_MINI_FONT_SIZE),
        stats_title_font=Font(FONTS_FOLDER + "Oswaldt.ttf", STATS_TITLE_FONT_SIZE),
        dialog_title_font=Font(FONTS_FOLDER + "Oswaldt.ttf", TITLE_FONT_SIZE),
        useful_keys=[K_RETURN, K_UP, K_DOWN, K_s],
        stats_colors=STATS_COLORS,
    )

    game_script(game)

    clock = pygame.time.Clock()
    pygame.mixer.init()
    pygame.mixer.music.load(MUSIC_FOLDER + "background.mp3") 
    pygame.mixer.music.play(-1,0.0)
    pygame.mixer.music.set_volume(0.1)

    se_enter_menu = pygame.mixer.Sound(MUSIC_FOLDER + "enter_menu.wav")
    se_enter = pygame.mixer.Sound(MUSIC_FOLDER + "enter.wav")
    se_move_menu = pygame.mixer.Sound(MUSIC_FOLDER + "move_menu.wav")
    se_s = pygame.mixer.Sound(MUSIC_FOLDER + "s.wav")

    se_enter_menu.set_volume(0.5)
    se_enter.set_volume(2.0)
    se_move_menu.set_volume(4.0)
    se_s.set_volume(0.5)

    while game.running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

        keys = pygame.key.get_pressed()

        update_game(game)

        def is_pressed(key: int) -> bool:
            return keys[key] and not game.last_keys[key]


        if is_pressed(K_s):
            game.show_stats = not game.show_stats
            se_s.play()

        if not game.show_stats:
            if game.menu:
                if is_pressed(K_RETURN):
                    game.action_idx += 1

                    selected_option = game.menu[game.menu_idx]
                    for k in selected_option.status:
                        game.player_status[k] += selected_option.status[k]

                    game.menu = None
                    se_enter_menu.play()

                elif is_pressed(K_UP):
                    game.menu_idx = (game.menu_idx - 1) % len(game.menu)
                    se_move_menu.play()

                elif is_pressed(K_DOWN):
                    game.menu_idx = (game.menu_idx + 1) % len(game.menu)
                    se_move_menu.play()
            else:
                if is_pressed(K_RETURN):
                    game.action_idx += 1
                    se_enter.play()

        for k in game.useful_keys:
            game.last_keys[k] = keys[k]

        game.screen.fill("white")
        game.dialog_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)
        game.caracter_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)
        game.menu_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)
        game.stats_mini_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)

        draw_background(game)
        draw_caracters(game)
        draw_dialog(game)
        draw_menu(game)
        draw_mini_status(game)
        draw_stats(game)

        if not game.show_stats:
            game.screen.blit(game.caracter_surface, (0, SCREEN_HEIGHT - CARACTER_HEIGHT))
            if game.menu:
                game.screen.blit(game.menu_surface, ((SCREEN_WIDTH - MENU_WIDTH)/2, (SCREEN_HEIGHT - MENU_HEIGHT)/2))
            else:
                game.screen.blit(game.dialog_surface, ((SCREEN_WIDTH - DIALOG_WIDTH)/2, SCREEN_HEIGHT - DIALOG_HEIGHT))
            game.screen.blit(game.stats_mini_surface, ((SCREEN_WIDTH - MINI_STATS_WIDTH - DIALOG_PADDING), DIALOG_PADDING))

        else:
            game.screen.blit(game.stats_surface, ((SCREEN_WIDTH - STATS_WIDTH)/2, (SCREEN_HEIGHT - STATS_HEIGHT)/2))

        pygame.display.flip()
        game.dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == "__main__":
    main()

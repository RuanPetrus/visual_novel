# Example file showing a circle moving on screen
import os
from copy import copy
from dataclasses import dataclass, field
from enum import Enum
import pygame
from pygame.font import Font
from pygame import Surface, Color, Rect, K_RETURN, K_UP, K_DOWN

SEP = os.path.sep
IMAGES_FOLDER = "images" +SEP
FONTS_FOLDER = "fonts" + SEP
CARACTER_FOLDER = IMAGES_FOLDER + "caracters" + SEP
BG_FOLDER = IMAGES_FOLDER + "backgrounds" + SEP
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
DIALOG_PADDING = 25
DIALOG_CORNER_RADIUS = 10
DIALOG_OPPACITY = 0.8

MENU_WIDTH = 3/4 * SCREEN_WIDTH
MENU_HEIGHT = 3/4 * SCREEN_HEIGHT

DIALOG_WIDTH = 9/10 * SCREEN_WIDTH
DIALOG_HEIGHT = 1/3 * SCREEN_HEIGHT

STATS_WIDTH = 3/4 * SCREEN_WIDTH
STATS_HEIGHT = 3/4 * SCREEN_HEIGHT

CARACTER_HEIGHT = 3/4 * SCREEN_HEIGHT

CARACTER_SEP_SIZE = 20
FONT_SIZE = 40
TITLE_FONT_SIZE = 50

WHITE = Color(255, 255, 255, 255)
BLACK = Color(0, 0, 0, 255)
BLUE = Color(0, 0, 255, 255)
GREEN = Color(0, 255, 0, 255)

MENU_FG_COLOR = Color(48, 55, 62, 255)
MENU_BG_COLOR = Color(245, 247, 250, 255)

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
    font: Font
    menu_font: Font
    dialog_title_font: Font
    stats_font: Font
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
    background = pygame.transform.scale(game.background, game.screen.get_size())
    game.screen.blit(background, (0, 0))

def draw_stats(game: Game):
    text_width = 0
    text_height = 0
    for k in game.player_status:
        width, height = game.stats_font.size(k)
        text_width = max(text_width, width)
        text_height += height

    value_width = game.stats_surface.get_width() - text_width

    text_sur = Surface((text_width, text_height), pygame.SRCALPHA, 32)
    value_sur = Surface((value_width, text_height), pygame.SRCALPHA, 32)

    vertical_offset = 0
    for k in game.player_status:
        width, height = game.stats_font.size(k)
        text_sur.blit(
            dialog_to_surface(k, text_width, game.stats_font, MENU_FG_COLOR), 
            (0, vertical_offset)
        )
        vertical_offset += height

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
                game.show_stats = True

    else:
        game.running = False

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
            "responsabilidade_social": 50,
            "integridade": 50,
            "inclusao": 50,
            "respeito_com_equipe": 5,
            "respeito_com_chefe" : 5,
            "respeito_na_empresa": 5,
        }
        game.player_status = status

        bg_office = pygame.image.load(BG_FOLDER + 'gigahard_entrance.png').convert()
        bg_reception = pygame.image.load(BG_FOLDER + 'gigahard_entrance.png').convert()
        bg_office_tour = pygame.image.load(BG_FOLDER + 'gigahard_tour.png').convert()
        bg_meeting_room = pygame.image.load(BG_FOLDER + 'gigahard_office.png').convert()

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

        def capitulo_1():
            scene(bg_office)

            # Dia 0 - Contexto
            dialog("Thiago era programador pleno numa empresa de médio porte, onde nunca se sentiu realizado profissionalmente.")
            dialog("Recentemente, ele decidiu dar um passo ousado: aceitou uma vaga júnior na GigaHard - a empresa dos seus sonhos desde a época da faculdade.")
            dialog("Apesar da queda na senioridade e na remuneração, Thiago viu na GigaHard uma oportunidade única:  sempre admirou os produtos da empresa e sabe que, além da boa  reputação, ela oferece ótimas perspectivas de crescimento e bons salários no longo prazo.")
            dialog("Com este contexto, Thiago está determinado (e um pouco pressionado) a ascender profissionalmente e conquistar seu espaço na  GigaHard. Para isso, ele planeja ser participativo e empenhado nas atividades dentro da GigaHard")

            # Dia 1
            scene(bg_reception)
            dialog("Dia 1")

            show(thiago, Pos.LEFT)
            dialog("Olá… meu nome é Thiago. Recebi um e-mail de confirmação dizendo que hoje seria meu primeiro dia de trabalho.", thiago)

            show(alissa, Pos.RIGHT)
            dialog("Oi… eu sou a Alissa. Também recebi um e-mail assim.", alissa)

            show(recepcionista, Pos.CENTER)
            dialog("Ah, claro! Vocês devem fazer parte da nova leva de contratados. Vou ligar para o andar de cima, alguém já deve vir recebê-los.", recepcionista)

            hide(recepcionista)
            show(carlos, Pos.CENTER)
            dialog("Olá! Meu nome é Carlos. Provavelmente serei o gerente de vocês. Gostariam de conhecer o prédio?", carlos)

            dialog("Sim, claro.", thiago)
            dialog("Sim!", alissa)

            hide(carlos)
            hide(thiago)
            hide(alissa)

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

            show(alissa, Pos.RIGHT)
            dialog("...", alissa)

            dialog("Bem… deixe-me apresentar os colegas de squad de vocês.", carlos)

            show(maria)
            dialog("Essa é a Maria, a funcionária mais antiga e esforçada do squad.", carlos)
            dialog("Prazer, eu sou a Maria.", maria)

            hide(maria)
            show(wellington)
            dialog("E este é o Wellington, também trabalha há uns anos na empresa.", carlos)
            dialog("Oi, eu sou o Wellington.", wellington)

            hide(wellington)
            dialog("Bem, para hoje devemos focar em buscar as nossas fontes de dados. Foquem em confiabilidade. Precisamos de dados robustos e de boa qualidade.", carlos)
            dialog("Amanhã, nesta mesma sala, às 16h teremos nossa primeira reunião.", carlos)

            dialog("Todos: Ok")
            hide(alissa)
            hide(thiago)
            hide(carlos)

            # Dia 2
            scene(bg_meeting_room)
            dialog("Dia 2")

            show(carlos, Pos.CENTER)
            dialog("Então… todos trouxeram as fontes de dados que se comprometeram a trazer?", carlos)

            show(thiago, Pos.LEFT)
            dialog("Encontrei uma fonte de dados financeiros mantida por uma empresa privada. O acesso é pago, mas parece bastante promissora.", thiago)

            show(alissa, Pos.RIGHT)
            dialog("Eu achei duas fontes… não são muito abrangentes, mas eu achei os dados bem estruturados e robustos.", alissa)

            show(wellington)
            dialog("Consegui encontrar uma API feita por uma associação de produtores rurais. Esses dados são ótimos, oferecem informações únicas sobre um nicho que é muito importante para nós.", wellington )
            dialog("Estarmos de posse desses dados nos colocaria em uma posição muito privilegiada, mas o problema é que não encontrei a licença atrelada ao serviço.", wellington )
            dialog("Temo que, se entrarmos em contato diretamente, por se tratar de um produto com fins lucrativos, eles possam negar o acesso.", wellington )

            dialog("E o que vocês acham que devemos fazer com essa API? Lembrem-se: se não tivermos acesso a esses dados, e a Gluglu conseguir, ficaremos em desvantagem.", carlos)

            menu([
                Option("Mesmo sem encontrar uma licença explícita, a organização pode ter diretrizes internas sobre o uso da API. O correto é entrar em contato antes de utilizar qualquer dado. Enquanto não houver autorização formal, não devemos acessar nem armazenar essas informações", 
                       {"integridade": 10, "respeito_com_equipe": -10}),
                Option("A API está aberta, e conseguimos baixar os dados sem obstáculos. Podemos coletar tudo agora e só depois perguntar sobre a licença. Se houver uma negativa futura, ao menos já teremos uma base histórica valiosa salva para trabalhar.a", 
                       {"integridade": -5, "respeito_com_equipe": 5}),
                Option("Enquanto não houver uma restrição clara, devemos aproveitar. Se deixarmos passar, a Gluglu pode sair na frente. Vamos extrair o máximo possível agora - depois vemos como lidar com a parte legal.", 
                       {"integridade": -10, "respeito_com_equipe": 5}),
            ])

        def capitulo_2():
            """TODO: Colocar aqui o capitulo 2 seguindo o exemplo do capitulo 1"""

        capitulo_1()
        capitulo_2()
        # TODO: Chamar aqui mais capitulos

    script()


def main():
    pygame.init()

    game = Game(
        screen=pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)),
        caracter_surface=Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA, 32),
        dialog_surface=Surface((DIALOG_WIDTH, DIALOG_HEIGHT), pygame.SRCALPHA, 32),
        menu_surface=Surface((MENU_WIDTH, MENU_HEIGHT), pygame.SRCALPHA, 32),
        stats_surface=Surface((STATS_WIDTH, STATS_HEIGHT), pygame.SRCALPHA, 32),
        font=Font(FONTS_FOLDER + "Oswaldt.ttf", FONT_SIZE),
        menu_font=Font(FONTS_FOLDER + "Oswaldt.ttf", FONT_SIZE),
        stats_font=Font(FONTS_FOLDER + "Oswaldt.ttf", FONT_SIZE),
        dialog_title_font=Font(FONTS_FOLDER + "Oswaldt.ttf", TITLE_FONT_SIZE),
        useful_keys=[K_RETURN, K_UP, K_DOWN]
    )

    game_script(game)

    clock = pygame.time.Clock()

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

        if game.menu is None:
            if is_pressed(K_RETURN):
                game.action_idx += 1
        else:
            if is_pressed(K_RETURN):
                game.action_idx += 1

                selected_option = game.menu[game.menu_idx]
                for k in selected_option.status:
                    game.player_status[k] += selected_option.status[k]

                game.menu = None

            elif is_pressed(K_UP):
                game.menu_idx = (game.menu_idx - 1) % len(game.menu)

            elif is_pressed(K_DOWN):
                game.menu_idx = (game.menu_idx + 1) % len(game.menu)

        for k in game.useful_keys:
            game.last_keys[k] = keys[k]

        game.screen.fill("white")
        game.dialog_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)
        game.caracter_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)
        game.menu_surface.fill(Color(0, 0, 0, 0))  # Optional: set overall transparency (0-255)

        draw_background(game)
        draw_caracters(game)
        draw_dialog(game)
        draw_menu(game)
        draw_stats(game)

        if not game.show_stats:
            game.screen.blit(game.caracter_surface, (0, SCREEN_HEIGHT - CARACTER_HEIGHT))
            if game.menu:
                game.screen.blit(game.menu_surface, ((SCREEN_WIDTH - MENU_WIDTH)/2, (SCREEN_HEIGHT - MENU_HEIGHT)/2))
            else:
                game.screen.blit(game.dialog_surface, ((SCREEN_WIDTH - DIALOG_WIDTH)/2, SCREEN_HEIGHT - DIALOG_HEIGHT))
        else:
            pass

        pygame.display.flip()
        game.dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == "__main__":
    main()

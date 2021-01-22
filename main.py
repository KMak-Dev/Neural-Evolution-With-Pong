import pygame
import time
import random
import neat
import pickle
import os
pygame.init()
# Textures, colors, fonts
background = pygame.image.load('Background.png')
icon = pygame.image.load('Icon.png')
white = (255, 255, 255)
blue = (174, 214, 241)
cyan = (115, 198, 182)
colors = [cyan]
# I like cyan

# Screen settings
HEIGHT = 600
WIDTH = 1200
running = True
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(" Pong - With AI !")
pygame.display.set_icon(icon)

# pong settings
num_player = 30
bounce = [0, 1, 2, 3, 4]
training_mode = False
# set to true for training


# Classes
class Paddle:
    def __init__(self, x, y):
        self.length = 150
        self.width = 20
        self.x = x
        self.y = y
        self.direction = 2
        self.velocity = 25
        # the y positions of pads in the previous frame
        self.prevL = 0
        self.prevR = 0


class Pong:
    def __init__(self):
        self.length = 20
        self.width = 20
        self.x = WIDTH/2
        self.y = HEIGHT/2
        self.velocityX = 5
        self.velocityY = 7
        self.hit = False
        self.hit_count = 0
        self.ball_starting_velocity_x = 5
        self.ball_starting_velocity_y = 5


class Player:
    def __init__(self):
        self.padL = Paddle(0, HEIGHT / 2)
        self.padR = Paddle(WIDTH - 20, HEIGHT / 2)
        self.ball = Pong()
        self.alive = True
        self.scoreL = 0
        self.scoreR = 0
        self.started = False
        self.color = random.choice(colors)


# Functions
def draw(players):
    time.sleep(0.0167)
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    i = 0
    while i < len(players):
        if players[i].alive:
            # displays score only if not in training mode
            if not training_mode:
                font = pygame.font.Font('freesansbold.ttf', 20)
                score_display = font.render("Score: " + str(players[i].scoreL), True, players[i].color)
                score_display1 = font.render("Score: " + str(players[i].scoreR), True, players[i].color)
                screen.blit(score_display, (200, 10))
                screen.blit(score_display1, (WIDTH - 300, 10))
            pygame.draw.rect(screen, players[i].color, [players[i].padL.x, players[i].padL.y, players[i].padL.width,
                                                        players[i].padL.length])
            pygame.draw.rect(screen, players[i].color, [players[i].padR.x, players[i].padR.y, players[i].padR.width,
                                                        players[i].padR.length])
            pygame.draw.rect(screen, players[i].color, [players[i].ball.x, players[i].ball.y, players[i].ball.width,
                                                        players[i].ball.length])
        i += 1


def move_players(players, networks, genomes):
    i = 0
    while i < len(players):
        if players[i].alive:
            # Every frame that players are alive, reward them by increasing fitness
            genomes[i][1].fitness += 0.01
            # if direction is positive, it is set to 1
            direction = 1
            if players[i].ball.velocityX < 0:
                direction = -1
            # make decision of upward vs. downward based on the following inputs
            output = networks[i].activate((players[i].padL.y, players[i].padR.y,
                                           players[i].ball.velocityY,
                                           players[i].ball.y, direction
                                           ))
            if output[0] > 0 > players[i].ball.velocityX:
                if players[i].padL.y > 0:
                    players[i].padL.y -= players[i].padL.velocity
            elif output[0] < 0 and players[i].ball.velocityX < 0:
                if players[i].padL.y < HEIGHT - players[i].padL.length:
                    players[i].padL.y += players[i].padL.velocity
            elif output[1] > 0 and players[i].ball.velocityX > 0:
                if players[i].padR.y > 0:
                    players[i].padR.y -= players[i].padR.velocity
            elif output[1] < 0 < players[i].ball.velocityX:
                if players[i].padR.y < HEIGHT - players[i].padR.length:
                    players[i].padR.y += players[i].padR.velocity
            # punish idle players by decreasing fitness
            y = players[i].padL.y
            y1 = players[i].padR.y
            if y == players[i].padL.prevL:
                genomes[i][1].fitness -= 0.01
            if y1 == players[i].padR.prevL:
                genomes[i][1].fitness -= 0.01
            players[i].padL.prevL = y
            players[i].padR.prevL = y1
        i += 1


def move_pongs(players, genomes):
    i = 0
    while i < len(players):
        if players[i].alive:
            # pong starts at random direction
            if not players[i].started:
                ran = random.choice(bounce)
                if ran == 1 or ran == 2:
                    players[i].ball.velocityX = -players[i].ball.velocityX
                ran = random.choice(bounce)
                if ran == 1 or ran == 2:
                    players[i].ball.velocityY = -players[i].ball.velocityY
                players[i].started = True
            # pong accelerates on first hit
            if players[i].ball.hit and players[i].ball.hit_count < 1:
                players[i].ball.velocityX = players[i].ball.velocityX * 4
                players[i].ball.hit_count += 1
            # pong bounces if it hits floor or ceiling
            if players[i].ball.y <= 0 + players[i].ball.length/2 or \
                    players[i].ball.y >= HEIGHT - players[i].ball.length/2:
                players[i].ball.velocityY = -players[i].ball.velocityY
            # pong upon hitting the pads
            elif (players[i].ball.x <= players[i].padL.x + players[i].padL.width + players[i].ball.width/2 and (
                    players[i].padL.y - players[i].ball.length <= players[i].ball.y
                    <= players[i].padL.y + players[i].ball.length + players[i].padL.length)) or players[i].ball.x >= \
                    players[i].padR.x - players[i].padR.width - players[i].ball.width/2 and (
                    players[i].padR.y - players[i].ball.length <= players[i].ball.y
                    <= players[i].padR.y + players[i].ball.length + players[i].padR.length):
                # reward the player for scoring by increasing its fitness
                genomes[i][1].fitness += 10
                if players[i].ball.velocityX < 0:
                    players[i].scoreL += 1
                else:
                    players[i].scoreR += 1
                players[i].ball.hit = True
                # pong bounces at random angle
                ran = random.choice(bounce)
                if ran == 0 and not training_mode:
                    if players[i].ball.velocityY > 0:
                        players[i].ball.velocityY = 2
                    else:
                        players[i].ball.velocityY = -2
                elif ran == 1 and not training_mode:
                    if players[i].ball.velocityY > 0:
                        players[i].ball.velocityY = 9
                    else:
                        players[i].ball.velocityY = -9
                elif ran == 2 and not training_mode:
                    if players[i].ball.velocityY > 0:
                        players[i].ball.velocityY = 9
                    else:
                        players[i].ball.velocityY = -9
                elif ran == 3 and not training_mode:
                    if players[i].ball.velocityY > 0:
                        players[i].ball.velocityY = 11
                    else:
                        players[i].ball.velocityY = -11
                elif ran == 4 and not training_mode:
                    if players[i].ball.velocityY > 0:
                        players[i].ball.velocityY = 17
                    else:
                        players[i].ball.velocityY = -17
                players[i].ball.velocityX = -players[i].ball.velocityX
            # if pong is out of bound
            if players[i].ball.x > WIDTH + players[i].ball.width or players[i].ball.x < 0 - players[i].ball.width:
                # punish the player for missing the pong, remove from screen
                genomes[i][1].fitness -= 20
                players[i].alive = False
                # randomize direction of pong
                ran = random.choice(bounce)
                if ran == 0 or ran == 1:
                    players[i].ball.velocityX = -players[i].ball.velocityY
                ran = random.choice(bounce)
                if ran == 0 or ran == 1:
                    players[i].ball.velocityY = -players[i].ball.velocityY
            # move the pong
            players[i].ball.x += players[i].ball.velocityX
            players[i].ball.y += players[i].ball.velocityY
        i += 1


def game(genomes, config):
    # generate neural networks, genomes, players
    networks = []
    genome = []
    Players = []
    for x, gene in genomes:
        net = neat.nn.FeedForwardNetwork.create(gene, config)
        networks.append(net)
        gene.fitness = 0
        genome.append(gene)
        Players.append(Player())
    for player in Players:
        player.color = random.choice(colors)
    # main loop
    while True:
        j = 0
        for player in Players:
            if player.alive:
                j += 1
        if j < 1:
            return
        draw(Players)
        move_players(Players, networks, genomes)
        move_pongs(Players, genomes)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        pygame.display.update()


# function used for acquiring desired genome, saving it to empty file
def train_genome(config_file):
    # essential setups for NEAT
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # run game and pickle the best genome
    winner = p.run(game, 100)
    file = open("empty_genome.pkl", 'wb')
    pickle.dump(winner, file)
    file.close()


# function for loading acquired genome
def load_saved_genome(configuration_path, genome_path="saved_genome.pkl"):
    # essential setups for NEAT and load best genome
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, configuration_path)
    with open(genome_path, "rb") as file:
        saved_genome = pickle.load(file)
    loaded_genome = [(1, saved_genome)]
    # run the game with the best genome
    game(loaded_genome, config)
    pygame.quit()


# run the program and load the saved genome
if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    if not training_mode:
        load_saved_genome(config_path)
    else:
        train_genome(config_path)